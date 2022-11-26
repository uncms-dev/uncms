import pytest
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings

from uncms.apps.testing_models.models import (
    PageBaseModel,
    PublishedBaseModel,
    PublishedBaseSearchAdapter,
    SearchMetaBaseModel,
    SearchMetaBaseSearchAdapter,
)


class ModelsBaseTest(TestCase):

    def test_publishedbasesearchadapter_get_live_queryset(self):
        search_adapter = PublishedBaseSearchAdapter(PublishedBaseModel)
        self.assertEqual(search_adapter.get_live_queryset().count(), 0)

        PublishedBaseModel.objects.create()
        self.assertEqual(search_adapter.get_live_queryset().count(), 1)

    def test_searchmetabase_get_context_data(self):
        obj = SearchMetaBaseModel.objects.create()
        expected_context = {
            'meta_description': '',
            'robots_follow': True,
            'robots_index': True,
            'title': ['SearchMetaBaseModel object', f'SearchMetaBaseModel object ({obj.pk})'],
            'robots_archive': True,
            'header': ['SearchMetaBaseModel object', f'SearchMetaBaseModel object ({obj.pk})'],
            'og_title': '',
            'og_description': '',
            'og_image': None,
            'twitter_card': None,
            'twitter_title': '',
            'twitter_description': '',
            'twitter_image': None
        }

        for key, value in obj.get_context_data().items():
            if isinstance(expected_context[key], list):
                self.assertIn(value, expected_context[key])
            else:
                self.assertEqual(value, expected_context[key])

    def test_searchmetabase_render(self):
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

        self.assertEqual(response.status_code, 200)

    def test_searchmetabasesearchadapter_get_live_queryset(self):
        search_adapter = SearchMetaBaseSearchAdapter(SearchMetaBaseModel)
        self.assertEqual(search_adapter.get_live_queryset().count(), 0)

        SearchMetaBaseModel.objects.create()
        self.assertEqual(search_adapter.get_live_queryset().count(), 1)

    def test_pagebasemodel_get_context_data(self):
        obj = PageBaseModel.objects.create()
        self.assertDictEqual(obj.get_context_data(), {
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
        })


@pytest.mark.django_db
def test_get_preview_url():
    obj = PageBaseModel.objects.create()

    assert obj.get_preview_url() == '/?preview=8b8dd47f46831cc58507'

    with override_settings(UNCMS={'PATH_SIGNING_SECRET': 'bonk'}):
        assert obj.get_preview_url() == '/?preview=1e4643d03f930d8c78bc'
