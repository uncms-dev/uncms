from tests.testing_app.models import PageBaseModel
from uncms.pages.models import Page
from uncms.pages.types import Breadcrumb, Breadcrumbs


class SomeRandomClass:
    def __str__(self):
        return "String"


class SomeRandomClassWithURL(SomeRandomClass):
    def get_absolute_url(self):
        return "/wat/"


def test_breadcrumb_from_object():
    # test the "return the thing i was given" escape-hatch branch
    obj = Breadcrumb(title="Toast")
    assert Breadcrumb.from_object(obj) == obj

    # Make sure it is working with Page...
    obj = Page(title="Long title")
    breadcrumb = Breadcrumb.from_object(obj)
    assert breadcrumb.url == obj.get_absolute_url()

    # ...and is obeying "short_title"
    obj = Page(title="Long title", short_title="Short")
    breadcrumb = Breadcrumb.from_object(obj)
    assert breadcrumb.title == "Short"
    assert breadcrumb.url == obj.get_absolute_url()

    # Try giving it a PageBase derivative. These aren't special-cased, but
    # almost everything should inherit from it.
    obj = PageBaseModel(title="I am PageBase")
    breadcrumb = Breadcrumb.from_object(obj)
    assert breadcrumb.title == "I am PageBase"
    assert breadcrumb.url == "/"

    # Try giving it some random objects that both do and do not have URLs.
    obj = SomeRandomClass()
    breadcrumb = Breadcrumb.from_object(obj)
    assert breadcrumb.title == "String"
    assert breadcrumb.url is None

    obj = SomeRandomClassWithURL()
    breadcrumb = Breadcrumb.from_object(obj)
    assert breadcrumb.title == "String"
    assert breadcrumb.url == "/wat/"


def test_breadcrumbs_from_objects():
    # never throw an exception for an empty list
    # pylint:disable-next=use-implicit-booleaness-not-comparison
    assert Breadcrumbs.from_objects([]).items == []

    # Check all of the "single item" and "is iterable" branches are checked.
    page = Page(title="Page")
    some_random_class = SomeRandomClassWithURL()
    another_object = PageBaseModel(title="Another object")
    breadcrumbs = Breadcrumbs.from_objects([page, some_random_class], another_object)

    assert len(breadcrumbs.items) == 3
    assert breadcrumbs.count == 3
    assert breadcrumbs.items[0].title == "Page"
    assert breadcrumbs.items[0].tail is False
    assert breadcrumbs.items[0].index == 1
    assert breadcrumbs.items[0].index0 == 0

    assert breadcrumbs.items[1].title == "String"
    assert breadcrumbs.items[1].tail is False
    assert breadcrumbs.items[1].index == 2
    assert breadcrumbs.items[1].index0 == 1

    assert breadcrumbs.items[2].title == "Another object"
    assert breadcrumbs.items[2].tail is True
    assert breadcrumbs.items[2].index == 3
    assert breadcrumbs.items[2].index0 == 2
