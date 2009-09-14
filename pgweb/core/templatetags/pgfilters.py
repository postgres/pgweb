from django.template.defaultfilters import stringfilter
from django import template
register = template.Library()

@register.filter(name='hidemail')
@stringfilter
def hidemail(value):
	return value.replace('@', ' at ')

