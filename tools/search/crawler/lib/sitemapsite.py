import urllib
import xml.parsers.expat
import dateutil.parser

from lib.log import log
from lib.basecrawler import BaseSiteCrawler

class SitemapParser(object):
	def __init__(self):
		self.parser = xml.parsers.expat.ParserCreate()
		self.currenturl = ""
		self.currentprio = 0
		self.currentlastmod = None
		self.geturl = False
		self.getprio = False
		self.getlastmod = False
		self.currstr = ""
		self.urls = []

	def parse(self, f):
		self.parser.StartElementHandler = lambda name,attrs: self.processelement(name,attrs)
		self.parser.EndElementHandler = lambda name: self.processendelement(name)
		self.parser.CharacterDataHandler = lambda data: self.processcharacterdata(data)

		self.parser.ParseFile(f)

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
			self.urls.append((self.currenturl, self.currentprio, self.currentlastmod))

	def processcharacterdata(self, data):
		if self.geturl or self.getprio or self.getlastmod:
			self.currstr += data

class SitemapSiteCrawler(BaseSiteCrawler):
	def __init__(self, hostname, dbconn, siteid, serverip, https=False):
		super(SitemapSiteCrawler, self).__init__(hostname, dbconn, siteid, serverip, https)

	def init_crawl(self):
		# Fetch the sitemap. We ignore robots.txt in this case, and
		# assume it's always under /sitemap.xml
		u = urllib.urlopen("https://%s/sitemap.xml" % self.hostname)
		p = SitemapParser()
		p.parse(u)
		u.close()

		for url, prio, lastmod in p.urls:
			# Advance 8 characters - length of https://.
			url = url[len(self.hostname)+8:]
			if lastmod:
				if self.scantimes.has_key(url):
					if lastmod < self.scantimes[url]:
						# Not modified since last scan, so don't reload
						# Stick it in the list of pages we've scanned though,
						# to make sure we don't remove it...
						self.pages_crawled[url] = 1
						continue
			self.queue.put((url, prio))

		log("About to crawl %s pages from sitemap" % self.queue.qsize())

	# Stub functions used when crawling, ignored here
	def queue_url(self, url):
		pass

	def post_process_page(self, url):
		pass
