#!/usr/bin/env python3

#
# spider_ftp.py - spider the ftp site and generate an output file with all
#                 the metadata we require, that can be transferred over to
#                 the master web server.
#

import sys
import os
from datetime import datetime
import pickle as pickle
import codecs
import requests

# Directories, specified from the root of the ftp tree and down, that
# will be recursively excluded from the pickle.
exclude_roots = ['/repos', ]

allnodes = {}


def read_file(fn):
    f = codecs.open(fn, 'r', encoding='utf-8', errors='replace')
    t = f.read()
    f.close()
    return t


def parse_directory(dirname, rootlen):
    mynode = {}
    for f in os.listdir(dirname):
        if f.startswith(".") and not f == ".message":
            continue
        if f == "sync_timestamp":
            continue

        fn = os.path.join(dirname, f)
        if os.path.isdir(fn):
            # Can be a directory itself, or a symbolic link to a directory
            if os.path.islink(fn):
                # This is a symbolic link
                mynode[f] = {
                    't': 'l',
                    'd': os.readlink(fn).strip("/"),
                }
            else:
                # This is a subdirectory, recurse into it, unless it happens
                # to be on our exclude list.
                if not fn[rootlen:] in exclude_roots:
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
    print("Usage: spider_ftp.py <ftp_root> <pickle_file>")
    print("")
    print("If <pickle_file> starts with http[s]://, the file will be uploaded")
    print("to that URL instead of written to the filesystem.")
    sys.exit(1)


if len(sys.argv) != 3:
    Usage()

parse_directory(sys.argv[1], len(sys.argv[1]))

if sys.argv[2].startswith("http://") or sys.argv[2].startswith("https://"):
    r = requests.put(
        sys.argv[2],
        data=pickle.dumps(allnodes),
        headers={
            'Content-type': 'application/octet-stream',
            'Host': 'www.postgresql.org',
        },
    )
    if r.status_code != 200:
        print("Failed to upload, code: %s" % r.status_code)
        sys.exit(1)
    elif r.text != "NOT CHANGED" and r.text != "OK":
        print("Failed to upload: %s" % x)
        sys.exit(1)
else:
    f = open(sys.argv[2] + ".tmp", "wb")
    pickle.dump(allnodes, f)
    f.close()
    os.rename(sys.argv[2] + ".tmp", sys.argv[2])
