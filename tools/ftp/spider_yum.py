#!/usr/bin/env python3
import argparse
import sys
import os
import re
import json
import requests
from decimal import Decimal
from tempfile import NamedTemporaryFile

platform_names = {
    'redhat': 'Red Hat Enterprise Linux {0}',
    'centos': 'CentOS {0}',
    'sl': 'Scientific Linux {0}',
    'fedora': 'Fedora {0}',
    'oraclelinux': 'Oracle Enterprise Linux {0}',
    'ami201503-': 'Amazon Linux AMI201503 {0}',
}
platform_sort = {
    'redhat': 1,
    'centos': 2,
    'sl': 3,
    'fedora': 4,
    'oraclelinux': 5,
    'ami201503-': 6,
}
archs = ['x86_64', 'i386', 'i686', 'ppc64le']


def generate_platform(dirname, familyprefix, ver, installer, systemd):
    for f in list(platform_names.keys()):
        yield ('%s-%s' % (f, ver), {
            't': platform_names[f].format(ver),
            'p': os.path.join(dirname, '{0}-{1}'.format(familyprefix, ver)),
            'f': f,
            'i': installer,
            'd': systemd,
            's': platform_sort[f] * 1000 - ver,
            'found': False,
        })


def get_redhat_systemd(ver):
    return (ver >= 7)


platforms = {}
for v in range(5, 7 + 1):
    platforms.update(dict(generate_platform('redhat', 'rhel', v, 'yum', get_redhat_systemd(v))))
for v in range(24, 30 + 1):
    platforms.update(dict(generate_platform('fedora', 'fedora', v, 'dnf', True)))

re_reporpm = re.compile('^pgdg-([a-z0-9-]+)([0-9]{2})-[^-]+-(\d+)\.noarch\.rpm$')
re_versiondirs = re.compile(r'^\d+(\.\d+)?$')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spider repo RPMs")
    parser.add_argument('yumroot', type=str, help='YUM root path')
    parser.add_argument('target', type=str, help='Target URL or filename')

    args = parser.parse_args()

    versions = sorted([v for v in os.listdir(args.yumroot) if re_versiondirs.match(v)], key=Decimal, reverse=True)
    reporpms = {}
    for v in versions:
        reporpms[v] = {}
        vroot = os.path.join(args.yumroot, v)
        for dirpath, dirnames, filenames in os.walk(vroot):
            rmatches = [_f for _f in (re_reporpm.match(f) for f in sorted(filenames, reverse=True)) if _f]

            if rmatches:
                familypath = os.path.join(*dirpath.split('/')[-2:])
                (familypath, arch) = familypath.rsplit('-', 1)

                for r in rmatches:
                    shortdist, shortver, ver = r.groups(1)

                    found = False
                    for p, pinfo in list(platforms.items()):
                        if pinfo['p'] == familypath and pinfo['f'] == shortdist:
                            if p not in reporpms[v]:
                                reporpms[v][p] = {}
                            reporpms[v][p][arch] = max(int(ver), int(reporpms[v][p].get(arch, 0)))
                            platforms[p]['found'] = True
                            break
                    else:
                        # DEBUG
                        # print "%s (%s) not found in platform list" % (familypath, shortdist)
                        pass

    # Filter all platforms that are not used
    platforms = {k: v for k, v in platforms.items() if v['found']}
    for k, v in platforms.items():
        del v['found']

    j = json.dumps({'platforms': platforms, 'reporpms': reporpms})

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
        with NamedTemporaryFile(dir=os.path.dirname(os.path.abspath(args.target))) as f:
            f.write(j)
            f.flush()
            if os.path.isfile(args.target):
                os.unlink(args.target)
            os.link(f.name, args.target)
