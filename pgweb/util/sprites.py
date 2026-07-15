import os
from PIL import Image

from pgweb.docs.views import booksdata


class HorizontalSpriteBuilder:
    def build_sprite_image(self):
        inputlist = list(self.items())

        fullwidth = len(inputlist) * (self.width + 1)

        fullimg = Image.new("RGBA", (fullwidth, self.height), (255, 0, 0, 0))
        for i, fn in enumerate(inputlist):
            im = Image.open(fn)
            ratio = min(self.width / im.width, self.height / im.height)
            new_width = round(im.width * ratio)
            new_height = round(im.height * ratio)

            im = im.resize((new_width, new_height), Image.LANCZOS)

            # Center if smaller
            xofs = (self.width - new_width) // 2
            yofs = (self.height - new_height) // 2

            fullimg.paste(im, (i * (self.width + 1) + xofs, yofs))

        fullimg.save(self.output, optimize=True, compress_level=9)


class BooksSpriteBuilder(HorizontalSpriteBuilder):
    width = 130
    height = 160
    # We use webp here because it's jpeg size (even smaller actually) and can be made transparent
    output = "media/img/docs/books/combined.webp"

    def items(self):
        return (os.path.join('media/img/docs/books/', b['image']) for b in booksdata.get()['books'])


sprites = {
    'books': BooksSpriteBuilder(),
}
