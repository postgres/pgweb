from subprocess import Popen, PIPE
from email.mime.text import MIMEText

from pgweb.util.helpers import template_to_string

def prettySize(size):
	if size < 1024:
		return "%s bytes" % size
	suffixes = [("bytes",2**10), ("KB",2**20), ("MB",2**30), ("GB",2**40), ("TB",2**50)]
	for suf, lim in suffixes:
		if size > lim:
			continue
		else:
			return "%s %s" % (round(size/float(lim/2**10),2).__str__(),suf)

def sendmail(msg):
	pipe = Popen("sendmail -t", shell=True, stdin=PIPE).stdin
	pipe.write(msg.as_string())
	pipe.close()

def send_template_mail(sender, receiver, subject, templatename, templateattr={}):
	msg = MIMEText(
		template_to_string(templatename, templateattr),
		_charset='utf-8')
	msg['Subject'] = subject
	msg['To'] = receiver
	msg['From'] = sender
	sendmail(msg)


def is_behind_cache(request):
	"""
	Determine if the client is behind a cache. In this, we are only interested in our own
	frontend caches, we don't care about any client side caches or such things.
	"""
	if request.is_secure():
		# We never proxy https requests, so shortcut the check if it's there
		return False

	if request.META.has_key('HTTP_X_VARNISH'):
		# So, it's a varnish cache. Check that it's one of our frontends
		if request.META['REMOTE_ADDR'] in settings.FRONTEND_SERVERS:
			# Yup, it's one of our varnish servers, so we're behind a cache
			return True
		else:
			# It's someone elses varnish? Or misconfigured? Either way, don't claim
			# it's behind a cache.
			return False
	# X-Varnish not set, clearly we're not behind a cache
	return False


def get_client_ip(request):
	"""
	Get the IP of the client. If the client is served through our Varnish caches,
	make sure we get the *actual* client IP, and not the IP of the Varnish cache.
	"""
	if is_behind_cache:
		# When we are served behind a cache, our varnish is (should) always be configured
		# to set the X-Forwarded-For header. It will also remove any previous such header,
		# so we can always trust that header if it's there.
		try:
			return request.META['HTTP_X_FORWARDED_FOR']
		except:
			# In case something failed, we'll return the remote address. This is most likely
			# the varnish server itself, but it's better than aborting the request.
			return request.META['REMOTE_ADDR']
	else:
		return request.META['REMOTE_ADDR']
