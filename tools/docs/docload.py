#!/usr/bin/env python

# Script to load documentation from tarballs

import sys
import os
import tarfile
import re
import tidy
from optparse import OptionParser
from ConfigParser import ConfigParser

import psycopg2

pagecount = 0
quiet = False

re_titlematch = re.compile('<title\s*>([^<]+)</title\s*>', re.IGNORECASE)


# Load a single page
def load_doc_file(filename, f):
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
    if rawcontents.startswith('<?xml version="1.0" encoding="UTF-8"'):
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

    contents = unicode(rawcontents, encoding)

    tm = re_titlematch.search(contents)
    if tm:
        title = tm.group(1)
    else:
        title = ""
    if not quiet: print "--- file: %s (%s) ---" % (filename, title)

    s = tidy.parseString(contents.encode('utf-8'), **tidyopts)
    curs.execute("INSERT INTO docs (file, version, title, content) VALUES (%(f)s, %(v)s, %(t)s, %(c)s)", {
        'f': filename,
        'v': ver,
        't': title,
        'c': str(s),
    })
    global pagecount
    pagecount += 1


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

config = ConfigParser()
config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'docload.ini'))

if not os.path.isfile(tarfilename):
    print "File %s not found" % tarfilename
    sys.exit(1)

tf = tarfile.open(tarfilename)

connection = psycopg2.connect(config.get('db', 'dsn'))

curs = connection.cursor()
# Verify that the version exists, and what we're loading
curs.execute("SELECT current FROM core_version WHERE tree=%(v)s", {'v': ver})
r = curs.fetchall()
if len(r) != 1:
    print "Version %s not found in the system, cannot load!" % ver
    sys.exit(1)

iscurrent = r[0][0]

# Remove any old docs for this version (still protected by a transaction while
# we perform the load)
curs.execute("DELETE FROM docs WHERE version=%(v)s", {'v': ver})


re_htmlfile = re.compile('[^/]*/doc/src/sgml/html/.*')
re_tarfile = re.compile('[^/]*/doc/postgres.tar.gz$')
for member in tf:
    if re_htmlfile.match(member.name):
        load_doc_file(os.path.basename(member.name), tf.extractfile(member))
    if re_tarfile.match(member.name):
        f = tf.extractfile(member)
        inner_tar = tarfile.open(fileobj=f)
        for inner_member in inner_tar:
            # Some old versions have index.html as a symlink - so let's
            # just ignore all symlinks to be on the safe side.
            if inner_member.issym(): continue

            if inner_member.name.endswith('.html') or inner_member.name.endswith('.htm'):
                load_doc_file(inner_member.name, inner_tar.extractfile(inner_member))
tf.close()

# Update the docs loaded timestamp
curs.execute("UPDATE core_version SET docsloaded=CURRENT_TIMESTAMP WHERE tree=%(v)s", {'v': ver})

# Issue varnish purge for all docs of this version
if ver == "0":
    # Special handling of developer docs...
    ver = "devel"

curs.execute("SELECT varnish_purge('^/docs/' || %(v)s || '/')", {'v': ver})
if iscurrent:
    curs.execute("SELECT varnish_purge('^/docs/current/')")

connection.commit()
connection.close()

if not quiet: print "Done (%i pages)." % pagecount
