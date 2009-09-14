#!/usr/bin/env python

# Script to load documentation from tarballs

import sys
import os
import tarfile
import re
import tidy
import psycopg2

pagecount = 0

re_titlematch = re.compile('<title\s*>([^<]+)</title\s*>', re.IGNORECASE)

## Load a single page
def load_doc_file(filename, f):
	tidyopts = dict(drop_proprietary_attributes=1,
				alt_text='',
				hide_comments=1,
				output_xhtml=1,
				show_body_only=1,
				clean=1,
				char_encoding='utf8',
				indent='auto',
			)

	contents = unicode(f.read(),'latin1')
	tm = re_titlematch.search(contents)
	if tm:
		title = tm.group(1)
	else:
		title = ""
	print "--- file: %s (%s) ---" % (filename, title)

	s = tidy.parseString(contents.encode('utf-8'), **tidyopts)
	curs.execute("INSERT INTO docs (file, version, title, content) VALUES (%(f)s, %(v)s, %(t)s, %(c)s)",{
		'f': filename,
		'v': ver,
		't': title,
		'c': str(s),
	})
	global pagecount
	pagecount += 1

## Your typical usage message
def Usage():
	print "Usage: docload.py <version> <tarfile>"
	sys.exit(1)

## Main execution

if len(sys.argv) != 3:
	Usage()

ver = sys.argv[1]
tarfilename = sys.argv[2]

if not os.path.isfile(tarfilename):
	print "File %s not found" % tarfilename
	sys.exit(1)

tf = tarfile.open(tarfilename)

db = psycopg2.connect('host=/tmp dbname=pgweb')
curs = db.cursor()
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
			if inner_member.name.endswith('.html') or inner_member.name.endswith('.htm'):
				load_doc_file(inner_member.name, inner_tar.extractfile(inner_member))
tf.close()

db.commit()
print "Done (%i pages)." % pagecount

