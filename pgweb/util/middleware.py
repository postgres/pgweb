from pgweb.util.templateloader import initialize_template_collection, get_all_templates

import hashlib

# Use thread local storage to pass the username down.
# http://code.djangoproject.com/wiki/CookBookThreadlocalsAndUser
try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()
def get_current_user():
	return getattr(_thread_locals, 'user', None)


# General middleware for all middleware functionality specific to the pgweb
# project.
class PgMiddleware(object):
	def process_view(self, request, view_func, view_args, view_kwargs):
		return None

	def process_request(self, request):
# Thread local store for username, see comment at the top of this file
		_thread_locals.user = getattr(request, 'user', None)
		initialize_template_collection()

	def process_response(self, request, response):
		response['xkey'] = ' '.join(["pgwt_{0}".format(hashlib.md5(t).hexdigest()) for t in get_all_templates()])
		return response
