import datetime
from functools import wraps
from django.contrib.auth.decorators import login_required as django_login_required

def nocache(fn):
	def _nocache(request, *_args, **_kwargs):
		resp = fn(request, *_args, **_kwargs)
		resp['Cache-Control'] = 's-maxage=0'
		return resp
	return _nocache

def cache(days=0, hours=0, minutes=0, seconds=0):
	"Set the server to cache object a specified time. td must be a timedelta object"
	def _cache(fn):
		def __cache(request, *_args, **_kwargs):
			resp = fn(request, *_args, **_kwargs)
			td = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
			resp['Cache-Control'] = 's-maxage=%s' % (td.days*3600*24 + td.seconds)
			return resp
		return __cache
	return _cache

from django.utils.decorators import available_attrs

# A wrapped version of login_required that throws an exception if it's
# used on a path that's not under /account/.
def login_required(f):
	@wraps(f)
	def wrapper(*args, **kwargs):
		request = args[0]
		if not request.path.startswith('/account/'):
			raise Exception("Login required in bad path, aborting with exception.")
		return django_login_required(f)(*args, **kwargs)
	return wrapper
