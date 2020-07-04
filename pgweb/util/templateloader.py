from django.template import Origin, TemplateDoesNotExist
import django.template.loaders.base

# Store in TLS, since a template loader can't access the request
try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()


def initialize_template_collection():
    _thread_locals.templates = []


def get_all_templates():
    return getattr(_thread_locals, 'templates', [])


class TrackingTemplateLoader(django.template.loaders.base.Loader):
    def get_template_sources(self, template_name):
        _thread_locals.templates = getattr(_thread_locals, 'templates', []) + [template_name, ]
        yield Origin(None)

    def get_contents(self, origin):
        raise TemplateDoesNotExist(origin)
