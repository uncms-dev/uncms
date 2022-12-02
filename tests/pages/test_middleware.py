from dataclasses import dataclass

import pytest
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, HttpResponseNotFound
from django.test import RequestFactory, TestCase
from watson import search

from tests.testing_app.models import MiddlewareTestPage, MiddlewareURLsTestPage
from uncms.pages.middleware import PageMiddleware, RequestPageManager
from uncms.pages.models import Page


def _generate_pages(self):
    with search.update_index():
        content_type = ContentType.objects.get_for_model(MiddlewareTestPage)

        self.homepage = Page.objects.create(
            title="Homepage",
            slug='homepage',
            content_type=content_type,
        )

        MiddlewareTestPage.objects.create(
            page=self.homepage,
        )

        self.page_1 = Page.objects.create(
            title='Foo',
            slug='foo',
            parent=self.homepage,
            content_type=content_type,
        )

        MiddlewareTestPage.objects.create(
            page=self.page_1,
        )

        self.page_2 = Page.objects.create(
            title='Bar',
            slug='bar',
            parent=self.page_1,
            content_type=content_type,
        )

        MiddlewareTestPage.objects.create(
            page=self.page_2,
        )

        self.auth_page = Page.objects.create(
            title='Auth Page',
            slug='auth',
            parent=self.homepage,
            content_type=content_type,
            requires_authentication=True,
        )

        MiddlewareTestPage.objects.create(
            page=self.auth_page,
        )


