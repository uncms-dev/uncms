from dataclasses import dataclass
from functools import cached_property
from typing import List

from uncms.pages import get_page_model


@dataclass
class Breadcrumb:
    """
    `Breadcrumb` represents a single node in a breadcrumb navigation trail. It
    has a mandatory title, and an optional URL.
    """

    title: str
    url: str = None
    tail: bool = False
    index: int = False

    @classmethod
    def from_object(cls, obj):
        """
        Breadcrumb.from_object returns a Breadcrumb instance for the given
        object. It makes intelligent guesses about its title, and will use
        its get_absolute_url method if it has one.
        """
        page_model = get_page_model()

        # Simplify calling logic - if it's an instance of a Breadcrumb, return
        # it. We provide this escape hatch for cases where the current
        # breadcrumb isn't really an "object", such as the search results page
        # on a site, or maybe some super-special object that implements a URL
        # function called something other than the conventional
        # "get_absolute_url".
        if isinstance(obj, cls):
            return obj

        # We know how to get the URL and title of uncms.pages.models.Page -
        # it will definitely have `get_absolute_url`, and we should prefer its
        # `short_title` and fall back to `title` for the string representation.
        if isinstance(obj, page_model):
            return cls(title=obj.short_title or obj.title, url=obj.get_absolute_url())

        # Who knows?? but assume its __str__ is meaningful.
        title = str(obj)

        # Check for "get_absolute_url" in accordance with Django convention.
        if getattr(obj, "get_absolute_url", None):
            url = obj.get_absolute_url()

        else:
            url = None

        return cls(title=title, url=url)

    @property
    def index0(self):
        """
        index0 will return a zero-based index. `index` is 1-based for easier
        usage with templates.
        """
        return self.index - 1


@dataclass
class Breadcrumbs:
    """
    `Breadcrumbs` represents a breadcrumb trail, i.e. a list of Breadcrumb
    objects.

    It should always consider itself to have a full trail up to and including
    the current page. It does not concern itself with decisions such as
    whether the current page should be rendered in the breadcrumbs.
    """

    items: List[Breadcrumb]

    @classmethod
    def from_objects(cls, *args):
        items = []
        for arg in args:
            # Allow passing in an iterable to keep the calling logic simpler.
            try:
                items += [Breadcrumb.from_object(obj) for obj in arg]
            except TypeError:
                items.append(Breadcrumb.from_object(arg))

        # Set the last item to "last" - this simplifies checking if we are on
        # the final item, without keeping track of loop indices. Also handy
        # is that this means that the Jinja2 and Django templates can be byte
        # for byte identical, which means it's easy to ensure they are in sync
        # (make sure the templates give the same rendered output, and make
        # sure the templates are identical).
        try:
            items[-1].tail = True
        except IndexError:
            pass

        for index, item in enumerate(items):
            item.index = index + 1

        return cls(items=items)

    @cached_property
    def count(self):
        return len(self.items)
