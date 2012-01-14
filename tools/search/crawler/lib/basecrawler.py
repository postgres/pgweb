import datetime
import httplib
import time
from email.utils import formatdate, parsedate
import urlparse

from Queue import Queue
import threading

from lib.log import log
from lib.parsers import GenericHtmlParser, lossy_unicode

class BaseSiteCrawler(object):
	def __init__(self, hostname, dbconn, siteid, serverip=None):
		self.hostname = hostname
		self.dbconn = dbconn
		self.siteid = siteid
		self.serverip = serverip
		self.pages_crawled = {}
		self.pages_new = 0
		self.pages_updated = 0
		self.pages_deleted = 0
		self.status_interval = 5

		curs = dbconn.cursor()
		curs.execute("SELECT suburl, lastscanned FROM webpages WHERE site=%(id)s AND lastscanned IS NOT NULL", {'id': siteid})
		self.scantimes = dict(curs.fetchall())
		self.queue = Queue()
		self.counterlock = threading.RLock()
		self.stopevent = threading.Event()

	def crawl(self):
		self.init_crawl()

		# Fire off worker threads
		for x in range(5):
			t = threading.Thread(name="Indexer %s" % x,
					   target = lambda: self.crawl_from_queue())
			t.daemon = True
			t.start()

		t = threading.Thread(name="statusthread", target = lambda: self.status_thread())
		t.daemon = True
		t.start()

		# XXX: need to find a way to deal with all threads crashed and
		# not done here yet!
		self.queue.join()
		self.stopevent.set()

		# Remove all pages that we didn't crawl
		curs = self.dbconn.cursor()
		curs.execute("DELETE FROM webpages WHERE site=%(site)s AND NOT suburl=ANY(%(urls)s)", {
				'site': self.siteid,
				'urls': self.pages_crawled.keys(),
				})
		if curs.rowcount:
			log("Deleted %s pages no longer accessible" % curs.rowcount)
		self.pages_deleted += curs.rowcount

		self.dbconn.commit()
		log("Considered %s pages, wrote %s updated and %s new, deleted %s." % (len(self.pages_crawled), self.pages_updated, self.pages_new, self.pages_deleted))

	def status_thread(self):
		starttime = time.time()
		while not self.stopevent.is_set():
			self.stopevent.wait(self.status_interval)
			nowtime = time.time()
			with self.counterlock:
				log("Considered %s pages, wrote %s upd, %s new, %s del (%s threads, %s in queue, %.1f pages/sec)" % (
					len(self.pages_crawled),
					self.pages_updated,
					self.pages_new,
					self.pages_deleted,
					threading.active_count() - 2,
					self.queue.qsize(),
					len(self.pages_crawled) / (nowtime - starttime),
					))

	def crawl_from_queue(self):
		while not self.stopevent.is_set():
			(url, relprio) = self.queue.get()
			try:
				self.crawl_page(url, relprio)
			except Exception, e:
				log("Exception crawling '%s': %s" % (url, e))
			self.queue.task_done()

	def exclude_url(self, url):
		return False

	def crawl_page(self, url, relprio):
		if self.pages_crawled.has_key(url) or self.pages_crawled.has_key(url+"/"):
			return

		if self.exclude_url(url):
			return

		self.pages_crawled[url] = 1
		(result, pagedata, lastmod) = self.fetch_page(url)

		if result == 0:
			if pagedata == None:
				# Result ok but no data, means that the page was not modified.
				# Thus we can happily consider ourselves done here.
				return
		else:
			# Page failed to load or was a redirect, so remove from database
			curs = self.dbconn.cursor()
			curs.execute("DELETE FROM webpages WHERE site=%(id)s AND suburl=%(url)s", {
					'id': self.siteid,
					'url': url,
					})
			with self.counterlock:
				self.pages_deleted += curs.rowcount

			if result == 1:
				# Page was a redirect, so crawl into that page if we haven't
				# already done so.
				self.queue_url(pagedata)
			return

		# Try to convert pagedata to a unicode string
		pagedata = lossy_unicode(pagedata)
		try:
			self.page = self.parse_html(pagedata)
		except Exception, e:
			log("Failed to parse HTML for %s" % url)
			log(e)
			return

		self.save_page(url, lastmod, relprio)
		self.post_process_page(url)

	def save_page(self, url, lastmod, relprio):
		if relprio == 0.0:
			relprio = 0.5
		params = {
			'title': self.page.title,
			'txt': self.page.gettext(),
			'lastmod': lastmod,
			'site': self.siteid,
			'url': url,
			'relprio': relprio,
			}
		curs = self.dbconn.cursor()
		curs.execute("UPDATE webpages SET title=%(title)s, txt=%(txt)s, fti=to_tsvector(%(txt)s), lastscanned=%(lastmod)s, relprio=%(relprio)s WHERE site=%(site)s AND suburl=%(url)s", params)
		if curs.rowcount != 1:
			curs.execute("INSERT INTO webpages (site, suburl, title, txt, fti, lastscanned, relprio) VALUES (%(site)s, %(url)s, %(title)s, %(txt)s, to_tsvector(%(txt)s), %(lastmod)s, %(relprio)s)", params)
			with self.counterlock:
				self.pages_new += 1
		else:
			with self.counterlock:
				self.pages_updated += 1

	ACCEPTED_CONTENTTYPES = ("text/html", "text/plain", )
	def accept_contenttype(self, contenttype):
		# Split apart if there is a "; charset=" in it
		if contenttype.find(";"):
			contenttype = contenttype.split(';',2)[0]
		return contenttype in self.ACCEPTED_CONTENTTYPES

	def fetch_page(self, url):
		try:
			# Unfortunatley, persistent connections seem quite unreliable,
			# so create a new one for each page.
			h = httplib.HTTPConnection(host=self.serverip and self.serverip or self.hostname,
									   port=80,
									   strict=True,
									   timeout=10)
			h.putrequest("GET", url)
			h.putheader("User-agent","pgsearch/0.2")
			if self.serverip:
				h.putheader("Host", self.hostname)
			h.putheader("Connection","close")
			if self.scantimes.has_key(url):
				h.putheader("If-Modified-Since", formatdate(time.mktime(self.scantimes[url].timetuple())))
			h.endheaders()
			resp = h.getresponse()

			if resp.status == 200:
				if not self.accept_contenttype(resp.getheader("content-type")):
					# Content-type we're not interested in
					return (2, None, None)
				return (0, resp.read(), self.get_date(resp.getheader("last-modified")))
			elif resp.status == 304:
				# Not modified, so no need to reprocess, but also don't
				# give an error message for it...
				return (0, None, None)
			elif resp.status == 301:
				# A redirect... So try again with the redirected-to URL
				# We send this through our link resolver to deal with both
				# absolute and relative URLs
				if resp.getheader('location', '') == '':
					log("Url %s returned empty redirect" % url)
					return (2, None, None)

				for tgt in self.resolve_links([resp.getheader('location', '')], url):
					return (1, tgt, None)
				# No redirect at all found, becaue it was invalid?
				return (2, None, None)
			else:
				#print "Url %s returned status %s" % (url, resp.status)
				pass
		except Exception, e:
			log("Exception when loading url %s: %s" % (url, e))
		return (2, None, None)

	def get_date(self, date):
		d = parsedate(date)
		if d:
			return datetime.datetime.fromtimestamp(time.mktime(d))
		return datetime.datetime.now()

	def parse_html(self, page):
		if page == None:
			return None

		p = GenericHtmlParser()
		p.feed(page)
		return p

	def resolve_links(self, links, pageurl):
		for x in links:
			p = urlparse.urlsplit(x)
			if p.scheme == "http":
				if p.netloc != self.hostname:
					# Remote link
					continue
				# Turn this into a host-relative url
				p = ('', '', p.path, p.query, '')

			if p[4] != "" or p[3] != "":
				# Remove fragments (part of the url past #)
				p = (p[0], p[1], p[2], '', '')

			if p[0] == "":
				if p[2] == "":
					# Nothing in the path, so it's a pure fragment url
					continue

				if p[2][0] == "/":
					# Absolute link on this host, so just return it
					yield urlparse.urlunsplit(p)
				else:
					# Relative link
					yield urlparse.urljoin(pageurl, urlparse.urlunsplit(p))
			else:
				# Ignore unknown url schemes like mailto
				pass
