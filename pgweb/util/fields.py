from django.db import models
from django.core.exceptions import ValidationError

from .forms import ImageBinaryFormField

import io

from PIL import ImageFile

from pgweb.util.image import rescale_image, apply_exif_orientation, EXIF_ORIENTATION_TAG


class ImageBinaryField(models.Field):
    empty_values = [None, b'']

    def __init__(self, max_length, *args, **kwargs):
        self.resolution = kwargs.pop('resolution', None)
        self.auto_scale = kwargs.pop('auto_scale', False)
        super(ImageBinaryField, self).__init__(*args, **kwargs)
        self.max_length = max_length

    def deconstruct(self):
        name, path, args, kwargs = super(ImageBinaryField, self).deconstruct()
        return name, path, args, kwargs

    def get_internal_type(self):
        return "ImageBinaryField"

    def get_placeholder(self, value, compiler, connection):
        return '%s'

    def get_default(self):
        return b''

    def db_type(self, connection):
        return 'bytea'

    def get_db_prep_value(self, value, connection, prepared=False):
        value = super(ImageBinaryField, self).get_db_prep_value(value, connection, prepared)
        if value is not None:
            return connection.Database.Binary(value)
        return value

    def to_python(self, value):
        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError("Maximum size of file is {} bytes".format(self.max_length))

        if isinstance(value, memoryview):
            v = bytes(value)
        else:
            v = value
        try:
            p = ImageFile.Parser()
            p.feed(v)
            p.close()
            img = p.image
        except Exception as e:
            raise ValidationError("Could not parse image: %s" % e)

        if img.format.upper() not in ('JPEG', 'PNG'):
            raise ValidationError("Only JPEG or PNG files are allowed")

        # Bake EXIF orientation in; re-encode only when actually rotated so
        # untouched JPEGs are not needlessly recompressed.
        if img.getexif().get(EXIF_ORIENTATION_TAG, 1) != 1:
            fmt = img.format
            img = apply_exif_orientation(img)
            saver = io.BytesIO()
            img.save(saver, format=fmt)
            value = saver.getvalue()

        if self.resolution:
            if img.size[0] != self.resolution[0] or img.size[1] != self.resolution[1]:
                if self.auto_scale:
                    value = rescale_image(img, self.resolution, centered=True)
                else:
                    raise ValidationError("Image size must be {}x{}".format(*self.resolution))

        return value

    def save_form_data(self, instance, data):
        if data is not None:
            if not data:
                data = b''
            setattr(instance, self.name, data)

    def formfield(self, **kwargs):
        defaults = {'form_class': ImageBinaryFormField}
        defaults.update(kwargs)
        return super(ImageBinaryField, self).formfield(**defaults)
