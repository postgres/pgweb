from django.template.defaultfilters import stringfilter
from django import template, forms
from django.utils.safestring import mark_safe
from django.template.loader import get_template
from django.conf import settings

import os
from pathlib import Path
import json
import pynliner
import babel

register = template.Library()


@register.filter(name='class_name')
def class_name(ob):
    return ob.__class__.__name__


@register.filter(is_safe=True)
def field_class(value, arg):
    if 'class' in value.field.widget.attrs:
        c = arg + ' ' + value.field.widget.attrs['class']
    else:
        c = arg
    return value.as_widget(attrs={"class": c})


@register.filter(name='hidemail')
@stringfilter
def hidemail(value):
    return value.replace('@', ' at ')


@register.filter(is_safe=True)
def ischeckbox(obj):
    return obj.field.widget.__class__.__name__ in ["CheckboxInput", "CheckboxSelectMultiple"] and not getattr(obj.field, 'regular_field', False)


@register.filter(is_safe=True)
def ismultiplecheckboxes(obj):
    return obj.field.widget.__class__.__name__ == "CheckboxSelectMultiple" and not getattr(obj.field, 'regular_field', False)


@register.filter(is_safe=True)
def isrequired_error(obj):
    if obj.errors and obj.errors[0] == "This field is required.":
        return True
    return False


@register.filter(is_safe=True)
def label_class(value, arg):
    return value.label_tag(attrs={'class': arg})


@register.filter()
def planet_author(obj):
    # takes a ImportedRSSItem object from a Planet feed and extracts the author
    # information from the title
    return obj.title.split(':')[0]


@register.filter()
def planet_title(obj):
    # takes a ImportedRSSItem object from a Planet feed and extracts the info
    # specific to the title of the Planet entry
    return ":".join(obj.title.split(':')[1:])


@register.filter(name='dictlookup')
def dictlookup(value, key):
    if hasattr(key, 'value'):
        # Django 3.1 made this a ModelChoiceIteratorValue -- while we support both 2.2 and 3.2,
        # we need to treat them differently.
        return value.get(key.value, None)
    else:
        return value.get(key, None)


@register.filter(name='keylookup')
def keylookup(value, key):
    return value[key]


@register.filter(name='json')
def tojson(value):
    return json.dumps(value)


@register.filter()
def release_notes_pg_minor_version(minor_version, major_version):
    """Formats the minor version number to the appropriate PostgreSQL version.
    This is particularly for very old version of PostgreSQL.
    """
    if str(major_version) in ['0', '1']:
        return str(minor_version)[2:4]
    return minor_version


@register.filter()
def joinandor(value, andor):
    # Value is a list of objects. Join them on comma, add "and" or "or" before the last.
    if len(value) == 1:
        return str(value[0])

    if not isinstance(value, list):
        # Must have a list to index from the end
        value = list(value)

    return ", ".join([str(x) for x in value[:-1]]) + ' ' + andor + ' ' + str(value[-1])


@register.filter()
def list_templates(value):
    for f in Path(os.path.join(settings.PROJECT_ROOT, '../templates/', value)).iterdir():
        if f.is_file() and f.suffix == '.html':
            yield f.stem


@register.filter()
def sort_lower(value, reverse=False):
    return sorted(value, key=lambda x: x.lower(), reverse=reverse)


@register.filter()
def languagename(lang):
    try:
        return babel.Locale(lang).english_name
    except Exception:
        return lang


@register.simple_tag(takes_context=True)
def git_changes_link(context):
    return mark_safe('<a href="https://git.postgresql.org/gitweb/?p=pgweb.git;a=history;f=templates/{}">View</a> change history.'.format(context.template_name))


# CSS inlining (used for HTML email)
@register.tag
class InlineCss(template.Node):
    def __init__(self, nodes, arg):
        self.nodes = nodes
        self.arg = arg

    def render(self, context):
        contents = self.nodes.render(context)
        css = ''
        path = self.arg.resolve(context, True)
        if path is not None:
            css = get_template(path).render()

        p = pynliner.Pynliner().from_string(contents)
        p.with_cssString(css)
        return p.run()


@register.tag
def inlinecss(parser, token):
    nodes = parser.parse(('endinlinecss',))

    parser.delete_first_token()

    # First part of token is the tagname itself
    css = token.split_contents()[1]

    return InlineCss(
        nodes,
        parser.compile_filter(css),
    )
