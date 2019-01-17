from django.template.defaultfilters import stringfilter
from django import template
import json


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
    if obj.errors and obj.errors[0] == u"This field is required.":
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
    return value.get(key, None)


@register.filter(name='json')
def tojson(value):
    return json.dumps(value)
