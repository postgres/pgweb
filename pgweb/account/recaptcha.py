#
# Basic field and widget for simple recaptcha support using
# the v2 APIs.
#
from django import forms
from django.forms import ValidationError
from django.utils.safestring import mark_safe
from django.conf import settings

import requests

import logging
log = logging.getLogger(__name__)


class ReCaptchaWidget(forms.widgets.Widget):
    def render(self, name, value, attrs=None):
        if settings.NOCAPTCHA:
            return 'Captcha disabled on this system'
        log.info("Generated captcha")
        return mark_safe('<div class="g-recaptcha" data-sitekey="{0}"></div>'.format(settings.RECAPTCHA_SITE_KEY))

    def value_from_datadict(self, data, files, name):
        if settings.NOCAPTCHA:
            return None
        return data.get('g-recaptcha-response', None)


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
        param = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': value,
        }
        try:
            r = requests.post(
                "https://www.google.com/recaptcha/api/siteverify", param,
                headers={
                    'Content-type': 'application/x-www-form-urlencoded',
                },
                timeout=5,
            )
        except requests.exceptions.Timeout:
            log.error('Timeout when trying to connect to google recaptcha API')
            raise ValidationError('Timeout in API call to google recaptcha')

        if r.status_code != 200:
            log.error('Invalid response code from google recaptcha')
            raise ValidationError('Invalid response code from google recaptcha')

        try:
            j = r.json()
        except Exception as e:
            log.error('Invalid response structure from google recaptcha')
            raise ValidationError('Invalid response structure from google recaptcha')

        if not j['success']:
            log.warning('Incorrect recaptcha entered. Trying again.')
            raise ValidationError('Invalid. Try again.')

        # Recaptcha validated ok!
        log.info("Successful recaptcha validation")
        return True
