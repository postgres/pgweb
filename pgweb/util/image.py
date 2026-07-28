import io

from PIL import Image, ImageFile, ImageOps


# EXIF "Orientation" tag: 274 decimal = 0x0112 hex as per Exif 2.32.
# Values: 1 = normal, 2..8 = mirror/rotate transforms. Exposed here so we can
# peek at the tag without re-encoding the image.
EXIF_ORIENTATION_TAG = 0x0112


# Bake EXIF orientation into pixel data; PIL does not auto-rotate on open.
def apply_exif_orientation(img):
    return ImageOps.exif_transpose(img)


# Rescale an image in the form of bytes to a new set of bytes
# in the same format. Assumes the aspect is correct and that
# the incoming data is valid (it's expected to be for example
# the output of previous image operations)
def rescale_image_bytes(origbytes, resolution):
    p = ImageFile.Parser()
    p.feed(origbytes)
    p.close()
    img = p.image

    return rescale_image(img, resolution)


def rescale_image(img, resolution, centered=False):
    fmt = img.format  # transpose returns a new image with .format = None
    img = apply_exif_orientation(img)
    scale = min(
        float(resolution[0]) / float(img.size[0]),
        float(resolution[1]) / float(img.size[1]),
    )

    newimg = img.resize(
        (int(img.size[0] * scale), int(img.size[1] * scale)),
        Image.BICUBIC,
    )
    saver = io.BytesIO()
    if centered and newimg.size[0] != newimg.size[1]:
        # This is not a square, so we have to roll it again
        centeredimg = Image.new('RGBA', resolution)
        centeredimg.paste(newimg, (
            (resolution[0] - newimg.size[0]) // 2,
            (resolution[1] - newimg.size[1]) // 2,
        ))
        centeredimg.save(saver, format='PNG')
    else:
        newimg.save(saver, format=fmt)

    return saver.getvalue()


def get_image_contenttype_from_bytes(image):
    if bytearray(image[:3]) == b'\xFF\xD8\xFF':
        return 'image/jpeg'
    elif bytearray(image[:8]) == b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a':
        return 'image/png'
    raise Exception("Could not determine image format")
