# Test-only models.
from django.db import models

from uncms.media.models import FileRefField, ImageRefField, VideoFileRefField
from uncms.models import OnlineBase, PageBase, PublishedBase, SearchMetaBase
from uncms.models.base import (
    PublishedBaseSearchAdapter as CMSPublishedBaseSearchAdapter,
)
from uncms.models.base import (
    SearchMetaBaseSearchAdapter as CMSSearchMetaBaseSearchAdapter,
)
from uncms.models.fields import LinkField
from uncms.moderation.models import ModerationBase
from uncms.pages.models import ContentBase, Page


class PageContent(ContentBase):
    urlconf = "tests.pages.urls"


class PageContentWithSections(ContentBase):
    testing = models.CharField(
        max_length=20,
        default="testing",
    )


class Section(models.Model):
    page = models.ForeignKey(
        "pages.Page",
        on_delete=models.CASCADE,
    )

    title = models.CharField(
        max_length=100,
    )


class InlineModel(models.Model):
    page = models.ForeignKey(
        "pages.Page",
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
        return "/"


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


class LinkFieldModel(models.Model):
    link = LinkField()


class AbstractImageFieldModel(models.Model):
    image = ImageRefField(null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        abstract = True


class ImageFieldModel(AbstractImageFieldModel):
    pass


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
    urlconf = "tests.pages.urls"


class MiddlewareTestPage(ContentBase):
    pass


class MiddlewareURLsTestPage(ContentBase):
    urlconf = "tests.pages.urls"


# All of the below are for the tests for test_file_used_on.
class UsageModelOne(AbstractImageFieldModel):
    pass


class UsageModelTwo(AbstractImageFieldModel):
    pass


class UsageContentBaseModel(
    AbstractImageFieldModel, ContentBase
):  # pylint:disable=duplicate-code
    pass


class UsageContentBaseModelInline(AbstractImageFieldModel):
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
    )


class UsageModelOneInline(AbstractImageFieldModel):
    parent = models.ForeignKey(
        UsageModelOne,
        on_delete=models.CASCADE,
    )


# End models for test_file_used_on
