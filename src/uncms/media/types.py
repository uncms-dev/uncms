from collections import OrderedDict
from dataclasses import dataclass, field


@dataclass
class Thumbnail:
    """
    Thumbnail is a dataclass used to represent an image thumbnail, with a
    couple of aspect ratio helpers.
    """

    url: str
    width: int
    height: int

    @property
    def aspect_ratio_string(self):
        return f"{self.width} / {self.height}"

    @property
    def height_ratio(self):
        return self.height / self.width

    @property
    def width_ratio(self):
        return self.width / self.height


@dataclass
class ThumbnailGroup:
    sizes: list = field(default_factory=list)

    def add(self, thumbnail):
        if not any(existing.width == thumbnail.width for existing in self.sizes):
            self.sizes.append(thumbnail)
            self.sizes.sort(key=lambda thing: thing.width)

    @property
    def srcset(self):
        if len(self.sizes) == 1:
            return self.sizes[0].url
        return ", ".join([f"{size.url} {size.width}w" for size in self.sizes])


@dataclass
class MultiThumbnail:
    """
    MultiThumbnail is a tiny dataclass that simplifies gathering multiple
    sizes of images.

    It provides an `add_size` method which adds a Thumbnail of the given MIME
    type, but only if an image with that width does not already exist in
    the ones that have been added already.

    This seems and is trivial, but it provides a huge simplification to the
    code in File.render_multisize.
    """

    formats: OrderedDict = field(default_factory=OrderedDict)

    def __init__(self):
        self.formats = OrderedDict()

    def add_size(self, mime_type: str, thumbnail: Thumbnail):
        self.formats.setdefault(mime_type, ThumbnailGroup())
        self.formats[mime_type].add(thumbnail)

    @property
    def items(self):
        """
        Tiny helper to expose formats.items() as a property. This permits
        using byte-for-byte exactly the same image template code for Django
        templates as Jinja2 (because Django does not have the parentheses for
        a function call).
        """
        return self.formats.items()