class TestRequestPageManager(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('')
        self.page_manager = RequestPageManager(self.request)

    def test_homepage(self):
        self.assertIsNone(self.page_manager.homepage)

        _generate_pages(self)
        page_manager = RequestPageManager(self.request)
        self.assertTrue(page_manager.is_homepage)

    def test_breadcrumbs(self):
        _generate_pages(self)

        self.request = self.factory.get('/')
        page_manager = RequestPageManager(self.request)
        self.assertListEqual(page_manager.breadcrumbs, [
            self.homepage
        ])

        self.request = self.factory.get('/foo/')
        page_manager = RequestPageManager(self.request)
        self.assertListEqual(page_manager.breadcrumbs, [
            self.homepage,
            self.page_1
        ])

        self.request = self.factory.get('/foo/bar/')
        page_manager = RequestPageManager(self.request)
        self.assertListEqual(page_manager.breadcrumbs, [
            self.homepage,
            self.page_1,
            self.page_2
        ])

    def test_section(self):
        self.assertIsNone(self.page_manager.section)

        _generate_pages(self)

        self.request = self.factory.get('/foo/bar/')
        self.page_manager = RequestPageManager(self.request)
        self.assertEqual(self.page_manager.section, self.page_1)

    def test_subsection(self):
        self.assertIsNone(self.page_manager.subsection)

        _generate_pages(self)

        self.request = self.factory.get('/foo/bar/')
        self.page_manager = RequestPageManager(self.request)
        self.assertEqual(self.page_manager.subsection, self.page_2)

    def test_current(self):
        self.assertIsNone(self.page_manager.current)

        _generate_pages(self)

        self.request = self.factory.get('/foo/bar/')
        self.page_manager = RequestPageManager(self.request)
        self.assertEqual(self.page_manager.current, self.page_2)

    def test_is_exact(self):
        _generate_pages(self)
        self.page_manager.path = ''
        self.page_manager.path_info = ''
        self.assertFalse(self.page_manager.is_exact)

        self.request = self.factory.get('/foo/bar/')
        self.page_manager = RequestPageManager(self.request)
        self.assertTrue(self.page_manager.is_exact)


@dataclass
class MockUser:
    is_authenticated: bool


class TestPageMiddleware(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_process_response(self):  # pylint:disable=too-many-statements
        request = self.factory.get('/')
        response = HttpResponse()

        middleware = PageMiddleware(lambda: None)
        self.assertEqual(middleware.process_response(request, response), response)

        response = HttpResponseNotFound()
        page_request = self.factory.get('')
        request.pages = RequestPageManager(page_request)
        self.assertEqual(middleware.process_response(request, response), response)

        _generate_pages(self)

        request = self.factory.get('/foo/')
        request.pages = RequestPageManager(request)
        processed_response = middleware.process_response(request, response)

        self.assertEqual(processed_response.status_code, 200)
        self.assertEqual(processed_response.template_name, (
            'testing_app/middlewaretestpage.html',
            'testing_app/base.html',
            'base.html'
        ))

        request = self.factory.get('/')
        request_foo = self.factory.get('/foo/')
        request.pages = RequestPageManager(request_foo)
        processed_response = middleware.process_response(request, response)

        self.assertEqual(processed_response['Location'], '/foo/')
        self.assertEqual(processed_response.status_code, 301)
        self.assertEqual(processed_response.content, b'')

        request = self.factory.get('/foobar/')
        request.pages = RequestPageManager(request)
        processed_response = middleware.process_response(request, response)
        self.assertEqual(processed_response.status_code, 404)

        with search.update_index():
            content_type = ContentType.objects.get_for_model(MiddlewareURLsTestPage)

            page = Page.objects.create(
                title="Foo",
                slug='urls',
                parent=self.homepage,
                content_type=content_type,
            )

            MiddlewareURLsTestPage.objects.create(
                page=page,
            )

        request = self.factory.get('/urls/')
        request.pages = RequestPageManager(request)
        processed_response = middleware.process_response(request, HttpResponseNotFound())
        self.assertEqual(processed_response.status_code, 200)
        self.assertEqual(processed_response.content, b'Hello!')
        with search.update_index():
            content_type = ContentType.objects.get_for_model(MiddlewareURLsTestPage)

            page = Page.objects.create(
                title="Foo",
                slug='raise404',
                parent=self.homepage,
                content_type=content_type,
            )

            MiddlewareURLsTestPage.objects.create(
                page=page,
            )

        request = self.factory.get('/raise404/')
        request.pages = RequestPageManager(request)
        processed_response = middleware.process_response(request, HttpResponseNotFound())
        self.assertEqual(processed_response.status_code, 404)

        with self.settings(DEBUG=True):
            request = self.factory.get('/raise404/')
            request.pages = RequestPageManager(request)
            processed_response = middleware.process_response(request, HttpResponseNotFound())
            self.assertEqual(processed_response.status_code, 404)

        request = self.factory.get('/auth/')
        request.user = MockUser(is_authenticated=False)
        request.pages = RequestPageManager(request)
        processed_response = middleware.process_response(request, response)
        self.assertEqual(processed_response['Location'], '/accounts/login/?next=/auth/')
        self.assertEqual(processed_response.status_code, 302)

        request = self.factory.get('/auth/')
        request.user = MockUser(is_authenticated=True)
        request.pages = RequestPageManager(request)
        processed_response = middleware.process_response(request, response)
        self.assertEqual(processed_response.status_code, 200)

        request = self.factory.get('/media/')
        request.pages = RequestPageManager(request)
        processed_response = middleware.process_response(request, response)
        self.assertEqual(processed_response, response)


@pytest.mark.django_db
def test_middleware_query_count(client, django_assert_num_queries):
    """
    Regression test to ensure that any middleware changes do not result in
    extra queries.
    """
    class Pages:
        pass

    pages = Pages()
    _generate_pages(pages)

    with django_assert_num_queries(4):
        response = client.get(pages.homepage.get_absolute_url())
    assert response.status_code == 200

    with django_assert_num_queries(4):
        response = client.get(pages.page_1.get_absolute_url())
    assert response.status_code == 200

    with django_assert_num_queries(4):
        response = client.get(pages.page_2.get_absolute_url())
    assert response.status_code == 200