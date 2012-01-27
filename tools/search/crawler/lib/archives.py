import datetime
import httplib
from Queue import Queue
import threading
import sys
import time

from lib.log import log
from lib.parsers import ArchivesParser

class MultiListCrawler(object):
	def __init__(self, lists, conn, status_interval=30, commit_interval=500):
		self.lists = lists
		self.conn = conn
		self.status_interval = status_interval
		self.commit_interval = commit_interval

		self.queue = Queue()
		self.counter = 0
		self.counterlock = threading.RLock()
		self.stopevent = threading.Event()

	def crawl(self, full=False, month=None):
		# Each thread can independently run on one month, so we can get
		# a reasonable spread. Therefor, submit them as separate jobs
		# to the queue.
		for listid, listname in self.lists:
			if full:
				# Generate a sequence of everything to index
				for year in range(1997, datetime.datetime.now().year+1):
					for month in range(1,13):
						self.queue.put((listid, listname, year, month, -1))
			elif month:
				# Do one specific month
				pieces = month.split("-")
				if len(pieces) != 2:
					print "Month format is <y>-<m>, cannot parse '%s'" % month
					sys.exit(1)
				try:
					pieces = [int(x) for x in pieces]
				except:
					print "Month format is <y>-<m>, cannot convert '%s' to integers" % month
					sys.exit(1)
				self.queue.put((listid, listname, pieces[0], pieces[1], -1))
			else:
				# In incremental scan, we check the current month and the
				# previous one, but only for new messages.
				curs = self.conn.cursor()
				curr = datetime.date.today()
				if curr.month == 1:
					prev = datetime.date(curr.year-1, 12, 1)
				else:
					prev = datetime.date(curr.year, curr.month-1, 1)

				for d in curr, prev:
					# Figure out what the highest indexed page in this
					# month is.
					curs.execute("SELECT max(msgnum) FROM messages WHERE list=%(list)s AND year=%(year)s AND month=%(month)s", {
							'list': listid,
							'year': d.year,
							'month': d.month,
							})
					x = curs.fetchall()
					if x[0][0]:
						maxmsg = x[0][0]
					else:
						maxmsg = -1
					self.queue.put((listid, listname, d.year, d.month, maxmsg))

		for x in range(5):
			t = threading.Thread(name="Indexer %s" % x,
								 target = lambda: self.crawl_from_queue())
			t.daemon= True
			t.start()

		t = threading.Thread(name="statusthread", target = lambda: self.status_thread())
		t.daemon = True
		t.start()

		# XXX: need to find a way to deal with all threads crashed and
		# not done here yet!
		self.queue.join()
		self.stopevent.set()

		return self.counter

	def status_thread(self):
		lastcommit = 0
		starttime = time.time()
		while not self.stopevent.is_set():
			self.stopevent.wait(self.status_interval)
			nowtime = time.time()
			with self.counterlock:
				log("Indexed %s messages so far (%s active threads, %s months still queued, %.1f msg/sec)" % (
					self.counter,
					threading.active_count() - 2 , # main thread + status thread
					self.queue.qsize(),
					self.counter / (nowtime - starttime),
					))
				# Commit every 500 messages
				if self.counter - lastcommit > self.commit_interval:
					lastcommit = self.counter
					self.conn.commit()

	def crawl_from_queue(self):
		while not self.stopevent.is_set():
			(listid, listname, year, month, maxmsg) = self.queue.get()
			self.crawl_month(listid, listname, year, month, maxmsg)
			self.queue.task_done()

	def crawl_month(self, listid, listname, year, month, maxmsg):
		currentmsg = maxmsg
		while True:
			currentmsg += 1
			try:
				if not self.crawl_single_message(listid, listname, year, month, currentmsg):
					break
			except Exception, e:
				log("Exception when crawling %s/%s/%s/%s - %s" % (
					listname, year, month, currentmsg, e))
				# Continue on to try the next message

	def crawl_single_message(self, listid, listname, year, month, msgnum):
		curs = self.conn.cursor()
		h = httplib.HTTPConnection(host="archives.postgresql.org",
								   port=80,
								   strict=True,
								   timeout=10)
		url = "/%s/%04d-%02d/msg%05d.php" % (
			listname,
			year,
			month,
			msgnum)
		h.putrequest("GET", url)
		h.putheader("User-agent", "pgsearch/0.2")
		h.putheader("Connection", "close")
		h.endheaders()
		resp = h.getresponse()
		txt = resp.read()
		h.close()

		if resp.status == 404:
			# Past the end of the month
			return False
		elif resp.status != 200:
			raise Exception("%s/%s/%s/%s returned status %s" % (listname, year, month, msgnum, resp.status))

		# Else we have the message!
		p = ArchivesParser()
		if not p.parse(txt):
			log("Failed to parse %s/%s/%s/%s" % (listname, year, month, msgnum))
			# We return true to move on to the next message anyway!
			return True
		curs.execute("INSERT INTO messages (list, year, month, msgnum, date, subject, author, txt, fti) VALUES (%(listid)s, %(year)s, %(month)s, %(msgnum)s, %(date)s, %(subject)s, %(author)s, %(txt)s, setweight(to_tsvector('pg', %(subject)s), 'A') || to_tsvector('pg', %(txt)s))", {
				'listid': listid,
				'year': year,
				'month': month,
				'msgnum': msgnum,
				'date': p.date,
				'subject': p.subject[:127],
				'author': p.author[:127],
				'txt': p.body,
				})
		with self.counterlock:
			self.counter += 1

		return True
