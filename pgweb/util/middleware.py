from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings

# Use thread local storage to pass the username down. 
# http://code.djangoproject.com/wiki/CookBookThreadlocalsAndUser
try:
    from threading import local, currentThread
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()
def get_current_user():
	return getattr(_thread_locals, 'user', None)


# General middleware for all middleware functionality specific to the pgweb
# project.
class PgMiddleware(object):
	def process_view(self, request, view_func, view_args, view_kwargs):
		# We implement the SSL verification in a middleware and not just a decorator, because
		# if we do it just in a decorator we'd have to add a decorator for each and every
		# view that *doesn't* require SSL. This is much easier, of course.

		if hasattr(settings,'NO_HTTPS_REDIRECT') and settings.NO_HTTPS_REDIRECT:
			return None

		# Don't redirect the admin interface, since the code is out of our control and we can't
		# give it the decorator require_ssl. We expect the web server config to deal with
		# redirecting *to* SSL here.
		if request.path.startswith('/admin'):
			return None

		if view_func.__name__ == '_require_ssl':
			# This view requires SSL, so check if we have it
			if not request.is_secure():
				# May need to deal with ports specified here?
				return HttpResponseRedirect(request.build_absolute_uri().replace('http://','https://',1))
		else:
			# This view must not use SSL, so make sure we don't have it
			if request.is_secure():
				return HttpResponseRedirect(request.build_absolute_uri().replace('https://','http://',1))

		return None

# Thread local store for username, see comment at the top of this file
	def process_request(self, request):
		_thread_locals.user = getattr(request, 'user', None)

