import datetime
from functools import wraps
from collections import defaultdict
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
            resp['Cache-Control'] = 's-maxage=%s' % (td.days * 3600 * 24 + td.seconds)
            return resp
        return __cache
    return _cache


def queryparams(*args):
    """
    Allow specified query parameters when calling function.
    NOTE! Must be the "outermost" decorator!!!
    """
    def _queryparams(fn):
        fn.queryparams = args
        return fn
    return _queryparams


def allow_frames(fn):
    def _allow_frames(request, *_args, **_kwargs):
        resp = fn(request, *_args, **_kwargs)
        resp.x_allow_frames = True
        return resp
    return _allow_frames


def content_sources(what, source):
    def _script_sources(fn):
        def __script_sources(request, *_args, **_kwargs):
            resp = fn(request, *_args, **_kwargs)
            if not hasattr(resp, 'x_allow_extra_sources'):
                resp.x_allow_extra_sources = defaultdict(list)
            resp.x_allow_extra_sources[what].append(source)
            return resp
        return __script_sources
    return _script_sources


def script_sources(source):
    return content_sources('script', source)


def frame_sources(source):
    return content_sources('frame', source)


# A wrapped version of login_required that throws an exception if it's
# used on a path that's not under /account/.
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        request = args[0]
        if not (request.path.startswith('/account/') or request.path.startswith('/admin/')):
            raise Exception("Login required in bad path, aborting with exception.")
        return django_login_required(f)(*args, **kwargs)
    return wrapper
