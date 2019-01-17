from django.conf import settings

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
    def process_view(self, request, view_func, view_args, view_kwargs):
        return None

    def process_request(self, request):
# Thread local store for username, see comment at the top of this file
        _thread_locals.user = getattr(request, 'user', None)
        initialize_template_collection()

    def process_response(self, request, response):
        # Set xkey representing the templates that are in use so we can do efficient
        # varnish purging on commits.
        tlist = get_all_templates()
        if 'base/esi.html' in tlist:
            response['x-do-esi'] = "1"
            tlist.remove('base/esi.html')
        if tlist:
            response['xkey'] = ' '.join(["pgwt_{0}".format(hashlib.md5(t).hexdigest()) for t in tlist])

        # Set security headers
        sources = OrderedDict([
            ('default', ["'self'", ]),
            ('img', ['*', 'data:', ]),
            ('script', ["'self'", "www.google-analytics.com", "ssl.google-analytics.com", "data:"]),
            ('connect', ["'self'", "www.google-analytics.com", "ssl.google-analytics.com"]),
            ('media', ["'self'", ]),
            ('style', ["'self'", "fonts.googleapis.com"]),
            ('font', ["'self'", "fonts.gstatic.com", "data:" ]),
        ])
        if hasattr(response, 'x_allow_extra_sources'):
            for k,v in response.x_allow_extra_sources.items():
                if k in sources:
                    sources[k].extend(v)
                else:
                    sources[k] = v

        security_policies = ["{0}-src {1}".format(k," ".join(v)) for k,v in sources.items()]

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
