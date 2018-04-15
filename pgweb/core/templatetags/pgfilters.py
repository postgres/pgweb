from django.template.defaultfilters import stringfilter
from django import template
register = template.Library()

@register.filter(name='class_name')
def class_name(ob):
	return ob.__class__.__name__

@register.filter(is_safe=True)
def field_class(value, arg):
	return value.as_widget(attrs={"class": arg})

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
