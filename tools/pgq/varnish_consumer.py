#!/usr/bin/env python
#
# A pgq consumer that generates varnish purge requests to expire things from
# the frontend caches.
#
# Reads the file varnish_pgq.ini, which is a normal pgq configuration file.
# Will look for any section starting with varnish_purger_<name>, and start one
# purger for each such section purging from the frontend <name>.
#
# Each purger will run in a process of it's own, because pgq doesn't support
# running different consumers in different threads.
#
# Purging is done by sending a regular GET request to /varnish-purge-url, with
# the regular expression to purge in the http header X-Purge-URL.
#
# Retrying is handled automatically by pgq. In case a subprocess dies, it will
# be restarted regularly by the remaining watchdog process.
#
#

import httplib
import signal
import sys
import time
import datetime
from ConfigParser import ConfigParser
from multiprocessing import Process

import pgq

def print_t(s):
	print "%s: %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), s)

class VarnishPurger(pgq.Consumer):
	"""
	pgq consumer that purges URLs from varnish as they appear in the queue.
	"""

	def __init__(self, frontend):
		self.frontend = frontend
		super(VarnishPurger, self).__init__('varnish_purger_%s' % frontend, 'db', ['varnish_pgq.ini'])

	def process_batch(self, db, batch_id, ev_list):
		"Called by pgq for each batch of events to run."

		for ev in ev_list:
			if ev.type == 'P':
				# 'P' events means purge.
				print_t("Purging '%s' on %s" % (ev.data, self.frontend))
				try:
					if self.do_purge(ev.data):
						ev.tag_done()
				except Exception, e:
					print_t("Failed to purge '%s' on '%s': %s" % (ev.data, self.frontend, e))
			elif ev.type == 'X':
				# 'X' events means ban expression (rather than just urls)
				print_t("Purging expression '%s' on %s" % (ev.data, self.frontend))
				try:
					if self.do_purge_expr(ev.data):
						ev.tag_done()
				except Exception, e:
					print_t("Failed to purge expression '%s' on '%s': %s" % (ev.data, self.frontend, e))
			else:
				print_t("Unknown event type '%s'" % ev.type)


	def internal_purge(self, headers):
		"""
		Send the actual purge request, by contacting the frontend this
		purger is running for and sending a GET request to the special URL
		with our regexp in a special header.
		"""
		conn = httplib.HTTPConnection('%s.postgresql.org' % self.frontend)
		conn.request("GET", "/varnish-purge-url", '', headers)
		resp = conn.getresponse()
		conn.close()
		if resp.status == 200:
			return True

		print_t("Varnish purge returned status %s (%s)" % (resp.status, resp.reason))
		return False

	def do_purge(self, url):
		return self.internal_purge({'X-Purge-URL': url})

	def do_purge_expr(self, expr):
		return self.internal_purge({'X-Purge-Expr': expr})

class PurgerProcess(object):
	"""
	Wrapper class that represents a subprocess that runs a varnish purger.
	"""
	def __init__(self, frontend):
		self.frontend = frontend
		self.start()

	def start(self):
		self.process = Process(target=self._run, name=frontend)
		self.process.start()

	def _run(self):
		# NOTE! This runs in the client! Must *NOT* be called from the
		# parent process!

		# Start by turning off signals so we don't try to restart ourselves
		# and others, entering into possible infinite recursion.
		signal.signal(signal.SIGTERM, signal.SIG_DFL)
		signal.signal(signal.SIGQUIT, signal.SIG_DFL)
		signal.signal(signal.SIGHUP, signal.SIG_DFL)

		# Start and run the consumer
		print_t("Initiating run of %s" % self.frontend)
		self.purger = VarnishPurger(frontend)
		self.purger.start()

	def validate(self):
		"""
		Validate that the process is running. If it's no longer running,
		try starting a new one.
		"""
		if not self.process.is_alive():
			# Ugh!
			print_t("Process for '%s' died!" % self.frontend)
			self.process.join()
			print_t("Attempting restart of '%s'!" % self.frontend)
			self.start()

	def terminate(self):
		"""
		Terminate the process running this purger.
		"""
		print_t("Terminating process for '%s'" % self.frontend)
		self.process.terminate()
		self.process.join()


# We need to keep the list of purgers in a global variable, so we can kill
# them off from the signal handler.
global purgers
purgers = []

def sighandler(signal, frame):
	print_t("Received terminating signal, shutting down subprocesses")
	for p in purgers:
		p.terminate()
	sys.exit(0)


if __name__=="__main__":
	cp = ConfigParser()
	cp.read('varnish_pgq.ini')

	if len(sys.argv) > 2 and sys.argv[1] == "-logfile":
		# Redirect to whatever is in sys.argv[2]
		# (yes, this is a really ugly way of doing things..)
		f = open(sys.argv[2], "a", 0)
		sys.stdout = f

	# Trap signals that shut us down, so we can kill off our subprocesses
	# before we die.
	signal.signal(signal.SIGTERM, sighandler)
	signal.signal(signal.SIGQUIT, sighandler)
	signal.signal(signal.SIGHUP, sighandler)

	# Start one process for each of the configured purgers
	for frontend in [section[15:] for section in cp.sections() if section[:15] == 'varnish_purger_']:
		purgers.append(PurgerProcess(frontend))

	# Loop forever, restarting any worker process that has potentially died
	while True:
		for p in purgers:
			p.validate()
		time.sleep(10)
