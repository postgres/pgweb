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

import logging
log = logging.getLogger(__name__)


class ReCaptchaWidget(forms.widgets.Widget):
    def render(self, name, value, attrs=None):
        if settings.NOCAPTCHA:
            return u'Captcha disabled on this system'
        log.info("Generated captcha")
        return mark_safe(u'<div class="g-recaptcha" data-sitekey="{0}"></div>'.format(settings.RECAPTCHA_SITE_KEY))

    def value_from_datadict(self, data, files, name):
        if settings.NOCAPTCHA:
            return None
        if data.has_key('g-recaptcha-response'):
            return data['g-recaptcha-response']
        return None


class ReCaptchaField(forms.CharField):
    def __init__(self, *args, **kwargs):
        self.remoteip = None
        self.widget = ReCaptchaWidget()
        self.required = not settings.NOCAPTCHA
        super(ReCaptchaField, self).__init__(*args, **kwargs)

    def set_ip(self, ip):
        self.remoteip = ip

    def clean(self, value):
        if settings.NOCAPTCHA:
            return True

        super(ReCaptchaField, self).clean(value)

        # Validate the recaptcha
        c = httplib.HTTPSConnection('www.google.com', strict=True, timeout=5)
        param = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': value,
        }

        # Temporarily don't include remoteip, because it only shows our ssl terminating
        # frontends.
#        if self.remoteip:
#            param['remoteip'] = self.remoteip

        try:
            c.request('POST', '/recaptcha/api/siteverify', urllib.urlencode(param), {
                'Content-type': 'application/x-www-form-urlencoded',
            })
            c.sock.settimeout(10)
        except Exception, e:
            # Error to connect at TCP level
            log.error('Failed to connect to google recaptcha API: %s' % e)
            raise ValidationError('Failed in API call to google recaptcha')

        try:
            r = c.getresponse()
        except:
            log.error('Failed in API call to google recaptcha')
            raise ValidationError('Failed in API call to google recaptcha')
        if r.status != 200:
            log.error('Invalid response code from google recaptcha')
            raise ValidationError('Invalid response code from google recaptcha')

        try:
            j = json.loads(r.read())
        except:
            log.error('Invalid response structure from google recaptcha')
            raise ValidationError('Invalid response structure from google recaptcha')

        if not j['success']:
            log.warning('Incorrect recaptcha entered. Trying again.')
            raise ValidationError('Invalid. Try again.')

        # Recaptcha validated ok!
        log.info("Successful recaptcha validation")
        return True
