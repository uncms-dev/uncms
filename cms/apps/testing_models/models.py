# Test-only models.
from django.db import models

from cms.apps.media.models import FileRefField, VideoFileRefField
from cms.apps.pages.models import ContentBase
from cms.models import OnlineBase, PageBase, PublishedBase, SearchMetaBase
from cms.models.base import \
    PublishedBaseSearchAdapter as CMSPublishedBaseSearchAdapter
from cms.models.base import \
    SearchMetaBaseSearchAdapter as CMSSearchMetaBaseSearchAdapter
from cms.models.fields import LinkField
from cms.plugins.moderation.models import ModerationBase


class PageContent(ContentBase):
    urlconf = 'cms.apps.pages.tests.urls'


class PageContentWithSections(ContentBase):
    testing = models.CharField(
        max_length=20,
        default='testing',
    )


class Section(models.Model):

    page = models.ForeignKey(
        'pages.Page',
        on_delete=models.CASCADE,
    )

    title = models.CharField(
        max_length=100,
    )


class InlineModel(models.Model):
    page = models.ForeignKey(
        'pages.Page',
        on_delete=models.CASCADE,
    )


class InlineModelNoPage(models.Model):
    pass


class PageContentWithFields(ContentBase):
    description = models.TextField(
        blank=True,
    )

    inline_model = models.ManyToManyField(
        InlineModelNoPage,
        blank=True,
    )


class SitemapModel(models.Model):
    pass


class PageBaseModel(PageBase):
    def get_absolute_url(self):
        return '/'


class SearchMetaBaseModel(SearchMetaBase):
    pass


class OnlineBaseModel(OnlineBase):
    pass


class PublishedBaseModel(PublishedBase):
    pass


class PublishedBaseSearchAdapter(CMSPublishedBaseSearchAdapter):
    pass


class SearchMetaBaseSearchAdapter(CMSSearchMetaBaseSearchAdapter):
    pass


class PermalinksModel(models.Model):

    def __str__(self):
        return 'Foo'

    def get_absolute_url(self):
        return '/foo/'


class HTMLModel(models.Model):
    def __str__(self):
        return 'Foo'

    def get_absolute_url(self):
        return '/foo/'


class LinkFieldModel(models.Model):

    link = LinkField()


class ModerationModel(ModerationBase):
    pass


class MediaTestModel(models.Model):

    file = FileRefField(
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    video_file = VideoFileRefField(
        blank=True,
        null=True,
    )


class TemplateTagTestPage(ContentBase):
    urlconf = 'cms.apps.pages.tests.urls'


class MiddlewareTestPage(ContentBase):
    pass


class MiddlewareURLsTestPage(ContentBase):
    urlconf = 'cms.apps.pages.tests.urls'
