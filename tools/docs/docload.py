#!/usr/bin/env python3

# Script to load documentation from tarballs

import sys
import os
import tarfile
import csv
import io
import re
import tidylib
from optparse import OptionParser
from configparser import ConfigParser

import psycopg2

# a counter that keeps track of the total number of pages (HTML, SVG) that are loaded
# into the database
pagecount = 0
# if set to "True" -- mutes any output from the script. Controlled by an option
quiet = False
# regular expression used to search and extract the title on a given piece of
# documentation, for further use in the application
re_titlematch = re.compile('<title\s*>([^<]+)</title\s*>', re.IGNORECASE)


# Load a single page
def load_doc_file(filename, f, c):
    """Prepares and loads a HTML file for import into the documentation database"""
    tidyopts = dict(
        drop_proprietary_attributes=1,
        alt_text='',
        hide_comments=1,
        output_xhtml=1,
        show_body_only=1,
        clean=1,
        char_encoding='utf8',
        indent='auto',
    )

    # Postgres 10 started using xml toolchain and now produces docmentation in utf8. So we need
    # to figure out which version it is.
    rawcontents = f.read()
    rawfirst = rawcontents[:50].decode('utf8', errors='ignore')
    if rawfirst.startswith('<?xml version="1.0" encoding="UTF-8"'):
        # Version 10, use utf8
        encoding = 'utf-8'
        # XML builds also don't need clean=1, and that one adds some interesting CSS properties
        del tidyopts['clean']
    else:
        encoding = 'latin1'

    # PostgreSQL prior to 11 used an older toolchain to build the docs, which does not support
    # indented HTML. So turn it off on those, but keep it on the newer versions where it works,
    # because it makes things a lot easier to debug.
    if float(ver) < 11 and float(ver) > 0:
        tidyopts['indent'] = 'no'

    # convert the raw contents to the appropriate encoding for the content that will
    # be stored in the database
    contents = str(rawcontents, encoding)

    # extract the title of the page, which is rendered in a few places in the documentation
    tm = re_titlematch.search(contents)
    if tm:
        title = tm.group(1)
    else:
        title = ""

    # if not in quiet mode, output the (filename, title) pair of the docpage that is being processed
    if not quiet:
        print("--- file: %s (%s) ---" % (filename, title))

    # run libtidy on the content
    (html, errors) = tidylib.tidy_document(contents, options=tidyopts)

    # add all of the information to the CSV that will be used to load the updated
    # documentation pages into the database
    c.writerow([filename, ver, title, html])


def load_svg_file(filename, f, c):
    """Prepares and loads a SVG file for import into the documentation database"""
    # this is fairly straightforward: we just need to load the contents, and
    # set the "title" as NULL as there is no title tag
    svg = f.read()
    c.writerow([filename, ver, None, svg.decode('utf-8')])


# Main execution
parser = OptionParser(usage="usage: %prog [options] <version> <tarfile>")
parser.add_option("-q", "--quiet", action="store_true", dest="quiet",
                  help="Run quietly")
(options, args) = parser.parse_args()

if len(args) != 2:
    parser.print_usage()
    sys.exit(1)

quiet = options.quiet
ver = sys.argv[1]
tarfilename = sys.argv[2]

# load the configuration that is used to connect to the database
config = ConfigParser()
config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'docload.ini'))

# determine if the referenced tarball exists; if not, exit
if not os.path.isfile(tarfilename):
    print("File %s not found" % tarfilename)
    sys.exit(1)

# open up the tarball as well as a connection to the database
tf = tarfile.open(tarfilename)

connection = psycopg2.connect(config.get('db', 'dsn'))

curs = connection.cursor()
# Verify that the version exists, and what we're loading
curs.execute("SELECT current FROM core_version WHERE tree=%(v)s", {'v': ver})
r = curs.fetchall()
if len(r) != 1:
    print("Version %s not found in the system, cannot load!" % ver)
    sys.exit(1)

iscurrent = r[0][0]

# begin creating a CSV that will be used to import the documentation into the database
s = io.StringIO()
c = csv.writer(s, delimiter=';', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)

