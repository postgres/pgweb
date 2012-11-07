import datetime
from functools import wraps

def ssl_required(fn):
	def _require_ssl(request, *_args, **_kwargs):
		return fn(request, *_args, **_kwargs)
	_require_ssl.ssl_required = True
	# wraps retains original function attributes such as __name__, csrf_exempt, etc
	return wraps(_require_ssl)(fn)

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
