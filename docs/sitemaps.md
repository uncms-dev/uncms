# Sitemaps

Any model that has a `get_absolute_url()` method should probably have its URL exposed in an [XML sitemap](https://en.wikipedia.org/wiki/Sitemaps) for easier indexing by search engines.
UnCMS has some helpers for this, which build on Django's [sitemaps framework](https://docs.djangoproject.com/en/dev/ref/contrib/sitemaps/).

First, you will wish to add `'django.contrib.sitemaps'` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # all your other apps here (you should be able to put the below
    # anywhere in the list)
    'django.contrib.sitemaps',
]
```

Next, you will need a URL route in your root `urls.py`. You will want something very much like this:

```python
from django.contrib.sitemaps import views as sitemaps_views
from django.urls import path

from uncms.sitemaps import registered_sitemaps

urlpatterns = [
    # ...your URLS here...
    path('sitemap.xml', sitemaps_views.index, {'sitemaps': registered_sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('sitemap-<str:section>.xml', sitemaps_views.sitemap, {'sitemaps': registered_sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]
```

There are, of course, helper sitemap classes for all of UnCMS's [helper models](helpers.md).
You don't need to worry about those most of the time.
The `uncms.sitemaps.register` function guesses an appropriate one for you:

```python
from uncms import sitemaps
sitemaps.register(YourModel)
```

It will guess which sitemap class to use based on which helper model your model inherits from,
checking `PageBase`, `SearchMetaBase`, and `OnlineBase`, in that order.

`uncms.sitemaps.BaseSitemap` does not do anything at all, other than returning all of the instances of a given model.
It assumes that the model implements a `get_absolute_url` method.

`uncms.sitemaps.OnlineBaseSitemap` inherits from `BaseSitemap`, but does not add anything.
The `OnlineBaseManager` used by `OnlineBase`, not `OnlineBaseSitemap`, ensures that only online objects are included in the sitemap.
However if you are inheriting from `OnlineBase` your sitemap should inherit from this class in case the implementation changes in the future.

`uncms.sitemaps.SearchMetaBaseSitemap` and `uncms.sitemaps.PageBaseSitemap` are for models that inherit from `SearchMetaBase` and `PageBase`.
They will add the change frequency and priority from the SEO fields on those models to the model's sitemap.
They will also exclude any objects that have been excluded from search engines (i.e. `robots_index == False`).

It may be useful to exclude certain URLs from your sitemap on criteria other than its "online" status.
Let's contrive an example.
Say you have an `Article` model in your site that inherits from `PageBase`, which has the option of just linking to an external URL, rather than having any content of its own.
We don't want those articles to appear in the sitemap. So we exclude them from indexing like so.

```python
from uncms import sitemaps

class ArticleSitemap(sitemaps.PageBaseSitemap):
    model = Article

    def items(self):
        return super().items().filter(external_url=None)

sitemaps.register(Article, sitemap_cls=ArticleSitemap)
```

Once you have a sitemap, you will want search engines to know where it lives.
Add an entry like this to your /robots.txt:

```
Sitemap: https://www.example.com/sitemap.xml
```
