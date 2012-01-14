import re

from basecrawler import BaseSiteCrawler
from parsers import RobotsParser

class GenericSiteCrawler(BaseSiteCrawler):
	def __init__(self, hostname, dbconn, siteid):
		super(GenericSiteCrawler, self).__init__(hostname, dbconn, siteid)

	def init_crawl(self):
		# Load robots.txt
		self.robots = RobotsParser("http://%s/robots.txt" % self.hostname)

		# We need to seed the crawler with every URL we've already seen, since
		# we don't recrawl the contents if they haven't changed.
		allpages = self.scantimes.keys()

		# Figure out if there are any excludes to deal with (beyond the
		# robots.txt ones)
		curs = self.dbconn.cursor()
		curs.execute("SELECT suburlre FROM site_excludes WHERE site=%(site)s", {
				'site': self.siteid,
				})
		self.extra_excludes = [re.compile(x) for x, in curs.fetchall()]

		# We *always* crawl the root page, of course
		self.queue.put(("/", 0.5))

		# Now do all the other pages
		for x in allpages:
			self.queue.put((x, 0.5))

	def exclude_url(self, url):
		if self.robots and self.robots.block_url(url):
			return True
		for r in self.extra_excludes:
			if r.search(url):
				return True
		return False

	def queue_url(self, url):
		self.queue.put((url.strip(), 0.5))

	def post_process_page(self, url):
		for l in self.resolve_links(self.page.links, url):
			if self.pages_crawled.has_key(l) or self.pages_crawled.has_key(l+"/"):
				continue
			if self.exclude_url(l):
				continue
			self.queue_url(l)
