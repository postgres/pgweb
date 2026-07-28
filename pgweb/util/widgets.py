from django import forms
from django.forms.widgets import Widget
from django.core.files.uploadedfile import UploadedFile
from django.utils.safestring import mark_safe
from django.template import loader

import base64


class TemplateRenderWidget(Widget):
    def __init__(self, *args, **kwargs):
        self.template_name = kwargs.pop('template')
        self.templatecontext = kwargs.pop('context')

        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        return self.templatecontext


class InlineImageUploadWidget(forms.ClearableFileInput):
    clear_checkbox_label = "Remove image"

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        if value and not isinstance(value, UploadedFile):
            context['widget']['value'] = base64.b64encode(value).decode('ascii')
            context['widget']['imagetype'] = 'image/png' if bytes(value[:8]) == b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A' else 'image/jpg'
        return mark_safe(loader.render_to_string('util/widgets/inline_image_upload.html', context))
