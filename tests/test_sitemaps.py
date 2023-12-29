import pytest

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


class SampleObject:
    sitemap_priority = 1

    def __init__(self, *args, **kwargs):
        self.sitemap_changefreq = kwargs.get("freq", 1)

    def get_sitemap_changefreq_display(self):
        return "Always"


def test_searchmetabasesitemap_changefreq():
    sitemap = SearchMetaBaseSitemap()
    obj = SampleObject()
    assert sitemap.changefreq(obj) == "always"

    obj = SampleObject(freq=None)
    assert sitemap.changefreq(obj) is None


def test_searchmetabasesitemap_priority():
    sitemap = SearchMetaBaseSitemap()
    obj = SampleObject()
    assert sitemap.priority(obj) == 1


def test_register():
    register(SitemapModel)

    with pytest.raises(SitemapRegistrationError):
        register(SitemapModel)

    assert registered_sitemaps["testing_app-sitemapmodel"].__bases__[0] == BaseSitemap

    register(SearchMetaBaseModel)
    assert (
        registered_sitemaps["testing_app-searchmetabasemodel"].__bases__[0]
        == SearchMetaBaseSitemap
    )

    register(OnlineBaseModel)
    assert (
        registered_sitemaps["testing_app-onlinebasemodel"].__bases__[0]
        == OnlineBaseSitemap
    )

    register(PublishedBaseModel)
    assert (
        registered_sitemaps["testing_app-publishedbasemodel"].__bases__[0]
        == PublishedBaseSitemap
    )

    register(PageBaseModel)
    assert (
        registered_sitemaps["testing_app-pagebasemodel"].__bases__[0] == PageBaseSitemap
    )
