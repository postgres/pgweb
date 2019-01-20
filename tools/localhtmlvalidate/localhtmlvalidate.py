#!/usr/bin/env python3
#
# localhtmlvalidate.py - validate local HTML for pgweb
#
# This is a small tool that you run to validate the HTML output of your
# localhost pgweb installation against the W3C validator. Give it the
# localhost:8000 URL (or other, depending on what port you're running the
# local server on), and it will give you a list of possible issues with
# the page.
#
# In theory it can be used just fine for non-pgweb pages as well, but
# for obvious reasons the functionality to show the source line number
# based on the pgweb templates won't work.
#

import sys
import requests
import re
import html.parser


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: localhtmlvalidate.py <local url>")
        sys.exit(1)

    r = requests.get(sys.argv[1])
    contents = r.text

    # Try to figure out where the actual contents start :)
    try:
        firstline = contents.splitlines().index('<div id="pgContentWrap">')
    except ValueError:
        firstline = 0

    # Generate a form body
    data = {
        'doctype': 'Inline',
        'group': '0',
        'verbose': '1',
        'prefill': '1',
        'prefill_doctype': 'html401',
        'fragment': contents,
    }

    # Now submit it to the w3c validator
    resp = requests.post(
        'https://validator.w3.org/check',
        data=data,
        headers={
            "User-Agent": "localcheck-tester/0.0",
        },
        timeout=20,
    )
    if resp.headers['x-w3c-validator-status'] == 'Valid':
        print("Page validates!")
        sys.exit(0)
    elif resp.headers['x-w3c-validator-status'] == 'Invalid':
        print("Invalid!")
        print("Errors: %s" % resp.headers['x-w3c-validator-errors'])
        print("Warnings: %s" % resp.headers['x-w3c-validator-warnings'])
        hp = html.parser.HTMLParser()
        for m in re.findall('<li class="msg_err">.*?</li>', resp.text, re.DOTALL):
            r = re.search('<em>Line <a href="[^"]+">(\d+)</a>.*<span class="msg">(.*?)</span>', m, re.DOTALL)
            if r:
                print("Line %s (should be around %s): %s" % (r.group(1), int(r.group(1)) - firstline, hp.unescape(r.group(2))))
            r2 = re.search('<code class="input">(.*?)<strong title=".*?">(.*?)</strong>(.*?)</code>', m, re.DOTALL)
            if r2:
                s = "%s%s%s" % r2.groups()
                print("Source: %s" % hp.unescape(s))
            print("")
    else:
        print("Unknown status: %s" % headers['x-w3c-validator-status'])
        print(headers)
        sys.exit(1)
