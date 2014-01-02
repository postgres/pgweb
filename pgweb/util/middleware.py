from django.http import HttpResponseRedirect
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

# Per django ticket #3777, make filters in admin be sticky
		path = request.path
		if path.find('/admin/') != -1:
			query_string = request.META['QUERY_STRING']
			if not request.META.has_key('HTTP_REFERER'):
				return None
			session = request.session
			if session.get('redirected', False):
				del session['redirected']
				return None
			referrer = request.META['HTTP_REFERER'].split('?')[0]
			referrer = referrer[referrer.find('/admin'):len(referrer)]
			key = 'key'+path.replace('/','_')
			if path == referrer:
				if query_string == '':
					if session.get(key,False):
						del session[key]
					return None
				request.session[key] = query_string
			else:
				if session.get(key,False):
					query_string=request.session.get(key)
					redirect_to = path+'?'+query_string
					request.session['redirected'] = True
					return HttpResponseRedirect(redirect_to)
				else:
					return None
