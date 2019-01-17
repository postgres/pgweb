#!/usr/bin/env python
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
import urllib
import httplib
import re
import HTMLParser

BOUNDARY="-=--=foobar-=--="

def encode_multipart_formdata(fields, files):
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: text/html')
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = "\r\n".join(L)
    return body

if __name__=="__main__":
    if len(sys.argv) != 2:
        print "Usage: localhtmlvalidate.py <local url>"
        sys.exit(1)

    contents = urllib.urlopen(sys.argv[1]).read()

    # Try to figure out where the actual contents start :)
    try:
        firstline = contents.splitlines().index('<div id="pgContentWrap">')
    except ValueError:
        firstline = 0

    # Generate a form body
    body = encode_multipart_formdata([
            ('charset', 'utf-8'),
            ('doctype', 'inline'),
            ('group', '0'),
            ('verbose', '1'),
            ],
                                     [('uploaded_file', 'test.html', contents)])

    # Now submit it to the w3c validator
    h = httplib.HTTP("validator.w3.org")
    h.putrequest("POST", "/check")
    h.putheader("User-Agent: localcheck-tester/0.0")
    h.putheader("content-type", "multipart/form-data; boundary=%s" % BOUNDARY)
    h.putheader("content-length", str(len(body)))
    h.endheaders()
    h.send(body)
    errcode, errmsg, headers = h.getreply()
    rbody = h.getfile().read()
    if headers['x-w3c-validator-status'] == 'Valid':
        print "Page validates!"
        sys.exit(0)
    elif headers['x-w3c-validator-status'] == 'Invalid':
        print "Invalid!"
        print "Errors: %s" % headers['x-w3c-validator-errors']
        print "Warnings: %s" % headers['x-w3c-validator-warnings']
        hp = HTMLParser.HTMLParser()
        for m in re.findall('<li class="msg_err">.*?</li>', rbody, re.DOTALL):
            r = re.search('<em>Line (\d+).*<span class="msg">(.*?)</span>', m, re.DOTALL)
            print "Line %s (should be around %s): %s" % (r.group(1), int(r.group(1)) - firstline, hp.unescape(r.group(2)))

            r2 = re.search('<code class="input">(.*?)<strong title=".*?">(.*?)</strong>(.*?)</code>', unicode(m, 'utf8'), re.DOTALL)
            if r2:
                s = u"%s%s%s" % r2.groups()
                print "Source: %s" % hp.unescape(s).encode('utf-8')
            print ""
    else:
        print "Unknown status: %s" % headers['x-w3c-validator-status']
        print headers
        sys.exit(1)
    
    
