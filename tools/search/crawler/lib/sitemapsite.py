import xml.parsers.expat
import dateutil.parser
import requests

from lib.log import log
from lib.basecrawler import BaseSiteCrawler


class SitemapParser(object):
    def __init__(self):
        self.urls = []

    def parse(self, data, internal=False):
        self.parser = xml.parsers.expat.ParserCreate()
        self.currenturl = ""
        self.currentprio = 0
        self.currentlastmod = None
        self.geturl = False
        self.getprio = False
        self.getlastmod = False
        self.currstr = ""
        self.internal = False
        self.parser.StartElementHandler = lambda name, attrs: self.processelement(name, attrs)
        self.parser.EndElementHandler = lambda name: self.processendelement(name)
        self.parser.CharacterDataHandler = lambda data: self.processcharacterdata(data)
        self.internal = internal

        self.parser.Parse(data)

    def processelement(self, name, attrs):
        if name == "url":
            self.currenturl = ""
            self.currentprio = 0
            self.currentlastmod = None
        elif name == "loc":
            self.geturl = True
            self.currstr = ""
        elif name == "priority":
            self.getprio = True
            self.currstr = ""
        elif name == "lastmod":
            self.getlastmod = True
            self.currstr = ""

    def processendelement(self, name):
        if name == "loc":
            self.geturl = False
            self.currenturl = self.currstr
        elif name == "priority":
            self.getprio = False
            self.currentprio = float(self.currstr)
        elif name == "lastmod":
            self.getlastmod = False
            self.currentlastmod = dateutil.parser.parse(self.currstr)
        elif name == "url":
            self.urls.append((self.currenturl, self.currentprio, self.currentlastmod, self.internal))

    def processcharacterdata(self, data):
        if self.geturl or self.getprio or self.getlastmod:
            self.currstr += data


class SitemapSiteCrawler(BaseSiteCrawler):
    def __init__(self, hostname, dbconn, siteid, serverip, https=False):
        super(SitemapSiteCrawler, self).__init__(hostname, dbconn, siteid, serverip, https)

    def init_crawl(self):
        # Fetch the sitemap. We ignore robots.txt in this case, and
        # assume it's always under /sitemap.xml
        r = requests.get("https://%s/sitemap.xml" % self.hostname)
        if r.status_code != 200:
            raise Exception("Could not load sitemap: %s" % r.status_code)

        p = SitemapParser()
        p.parse(r.text)

        # Attempt to fetch a sitempa_internal.xml. This is used to index
        # pages on our internal search engine that we don't want on
        # Google. They should also be excluded from default search
        # results (unless searching with a specific suburl)
        r = requests.get("https://%s/sitemap_internal.xml" % self.hostname)
        if r.status_code == 200:
            p.parse(r.text, True)

        for url, prio, lastmod, internal in p.urls:
            # Advance 8 characters - length of https://.
            url = url[len(self.hostname) + 8:]
            if lastmod:
                if url in self.scantimes:
                    if lastmod < self.scantimes[url]:
                        # Not modified since last scan, so don't reload
                        # Stick it in the list of pages we've scanned though,
                        # to make sure we don't remove it...
                        self.pages_crawled[url] = 1
                        continue
            self.queue.put((url, prio, internal))

        log("About to crawl %s pages from sitemap" % self.queue.qsize())

    # Stub functions used when crawling, ignored here
    def queue_url(self, url):
        pass

    def post_process_page(self, url):
        pass
