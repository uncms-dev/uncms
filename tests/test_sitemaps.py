from django.test import TestCase

from tests.testing_app.models import (
    OnlineBaseModel,
    PageBaseModel,
    PublishedBaseModel,
    SearchMetaBaseModel,
    SitemapModel,
)
from uncms.sitemaps import (
    BaseSitemap,
    OnlineBaseSitemap,
    PageBaseSitemap,
    PublishedBaseSitemap,
    SearchMetaBaseSitemap,
    SitemapRegistrationError,
    register,
    registered_sitemaps,
)


class Object:

    sitemap_priority = 1

    def __init__(self, *args, **kwargs):
        self.sitemap_changefreq = kwargs.get('freq', 1)

    def get_sitemap_changefreq_display(self):
        return 'Always'


class TestSitemaps(TestCase):

    def test_searchmetabasesitemap_changefreq(self):
        sitemap = SearchMetaBaseSitemap()
        obj = Object()
        self.assertEqual(sitemap.changefreq(obj), 'always')

        obj = Object(freq=None)
        self.assertIsNone(sitemap.changefreq(obj))

    def test_searchmetabasesitemap_priority(self):
        sitemap = SearchMetaBaseSitemap()
        obj = Object()
        self.assertEqual(sitemap.priority(obj), 1)

    def test_register(self):
        register(SitemapModel)

        with self.assertRaises(SitemapRegistrationError):
            register(SitemapModel)

        self.assertEqual(
            registered_sitemaps['testing_app-sitemapmodel'].__bases__[0],
            BaseSitemap
        )

        register(SearchMetaBaseModel)

        self.assertEqual(
            registered_sitemaps['testing_app-searchmetabasemodel'].__bases__[0],
            SearchMetaBaseSitemap
        )

        register(OnlineBaseModel)

        self.assertEqual(
            registered_sitemaps['testing_app-onlinebasemodel'].__bases__[0],
            OnlineBaseSitemap
        )

        register(PublishedBaseModel)

        self.assertEqual(
            registered_sitemaps['testing_app-publishedbasemodel'].__bases__[0],
            PublishedBaseSitemap
        )

        register(PageBaseModel)

        self.assertEqual(
            registered_sitemaps['testing_app-pagebasemodel'].__bases__[0],
            PageBaseSitemap
        )
