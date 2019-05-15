#!/usr/bin/env python3
import argparse
import sys
import os
import re
import json
import requests
from collections import defaultdict
from tempfile import NamedTemporaryFile

re_platformdir = re.compile('^(\w+)-(\d+)-([^-]+)$')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spider repo RPMs")
    parser.add_argument('yumroot', type=str, help='YUM root path')
    parser.add_argument('target', type=str, help='Target URL or filename')

    args = parser.parse_args()

    platforms = defaultdict(list)
    for repodir in os.listdir('{0}/reporpms'.format(args.yumroot)):
        m = re_platformdir.match(repodir)
        if m:
            platname = m.group(1)
            platver = m.group(2)
            arch = m.group(3)
            platforms['{0}-{1}'.format(platname, platver)].append(arch)

    j = json.dumps({'platforms': platforms})

    if args.target.startswith('http://') or args.target.startswith('https://'):
        r = requests.put(
            args.target,
            data=j,
            headers={
                'Content-type': 'application/json',
                'Host': 'www.postgresql.org',
            },
        )
        if r.status_code != 200:
            print("Failed to upload, code: %s" % r.status_code)
            sys.exit(1)

        if r.text != "NOT CHANGED" and r.text != "OK":
            print("Failed to upload: %s" % x)
            sys.exit(1)
    else:
        with NamedTemporaryFile(mode='w', dir=os.path.dirname(os.path.abspath(args.target))) as f:
            f.write(j)
            f.flush()
            if os.path.isfile(args.target):
                os.unlink(args.target)
            os.link(f.name, args.target)
