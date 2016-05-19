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

		# Does this view allow both SSL and non-ssl?
		if getattr(view_func, 'ssl_optional', False):
			# SSL is optional, so perform no redirects
			return None

		# Always redirect the admin interface to https
		if request.path.startswith('/admin'):
			if not request.is_secure():
				return HttpResponseRedirect(request.build_absolute_uri().replace('http://','https://',1))
			return None

		if getattr(view_func, 'ssl_required', False):
			# This view requires SSL, so check if we have it
			if not request.is_secure():
				# May need to deal with ports specified here?
				return HttpResponseRedirect(request.build_absolute_uri().replace('http://','https://',1))
		else:
			# This view must not use SSL, so make sure we don't have it
			if request.is_secure():
				return HttpResponseRedirect(request.build_absolute_uri().replace('https://','http://',1))

		return None

	def process_request(self, request):
# Thread local store for username, see comment at the top of this file
		_thread_locals.user = getattr(request, 'user', None)


# Protection middleware against badly encoded query strings.
# We could probably block this in the webserver further out, but this
# is a quick-fix. From django ticket #15152.
class RequestCheckMiddleware(object):
	def process_request(self, request):
		try:
			u'%s' % request.META.get('QUERY_STRING','')
		except UnicodeDecodeError:
			response = HttpResponse()
			response.status_code = 400  #Bad Request
			return response
