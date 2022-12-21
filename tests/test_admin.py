import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

from tests.media.factories import MinimalGIFFileFactory
from tests.testing_app.admin import RealPageBaseAdmin
from tests.testing_app.models import OnlineBaseModel, PageBaseModel
from uncms.admin import OnlineBaseAdmin, SEOQualityControlFilter


class AdminTest(TestCase):

    def setUp(self):
        factory = RequestFactory()
        self.request = factory.get('/')

        self.site = AdminSite()
        self.page_admin = OnlineBaseAdmin(OnlineBaseModel, self.site)

    def test_onlinebaseadmin_publish_selected(self):
        obj = OnlineBaseModel.objects.create(
            is_online=False,
        )

        self.assertFalse(obj.is_online)

        self.page_admin.publish_selected(self.request, OnlineBaseModel.objects.all())

        obj = OnlineBaseModel.objects.get(pk=obj.pk)
        self.assertTrue(obj.is_online)

    def test_onlinebaseadmin_unpublish_selected(self):
        obj = OnlineBaseModel.objects.create(
            is_online=True,
        )

        self.assertTrue(obj.is_online)

        self.page_admin.unpublish_selected(self.request, OnlineBaseModel.objects.all())

        obj = OnlineBaseModel.objects.get(pk=obj.pk)
        self.assertFalse(obj.is_online)


@pytest.mark.django_db
def test_quality_control_filter():
    rf = RequestFactory()
    image = MinimalGIFFileFactory()

    defaults = {
        'browser_title': 'Browser title',
        'meta_description': 'Meta description',
        'og_description': 'OG description',
        'og_image': image,
    }

    overrides = {
        'no-meta-description': [{'meta_description': ''}],
        'no-browser-title': [{'browser_title': ''}],
        'incomplete-opengraph-fields': [{'og_description': ''}],
    }

    objects = {}

    for key, value in overrides.items():
        objects[key] = []
        for fields in value:
            objects[key].append(PageBaseModel.objects.create(**dict(defaults, **fields)))

    for key, objs in objects.items():
        request = rf.get(f'/?seo_quality_control={key}')
        quality_filter = SEOQualityControlFilter(
            request,
            {'seo_quality_control': key},
            PageBaseModel,
            RealPageBaseAdmin,
        )
        ids = sorted(quality_filter.queryset(request, PageBaseModel.objects.all().values_list('id', flat=True)))
        assert ids == sorted(obj.id for obj in objs)
