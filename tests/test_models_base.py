import pytest
from django.test import RequestFactory
from django.test.utils import override_settings

from tests.testing_app.models import (
    PageBaseModel,
    PublishedBaseModel,
    PublishedBaseSearchAdapter,
    SearchMetaBaseModel,
    SearchMetaBaseSearchAdapter,
)


@pytest.mark.django_db
def test_onlinebase_get_preview_url():
    obj = PageBaseModel.objects.create()

    assert obj.get_preview_url() == '/?preview=8b8dd47f46831cc58507'

    with override_settings(UNCMS={'PATH_SIGNING_SECRET': 'bonk'}):
        assert obj.get_preview_url() == '/?preview=1e4643d03f930d8c78bc'


@pytest.mark.django_db
def test_pagebase_get_context_data():
    obj = PageBaseModel.objects.create()
    assert obj.get_context_data() == {
        'meta_description': '',
        'robots_follow': True,
        'robots_index': True,
        'title': '',
        'robots_archive': True,
        'header': '',
        'og_title': '',
        'og_description': '',
        'og_image': None,
        'twitter_card': None,
        'twitter_title': '',
        'twitter_description': '',
        'twitter_image': None
    }


@pytest.mark.django_db
def test_publishedbasesearchadapter_get_live_queryset():
    search_adapter = PublishedBaseSearchAdapter(PublishedBaseModel)
    assert search_adapter.get_live_queryset().count() == 0

    PublishedBaseModel.objects.create()
    assert search_adapter.get_live_queryset().count() == 1


@pytest.mark.django_db
def test_searchmetabase_get_context_data():
    obj = SearchMetaBaseModel.objects.create()
    expected_context = {
        'meta_description': '',
        'robots_follow': True,
        'robots_index': True,
        'title': f'SearchMetaBaseModel object ({obj.pk})',
        'robots_archive': True,
        'header': f'SearchMetaBaseModel object ({obj.pk})',
        'og_title': '',
        'og_description': '',
        'og_image': None,
        'twitter_card': None,
        'twitter_title': '',
        'twitter_description': '',
        'twitter_image': None
    }

    for key, value in obj.get_context_data().items():
        assert value == expected_context[key]


@pytest.mark.django_db
def test_searchmetabase_render():
    factory = RequestFactory()
    request = factory.get('/')
    request.pages = []

    class Context(dict):
        pass

    context = Context()
    context['page_obj'] = Context()
    context['page_obj'].has_other_pages = lambda: False

    obj = SearchMetaBaseModel.objects.create()
    response = obj.render(request, 'pagination/pagination.html', context)

    assert response.status_code == 200


@pytest.mark.django_db
def test_searchmetabasesearchadapter_get_live_queryset():
    search_adapter = SearchMetaBaseSearchAdapter(SearchMetaBaseModel)
    assert search_adapter.get_live_queryset().count() == 0

    SearchMetaBaseModel.objects.create()
    assert search_adapter.get_live_queryset().count() == 1

    SearchMetaBaseModel.objects.create(robots_index=False)
    assert search_adapter.get_live_queryset().count() == 1
