import markdown
from bleach.sanitizer import Cleaner
from bleach.html5lib_shim import Filter


# Tags and attributes generated by markdown (anything that's not
# generated by markdown is clearly manually added html)
# This list is from the bleach-allowlist module, but adding a dependency
# on it just to get two arrays seems silly.

_markdown_tags = [
    "h1", "h2", "h3", "h4", "h5", "h6",
    "b", "i", "strong", "em", "tt",
    "p", "br",
    "span", "div", "blockquote", "code", "pre", "hr",
    "ul", "ol", "li", "dd", "dt",
    # "img",     # img is optional in our markdown validation
    "a",
    "sub", "sup",
]

_markdown_attrs = {
    "*": ["id"],
    "img": ["src", "alt", "title"],
    "a": ["href", "alt", "title"],
}


# Prevent relative links, by simply removing any href tag that does not have
# a : in it.
class RelativeLinkFilter(Filter):
    def __iter__(self):
        for token in Filter.__iter__(self):
            if token['type'] in ['StartTag', 'EmptyTag'] and token['data']:
                if (None, 'href') in token['data']:
                    # This means a href attribute with no namespace
                    if ':' not in token['data'][(None, 'href')]:
                        # Relative link!
                        del token['data'][(None, 'href')]
            yield token


def pgmarkdown(value, allow_images=False, allow_relative_links=False):
    tags = _markdown_tags
    filters = []

    if allow_images:
        tags.append('img')
    if not allow_relative_links:
        filters.append(RelativeLinkFilter)

    cleaner = Cleaner(tags=tags, attributes=_markdown_attrs, filters=filters)

    return cleaner.clean(markdown.markdown(value))
