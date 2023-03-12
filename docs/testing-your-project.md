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
    file = factory.django.FileField(from_func=lambda: BytesIO(b'Sample'))
```

### `uncms.testhelpers.factories.media.EmptyFileFactory`

`EmptyFileFactory` creates a file object in the [media app](media-app.md) with no contents.
It is useful when a model requires a file to be present,
but tests do not particularly care about its contents.

### `uncms.testhelpers.factories.media.SamplePNGFileFactory`

`SamplePNGFileFactory` creates a 1920x1080 PNG file in your media library.
It is useful for testing models which require a real image, or views which render them.

```python
import pytest
from uncms.testhelpers.factories.media import SamplePNGFileFactory


@pytest.mark.django_db
def test_example():
    test_file = SamplePNGFileFactory()
    assert test_file.width == 1920
```

### `uncms.testhelpers.factories.media.SampleJPEGFileFactory`

`SampleJPEGFileFactory` creates a 1920x1080 JPEG file in your media library.

```python
import pytest
from uncms.testhelpers.factories.media import SampleJPEGFileFactory


@pytest.mark.django_db
def test_example():
    test_file = SampleJPEGFileFactory()
    assert test_file.width == 1920
```

### `uncms.testhelpers.factories.media.SampleWebPFileFactory`

`SampleWebPFileFactory` generates a 1920x1080 WebP file in your media library.

```python
import pytest
from uncms.testhelpers.factories.media import SampleWebPFileFactory


@pytest.mark.django_db
def test_example():
    test_file = SampleWebPFileFactory()
    assert test_file.width == 1920
```

### `uncms.testhelpers.factories.media.MinimalGIFFileFactory`

`MinimalGIFFileFactory` generates the very minimum (that I know of) valid image for use in your media library. It is useful when your model requires an image, but your tests do not particularly care about its contents. It will be slightly faster than using the other example image file factories.

```python
import pytest
from uncms.testhelpers.factories.media import MinimalGIFFileFactory


@pytest.mark.django_db
def test_example():
    test_file = MinimalGIFFileFactory()
    assert test_file.is_image is True
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


@pytest.mark.django_Db
def test_example():
    homepage = PageFactory.create_tree(5, 4, 7)
    assert len(homepage.children) == 5
```
