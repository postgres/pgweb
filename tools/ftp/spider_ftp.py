#!/usr/bin/python

#
# spider_ftp.py - spider the ftp site and generate an output file with all
#                 the metadata we require, that can be transferred over to
#                 the master web server.
#

import sys
import os
from datetime import datetime
import cPickle as pickle
#from pprint import pprint

allnodes = {}

def read_file(fn):
	f = open(fn, "r")
	t = f.read()
	f.close()
	return t

def parse_directory(dirname, rootlen):
	mynode = {}
	for f in os.listdir(dirname):
		if f.startswith(".") and not f == ".message": continue
		if f == "sync_timestamp": continue

		fn = os.path.join(dirname, f)
		if os.path.isdir(fn):
			# Can be a directory itself, or a symbolic link to a directory
			if os.path.islink(fn):
				# This is a symbolic link
				mynode[f] = {
					't': 'l',
					'd': os.readlink(fn),
					}
			else:
				# This is a subdirectory, recurse into it
				parse_directory(fn, rootlen)
				mynode[f] = {
					't': 'd',
				}
		else:
			# This a file
			stat = os.stat(fn)
			mynode[f] = {
				't': 'f',
				's': stat.st_size,
				'd': datetime.fromtimestamp(stat.st_mtime),
			}
			if f == "README" or f == "CURRENT_MAINTAINER" or f == ".message":
				mynode[f]['c'] = read_file(fn)

	allnodes[dirname[rootlen:].strip("/")] = mynode

def Usage():
	print "Usage: spider_ftp.py <ftp_root> <pickle_file>"
	sys.exit(1)

if len(sys.argv) != 3: Usage()

parse_directory(sys.argv[1], len(sys.argv[1]))

f = open(sys.argv[2] + ".tmp", "wb")
pickle.dump(allnodes, f)
f.close()
os.rename(sys.argv[2] + ".tmp", sys.argv[2])

#pprint(allnodes)
