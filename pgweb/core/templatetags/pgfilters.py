from django.template.defaultfilters import stringfilter
from django import template
register = template.Library()

@register.filter(name='hidemail')
@stringfilter
def hidemail(value):
	return value.replace('@', ' at ')

@register.filter(name='class_name')
def class_name(ob):
	return ob.__class__.__name__

