import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from tests.testing_app.admin import RealPageBaseAdmin
from tests.testing_app.models import OnlineBaseModel, PageBaseModel
from uncms.admin import OnlineBaseAdmin, SEOQualityControlFilter
from uncms.testhelpers.factories.media import MinimalGIFFileFactory


@pytest.mark.django_db
def test_onlinebaseadmin_publish_selected():
    page_admin = OnlineBaseAdmin(OnlineBaseModel, AdminSite())

    obj = OnlineBaseModel.objects.create(
        is_online=False,
    )
    assert obj.is_online is False

    page_admin.publish_selected(RequestFactory().get('/'), OnlineBaseModel.objects.all())

    obj.refresh_from_db()
    assert obj.is_online is True


@pytest.mark.django_db
def test_onlinebaseadmin_unpublish_selected():
    page_admin = OnlineBaseAdmin(OnlineBaseModel, AdminSite())

    obj = OnlineBaseModel.objects.create(
        is_online=True,
    )

    assert obj.is_online is True

    page_admin.unpublish_selected(RequestFactory().get('/'), OnlineBaseModel.objects.all())

    obj.refresh_from_db()
    assert obj.is_online is False


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
