from django.db import connection
from django.conf import settings

from pgweb.mailqueue.util import send_simple_mail
from pgweb.util.helpers import template_to_string

def send_template_mail(sender, receiver, subject, templatename, templateattr={}, usergenerated=False):
	send_simple_mail(sender, receiver, subject,
					 template_to_string(templatename, templateattr),
					 usergenerated=usergenerated)

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




def varnish_purge(url):
	"""
	Purge the specified URL from Varnish. Will add initial anchor to the URL,
	but no trailing one, so by default a wildcard match is done.
	"""
	url = '^%s' % url
	connection.cursor().execute("SELECT varnish_purge(%s)", (url, ))
