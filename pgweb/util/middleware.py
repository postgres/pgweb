from django.conf import settings
from django.http import QueryDict

from pgweb.util.templateloader import initialize_template_collection, get_all_templates

from collections import OrderedDict
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
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Thread local store for username, see comment at the top of this file
        _thread_locals.user = getattr(request, 'user', None)
        initialize_template_collection()

        # Call the view
        response = self.get_response(request)

        # Set xkey representing the templates that are in use so we can do efficient
        # varnish purging on commits.
        tlist = get_all_templates()
        if 'base/esi.html' in tlist:
            response['x-do-esi'] = "1"
            tlist.remove('base/esi.html')
        if tlist:
            response['xkey'] = ' '.join(["pgwt_{0}".format(hashlib.md5(t.encode('ascii', errors='replace')).hexdigest()) for t in tlist] + [response.get('xkey', '')])

        # Set security headers
        sources = OrderedDict([
            ('default', ["'self'", ]),
            ('img', ['*', 'data:', ]),
            ('script', ["'unsafe-eval'", "'self'", "www.google-analytics.com", "ssl.google-analytics.com", "www.googletagmanager.com", "tagmanager.google.com", "data:"]),
            ('connect', ["'self'", "www.google-analytics.com", "ssl.google-analytics.com"]),
            ('media', ["'self'", ]),
            ('style', ["'self'", "fonts.googleapis.com", "tagmanager.google.com"]),
            ('font', ["'self'", "fonts.gstatic.com", "data:", ]),
        ])
        if hasattr(response, 'x_allow_extra_sources'):
            for k, v in list(response.x_allow_extra_sources.items()):
                if k in sources:
                    sources[k].extend(v)
                else:
                    sources[k] = v

        security_policies = ["{0}-src {1}".format(k, " ".join(v)) for k, v in list(sources.items())]

        if not getattr(response, 'x_allow_frames', False):
            response['X-Frame-Options'] = 'DENY'
            security_policies.append("frame-ancestors 'none'")

        if hasattr(settings, 'SECURITY_POLICY_REPORT_URI'):
            security_policies.append("report-uri " + settings.SECURITY_POLICY_REPORT_URI)

        if security_policies:
            if getattr(settings, 'SECURITY_POLICY_REPORT_ONLY', False):
                response['Content-Security-Policy-Report-Only'] = " ; ".join(security_policies)
            else:
                response['Content-Security-Policy'] = " ; ".join(security_policies)

        response['X-XSS-Protection'] = "1; mode=block"
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Filter out any query parameters that are not explicitly allowed. We do the same thing in Varnish,
        # and it's better to also do it in django if they show up here, so issues because of it are caught
        # in local testing where there is no Varnish.
        if not request.GET:
            # If there are no parameters, just skip this whole process
            return None

        if request.path.startswith('/admin/'):
            # django-admin uses it a lot and it's not for us to change
            return None

        if settings.DEBUG_TOOLBAR and request.path.startswith('/__debug__/'):
            # The debug toolbar also uses a lot
            return None

        allowed = getattr(view_func, 'queryparams', None)

        if allowed:
            # Filter the QueryDict for only the allowed parameters
            result = request.GET.copy()
            for k in request.GET.keys():
                if k not in allowed:
                    del result[k]
            result.mutable = False
            request.GET = result
        else:
            request.GET = QueryDict()
        return None
