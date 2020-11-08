# Filter wrapping the python markdown library into a django template filter
from django import template
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

from pgweb.util.markup import pgmarkdown

register = template.Library()


@register.filter(is_safe=True)
def markdown(value, args=''):
    allow_images = False
    allow_relative_links = False

    if args:
        for a in args.split(','):
            if a == 'allowimages':
                allow_images = True
            elif a == 'allowrelativelinks':
                allow_relative_links = True
            else:
                raise ValueError("Invalid argument to markdown: {}".format(a))

    return mark_safe(pgmarkdown(
        force_text(value),
        allow_images=allow_images,
        allow_relative_links=allow_relative_links,
    ))
