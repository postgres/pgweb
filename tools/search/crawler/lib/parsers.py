import re
import urllib
from StringIO import StringIO
import dateutil.parser
from datetime import timedelta

from HTMLParser import HTMLParser

from lib.log import log


class GenericHtmlParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.lasttag = None
        self.title = ""
        self.pagedata = StringIO()
        self.links = []
        self.inbody = False

    def handle_starttag(self, tag, attrs):
        self.lasttag = tag
        if tag == "body":
            self.inbody = True
        if tag == "a":
            for a, v in attrs:
                if a == "href":
                    self.links.append(v)

    def handle_endtag(self, tag):
        if tag == "body":
            self.inbody = False

    DATA_IGNORE_TAGS = ("script",)

    def handle_data(self, data):
        d = data.strip()
        if len(d) < 2:
            return

        if self.lasttag == "title":
            self.title += d
            return

        # Never store text found in the HEAD
        if not self.inbody:
            return

        # Ignore specific tags, like SCRIPT
        if self.lasttag in self.DATA_IGNORE_TAGS:
            return

        self.pagedata.write(d)
        self.pagedata.write("\n")

    def gettext(self):
        self.pagedata.seek(0)
        return self.pagedata.read()


class ArchivesParser(object):
    rematcher = re.compile("<!--X-Subject: ([^\n]*) -->.*<!--X-From-R13: ([^\n]*) -->.*<!--X-Date: ([^\n]*) -->.*<!--X-Body-of-Message-->(.*)<!--X-Body-of-Message-End-->", re.DOTALL)
    hp = HTMLParser()

    def __init__(self):
        self.subject = None
        self.author = None
        self.date = None
        self.body = None

    def parse(self, contents):
        contents = lossy_unicode(contents)
        match = self.rematcher.search(contents)
        if not match:
            return False
        self.subject = self.hp.unescape(match.group(1))
        self.author = self.almost_rot13(self.hp.unescape(match.group(2)))
        if not self.parse_date(self.hp.unescape(match.group(3))):
            return False
        self.body = self.hp.unescape(match.group(4))
        return True

    _date_multi_re = re.compile(' \((\w+\s\w+|)\)$')
    _date_trailing_envelope = re.compile('\s+\(envelope.*\)$')

    def parse_date(self, d):
        # For some reason, we have dates that look like this:
        # http://archives.postgresql.org/pgsql-bugs/1999-05/msg00018.php
        # Looks like an mhonarc bug, but let's just remove that trailing
        # stuff here to be sure...
        if self._date_trailing_envelope.search(d):
            d = self._date_trailing_envelope.sub('', d)

        # We have a number of dates in the format
        # "<full datespace> +0200 (MET DST)"
        # or similar. The problem coming from the space within the
        # parenthesis, or if the contents of the parenthesis is
        # completely empty
        if self._date_multi_re.search(d):
            d = self._date_multi_re.sub('', d)
        # Isn't it wonderful with a string with a trailing quote but no
        # leading quote? MUA's are weird...
        if d.endswith('"') and not d.startswith('"'):
            d = d[:-1]

        # We also have "known incorrect timezone specs".
        if d.endswith('MST7MDT'):
            d = d[:-4]
        elif d.endswith('METDST'):
            d = d[:-3]
        elif d.endswith('"MET'):
            d = d[:-4] + "MET"

        try:
            self.date = dateutil.parser.parse(d)
        except ValueError:
            log("Failed to parse date '%s'" % d)
            return False

        if self.date.utcoffset():
            # We have some messages with completely incorrect utc offsets,
            # so we need to reject those too
            if self.date.utcoffset() > timedelta(hours=12) or self.date.utcoffset() < timedelta(hours=-12):
                log("Failed to parse date %s', timezone offset out of range." % d)
                return False

        return True

    # Semi-hacked rot13, because the one used by mhonarc is broken.
    # So we copy the brokenness here.
    # This code is from MHonArc/ewhutil.pl, mrot13()
    _arot13_trans = dict(list(zip(list(map(ord,
                                           '@ABCDEFGHIJKLMNOPQRSTUVWXYZ[abcdefghijklmnopqrstuvwxyz')),
                                  'NOPQRSTUVWXYZ[@ABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm')))

    def almost_rot13(self, s):
        return str(s).translate(self._arot13_trans)


class RobotsParser(object):
    def __init__(self, url):
        try:
            u = urllib.urlopen(url)
            txt = u.read()
            u.close()
            self.disallows = []
            activeagent = False
            for l in txt.splitlines():
                if l.lower().startswith("user-agent: ") and len(l) > 12:
                    if l[12] == "*" or l[12:20] == "pgsearch":
                        activeagent = True
                    else:
                        activeagent = False
                if activeagent and l.lower().startswith("disallow: "):
                    self.disallows.append(l[10:])
        except Exception:
            self.disallows = []

    def block_url(self, url):
        # Assumes url comes in as relative
        for d in self.disallows:
            if url.startswith(d):
                return True
        return False


# Convert a string to unicode, try utf8 first, then latin1, then give
# up and do a best-effort utf8.
def lossy_unicode(s):
    try:
        return str(s, 'utf8')
    except UnicodeDecodeError:
        try:
            return str(s, 'latin1')
        except UnicodeDecodeError:
            return str(s, 'utf8', 'replace')
