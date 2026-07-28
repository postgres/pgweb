from django import forms
from django.forms.widgets import FILE_INPUT_CONTRADICTION

from .widgets import InlineImageUploadWidget


class ImageBinaryFormField(forms.Field):
    widget = InlineImageUploadWidget

    def to_python(self, value):
        if value is False:
            # Value gets set to False if the clear checkbox is marked
            return None
        if value == FILE_INPUT_CONTRADICTION:
            # This gets set if the user *both* uploads a new file *and* marks the clear checkbox
            return None
        if value is None:
            return None
        # value is an UploadedFile. to_python() can run more than once per
        # request (e.g. Field.has_changed() -> changed_data, or a second
        # full_clean()), so rewind before reading to avoid returning b'' on a
        # subsequent pass.
        value.seek(0)
        return value.read()

    def prepare_value(self, value):
        return value

    def clean(self, data, initial=None):
        if data is False:
            if not self.required:
                return False
            data = None
        if not data and initial:
            return initial
        return super(ImageBinaryFormField, self).clean(data)
