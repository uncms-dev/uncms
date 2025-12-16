# Testing your project

A site that you have built with UnCMS will have tests (_right?_),
and your tests will invariably require generating test data.
And hopefully, you are using [Factory Boy](https://factoryboy.readthedocs.io/en/stable/) to generate test data;
if you are not, it would be a good idea to use Factory Boy, because it is good.

UnCMS comes with some factories for generating pages and media files in your tests. To use these factories, you will need to do two things:

* Install a recent version of Factory Boy, either by installing it directly (`pip install factory-boy`), or indirectly via the `testhelpers` extra (`pip install uncms[testhelpers]`).
* Add `uncms.testhelpers` to `INSTALLED_APPS` of your test settings. (It is not harmful to add it to your real settings, but it'll create a useless empty test page type in your admin.)

The sample tests below assume that you are using [pytest](https://pytest.org/) as your test runner, rather than Django's unit test framework.
The examples should be trivially adaptable to your favourite way of testing.

## The factories

### `uncms.testhelpers.factories.media.FileFactory`

`FileFactory` is a base class for generating files in the [media app](media-app.md).
This is not that useful by itself;
all the other file factories inherit from this.

```python
class SampleFileFactory(FileFactory):
    file = factory.django.FileField(from_func=lambda: BytesIO(b"Sample"))
```

`FileFactory` accepts various boolean keyword arguments to create different types of files ("traits", in Factory Boy terms).

If you pass `empty=True`, it creates a `File` instance with no contents. This is useful when a model or a test scenario requires a file to be present, but does not care about its contents.

For image testing, you can use `sample_png=True`, `sample_jpeg=True`, or `sample_webp=True` to create a 1920x1080 image file in your media library in PNG, JPEG, and WebP formats respectively. These are useful for testing models which require a real image, or views which render them. If you need an SVG file, pass `sample_svg=True` to generate a minimal, valid SVG file. The `minimal_gif` argument will create what I believe to be the smallest viable image file; that is useful if your tests merely require an image to be present.

```python
import pytest
from uncms.testhelpers.factories.media import FileFactory


@pytest.mark.django_db
def test_files():
    empty_file = FileFactory(empty=True)
    assert empty_file.is_image() is False

    png_file = FileFactory(sample_png=True)
    assert png_file.width == 1920

    minimal_image = FileFactory(minimal_gif=True)
    assert minimal_image.is_image() is True
```

### `uncms.testhelpers.factories.pages.PageFactory`

`PageFactory` takes care of generating [pages](pages-app.md) in your page tree.
You should instantiate it with at least a keyword argument `content`, which is an _unsaved_ instance of that page's content model.

```python
import pytest
from uncms.testhelpers.factories.pages import PageFactory

# Replace with one of your page's content models.
from myproject.news.models import NewsFeed


@pytest.mark.django_Db
def test_example():
    page = PageFactory(content=NewsFeed())
    assert page.content.__class__ == NewsFeed
```

It also has a `create_tree` method.
This is for generating a tree of pages, where you do not particularly care about exactly what content models those pages have.
It takes integers as positional arguments, which describe the _shape_ of the page tree.
`create_tree` will always create a home page.
The first argument describes how many pages are created as children of the home page (you can call these "top level pages").
The second describes how many pages should be created as children of _each_ of those top level pages.
The third will describe how many pages should be created as children of _those_ second-level pages, and so on.

This method will return the homepage that was created at the root of all of these pages.

For example if you want to create a menu of 5 top level pages (underneath the home page),
each of which has 4 children,
each of *those* having 7 children each,
you could do something like this:

```python
import pytest
from uncms.testhelpers.factories.pages import PageFactory


@pytest.mark.django_db
def test_example():
    homepage = PageFactory.create_tree(5, 4, 7)
    assert len(homepage.children) == 5
```
