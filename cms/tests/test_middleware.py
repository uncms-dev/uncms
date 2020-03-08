import os

from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.template.response import SimpleTemplateResponse
from django.test import RequestFactory, TestCase
from watson import search

from ..apps.pages.models import ContentBase, Country, Page
from ..middleware import PublicationMiddleware


class TestContentBase(ContentBase):
    pass


class MiddlewareTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/?preview=a')
        self.request.user = AnonymousUser()

    def test_publicationmiddleware_process_request(self):
        publication_middleware = PublicationMiddleware()
        publication_middleware.process_request(self.request)

    def test_publicationmiddleware_process_response(self):
        class Context(dict):
            pass

        context = Context()
        context['page_obj'] = Context()
        context['page_obj'].has_other_pages = lambda: False

        response = SimpleTemplateResponse('pagination/pagination.html', context)
        publication_middleware = PublicationMiddleware()

        response = publication_middleware.process_response(self.request, response)

        self.assertEqual(response.status_code, 200)

    def test_publicationmiddleware_preview(self):
        with search.update_index():
            page_obj = Page.objects.create(
                title='Foo',
                content_type=ContentType.objects.get_for_model(TestContentBase),
                is_online=False,
            )

            content_obj = TestContentBase.objects.create(page=page_obj)

        middleware = [
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'cms.middleware.PublicationMiddleware',
            'cms.apps.pages.middleware.PageMiddleware',
        ]

        with self.settings(MIDDLEWARE=middleware):
            request = self.client.get(page_obj.get_absolute_url())
            self.assertEqual(request.status_code, 404)

            # Ensure preview mode (without a valid token) fails for
            # non-authenticated users.
            request = self.client.get(page_obj.get_absolute_url() + '?preview=1')
            self.assertEqual(request.status_code, 404)

            request = self.client.get(page_obj.get_preview_url())
            self.assertEqual(request.status_code, 200)
