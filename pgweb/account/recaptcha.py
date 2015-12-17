#
# Basic field and widget for simple recaptcha support using
# the v2 APIs.
#
from django import forms
from django.forms import ValidationError
from django.utils.safestring import mark_safe
from django.conf import settings

import httplib
import urllib
import json

class ReCaptchaWidget(forms.widgets.Widget):
	def render(self, name, value, attrs=None):
		if settings.NOCAPTCHA:
			return u'Captcha disabled on this system'
		return mark_safe(u'<div class="g-recaptcha" data-sitekey="{0}"></div>'.format(settings.RECAPTCHA_SITE_KEY))

	def value_from_datadict(self, data, files, name):
		if settings.NOCAPTCHA:
			return None
		return data['g-recaptcha-response']


class ReCaptchaField(forms.CharField):
	def __init__(self, *args, **kwargs):
		self.widget = ReCaptchaWidget()
		self.required = not settings.NOCAPTCHA
		super(ReCaptchaField, self).__init__(*args, **kwargs)

	def clean(self, value):
		if settings.NOCAPTCHA:
			return True

		super(ReCaptchaField, self).clean(value)

		# Validate the recaptcha
		c = httplib.HTTPSConnection('www.google.com', strict=True, timeout=5)
		param = urllib.urlencode({
			'secret': settings.RECAPTCHA_SECRET_KEY,
			'response': value,
			# XXX: include remote ip!
		})
		c.request('POST', '/recaptcha/api/siteverify', param, {
			'Content-type': 'application/x-www-form-urlencoded',
		})
		c.sock.settimeout(10)
		try:
			r = c.getresponse()
		except:
			raise ValidationError('Failed in API call to google recaptcha')
		if r.status != 200:
			raise ValidationError('Invalid response code from google recaptcha')

		try:
			j = json.loads(r.read())
		except:
			raise ValidationError('Invalid response structure from google recaptcha')

		if not j['success']:
			raise ValidationError('Invalid. Try again.')

		# Recaptcha validated ok!
		return True