# this regular expression is for "newer" versions of PostgreSQL that keep all of
# the HTML documentation built out
re_htmlfile = re.compile('[^/]*/doc/src/sgml/html/.*')
# this regular expression is for "older" versions of PostgreSQL that keep the
# HTML documentation in a tarball within the tarball
re_tarfile = re.compile('[^/]*/doc/postgres.tar.gz$')
# go through each file of the tarball to determine if the file is documentation
# that should be imported
for member in tf:
    # newer versions of PostgreSQL will go down this path to find docfiles
    if re_htmlfile.match(member.name):
        # get the filename and a reference to the contents of the file
        filename = os.path.basename(member.name)
        f = tf.extractfile(member)
        # determine if the file being loaded is an SVG or a regular doc file
        if filename.endswith('.svg'):
            load_svg_file(filename, f, c)
        else:
            load_doc_file(filename, f, c)
        # after successfully preparing the file for load, increase the page count
        pagecount += 1
    # older versions of PostgreSQL kept a tarball of the documentation within the source
    # tarball, and as such will go down this path
    # SVG support was added for PostgreSQL 12, so the explicitly SVG check is not
    # present in this path
    if re_tarfile.match(member.name):
        f = tf.extractfile(member)
        inner_tar = tarfile.open(fileobj=f)
        for inner_member in inner_tar:
            # Some old versions have index.html as a symlink - so let's
            # just ignore all symlinks to be on the safe side.
            if inner_member.issym():
                continue

            if inner_member.name.endswith('.html') or inner_member.name.endswith('.htm'):
                load_doc_file(inner_member.name, inner_tar.extractfile(inner_member), c)
                # after successfully preparing the file for load, increase the page count
                pagecount += 1
tf.close()

if not quiet:
    print("Total parsed doc size: {:.1f} MB".format(s.tell() / (1024 * 1024)))

s.seek(0)

# Start loading the documentation into the database
# First, load the newly discovered documentation into a temporary table, where we
# can validate that we loaded exactly the number of docs that we thought we would,
# based on the page counter
curs.execute("CREATE TEMP TABLE docsload (file varchar(64) NOT NULL, version numeric(3,1) NOT NULL, title varchar(256) NOT NULL, content text)")
curs.copy_expert("COPY docsload FROM STDIN WITH CSV DELIMITER AS ';'", s)
if curs.rowcount != pagecount:
    print("Loaded invalid number of rows! {} rows for {} pages!".format(curs.rowcount, pagecount))
    sys.exit(1)

# If the previous step succeeded, delete all the documentation for the specified version
# and insert into / updatethe doc table the content that was loaded into the temporary table
curs.execute("DELETE FROM docs WHERE version=%(version)s AND NOT EXISTS (SELECT 1 FROM docsload WHERE docsload.file=docs.file)", {
    'version': ver,
})
if not quiet:
    print("Deleted {} orphaned doc pages".format(curs.rowcount))

curs.execute("INSERT INTO docs (file, version, title, content) SELECT file, version, title, content FROM docsload WHERE NOT EXISTS (SELECT 1 FROM docs WHERE docs.file=docsload.file AND docs.version=%(version)s)", {
    'version': ver,
})
if not quiet:
    print("Inserted {} new doc pages.".format(curs.rowcount))

curs.execute("UPDATE docs SET title=l.title, content=l.content FROM docsload l WHERE docs.version=%(version)s AND docs.file=l.file AND (docs.title != l.title OR docs.content != l.content)", {
    'version': ver,
})
if not quiet:
    print("Updated {} changed doc pages.".format(curs.rowcount))

# Update the docs loaded timestamp
curs.execute("UPDATE core_version SET docsloaded=CURRENT_TIMESTAMP WHERE tree=%(v)s", {'v': ver})

# Issue varnish purge for all docs of this version
if ver == "0":
    # Special handling of developer docs...
    ver = "devel"

curs.execute("SELECT varnish_purge('^/docs/' || %(v)s || '/')", {'v': ver})
if iscurrent:
    curs.execute("SELECT varnish_purge('^/docs/current/')")

# ensure the changes are committed, and close the connection
connection.commit()
connection.close()

if not quiet:
    print("Done (%i pages)." % pagecount)
