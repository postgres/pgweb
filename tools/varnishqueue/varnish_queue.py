#!/usr/bin/env python
#
# varnish_queue.py - handle varnish purging queues
#
# Spawns a worker for each of the varnish servers, each will drain
# it's own queue as quickly as it can when told to do so by a notify.
#

import time
import sys
import select
import httplib
import multiprocessing
import logging
import psycopg2
from setproctitle import setproctitle

def do_purge(consumername, headers):
	try:
		conn = httplib.HTTPConnection('%s.postgresql.org' % consumername)
		conn.request("GET", "/varnish-purge-url", '', headers)
		resp = conn.getresponse()
		conn.close()
		if resp.status == 200:
			return True
		logging.warning("Varnish purge on %s returned status %s (%s)" % (consumername, resp.status, resp.reason))
		return False
	except Exception, ex:
		logging.error("Exception purging on %s: %s" % (consumername, ex))
		return False
	return True

def worker(consumerid, consumername, dsn):
	logging.info("Starting worker for %s" % consumername)
	setproctitle("varnish_queue - worker for %s" % consumername)

	conn = psycopg2.connect(dsn)
	curs = conn.cursor()
	curs.execute("LISTEN varnishqueue")
	conn.commit()

	while True:
		# See if there is something to pick up off the queue
		curs.execute("SELECT id, mode, expr FROM varnishqueue.queue WHERE consumerid=%(consumerid)s AND completed IS NULL FOR UPDATE", {
			'consumerid': consumerid,
		})
		res = curs.fetchall()

		failed = False

		if len(res):
			idlist = []
			for r in res:
				# Do something with this entry...
				if r[1] == 'P':
					logging.info("Purging url %s on %s" % (r[2], consumername))
					if not do_purge(consumername, {'X-Purge-URL': r[2]}):
						# Failed, but we will try again, so don't add to list of removals
						failed = True
						continue
				elif r[1] == 'X':
					logging.info("Purging expression %s on %s" % (r[2], consumername))
					if not do_purge(consumername, {'X-Purge-Expr': r[2]}):
						failed = True
						continue
				else:
					logging.warning("Unknown purge type %s on %s, ignoring." % (r[1], consumername))

				# Schedule for removal
				idlist.append(r[0])

			# Then remove from queue
			curs.execute("UPDATE varnishqueue.queue SET completed=CURRENT_TIMESTAMP WHERE id=ANY(%(idlist)s)", {
				'idlist': idlist
			})
			conn.commit()
			if failed:
				time.sleep(5)
		else:
			# Nothing, so roll back the transaction and wait
			conn.rollback()

			select.select([conn],[],[],5*60)
			conn.poll()
			while conn.notifies:
				conn.notifies.pop()
			# Loop back up and process the full queue


def housekeeper(dsn):
	logging.info("Starting housekeeper")
	setproctitle("varnish_queue - housekeeper")
	conn = psycopg2.connect(dsn)
	curs = conn.cursor()

	while True:
		curs.execute("DELETE FROM varnishqueue.queue WHERE completed IS NOT NULL")
		if curs.rowcount > 0:
			conn.commit()
		else:
			conn.rollback()
		time.sleep(5*60)


if __name__ == "__main__":
	if len(sys.argv) != 2:
		print "Usage: varnish_queue.py <dsn>"
		sys.exit(1)

	logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)

	conn = psycopg2.connect(sys.argv[1])

	curs = conn.cursor()
	curs.execute("SELECT consumerid, consumer FROM varnishqueue.consumers")
	consumers = curs.fetchall()
	conn.close()

	# Now spawn a worker for each
	processes = []
	for consumerid, consumername in consumers:
		p = multiprocessing.Process(target=worker, args=(consumerid, consumername, sys.argv[1]))
		p.start()
		processes.append(p)

	# Start a housekeeping process as well
	p = multiprocessing.Process(target=housekeeper, args=(sys.argv[1],))
	p.start()
	processes.append(p)

	# They should never die, but if they do, commit suicide and
	# restart everything.
	while True:
		processes[0].join(timeout=120)
		for p in processes:
			if not p.is_alive():
				logging.warning("Child process died, killing all and existing")
				for p2 in processes:
					try:
						p2.terminate()
					except:
						pass
				logging.error("Children killed, existing")
				sys.exit(1)
		# If all processes are alive, loop back up and try again
