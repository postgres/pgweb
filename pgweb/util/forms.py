from django import forms
from django.forms.widgets import FILE_INPUT_CONTRADICTION

from functools import partial
from itertools import groupby
from operator import attrgetter

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


class GroupedIterator(forms.models.ModelChoiceIterator):
    def __init__(self, field, groupby):
        self.groupby = groupby
        super().__init__(field)

    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        for group, choices in groupby(self.queryset.all().order_by(self.groupby, *self.field.orderby), attrgetter(self.groupby)):
            yield (group,
                   [self.choice(c) for c in choices])


class GroupedModelChoiceField(forms.ModelChoiceField):
    def __init__(self, *args, groupfield, **kwargs):
        self.iterator = partial(GroupedIterator, groupby=groupfield)
        self.groupfield = groupfield
        super().__init__(*args, **kwargs)
        self.orderby = self.queryset.query.order_by
