from dataclasses import dataclass

import pytest
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, HttpResponseNotFound
from django.test import RequestFactory, TestCase
from watson import search

from tests.pages.factories import PageFactory
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


@pytest.mark.django_db
def test_requestpagemanager_is_homepage():
    rf = RequestFactory()
    page_manager = RequestPageManager(rf.get('/'))
    assert page_manager.homepage is None

    homepage = PageFactory()
    page_manager = RequestPageManager(rf.get('/'))
    assert page_manager.is_homepage is True

    other_page = PageFactory(parent=homepage)
    page_manager = RequestPageManager(rf.get(other_page.get_absolute_url()))
    assert page_manager.is_homepage is False


@pytest.mark.django_db
def test_requestpagemanager_breadcrumbs():
    rf = RequestFactory()
    request = rf.get('/')
    page_manager = RequestPageManager(request)
    assert page_manager.breadcrumbs == []  # pylint:disable=use-implicit-booleaness-not-comparison

    homepage = PageFactory()
    subpage = PageFactory(parent=homepage)
    subsubpage = PageFactory(parent=subpage)

    request = rf.get('/')
    page_manager = RequestPageManager(request)
    assert page_manager.breadcrumbs == [homepage]

    request = rf.get(subpage.get_absolute_url())
    page_manager = RequestPageManager(request)
    assert page_manager.breadcrumbs == [homepage, subpage]

    request = rf.get(subsubpage.get_absolute_url())
    page_manager = RequestPageManager(request)
    assert page_manager.breadcrumbs == [homepage, subpage, subsubpage]


@pytest.mark.django_db
def test_requestpagemanager_section():
    rf = RequestFactory()

    page_manager = RequestPageManager(rf.get('/'))
    assert page_manager.section is None

    homepage = PageFactory()
    subpage = PageFactory(parent=homepage)
    subsubpage = PageFactory(parent=subpage)

    request = rf.get('/')
    page_manager = RequestPageManager(request)
    assert page_manager.section is None

    for page in [subpage, subsubpage]:
        request = rf.get(page.get_absolute_url())
        page_manager = RequestPageManager(request)
        assert page_manager.section == subpage


@pytest.mark.django_db
def test_requestpagemanager_subsection():
    rf = RequestFactory()
    page_manager = RequestPageManager(rf.get('/'))
    assert page_manager.section is None

    homepage = PageFactory()
    subpage = PageFactory(parent=homepage)
    subsubpage = PageFactory(parent=subpage)
    subsubsubpage = PageFactory(parent=subsubpage)

    request = rf.get('/')
    page_manager = RequestPageManager(request)
    assert page_manager.subsection is None

    request = rf.get(subpage.get_absolute_url())
    page_manager = RequestPageManager(request)
    assert page_manager.subsection is None

    request = rf.get(subsubpage.get_absolute_url())
    page_manager = RequestPageManager(request)
    assert page_manager.subsection == subsubpage

    request = rf.get(subsubsubpage.get_absolute_url())
    page_manager = RequestPageManager(request)
    assert page_manager.subsection == subsubpage


@pytest.mark.django_db
def test_requestpagemanager_current():
    rf = RequestFactory()
    page_manager = RequestPageManager(rf.get('/'))
    assert page_manager.section is None

    homepage = PageFactory()
    subpage = PageFactory(parent=homepage)
    subsubpage = PageFactory(parent=subpage)

    for page in homepage, subpage, subsubpage:
        request = rf.get(page.get_absolute_url())
        page_manager = RequestPageManager(request)
        assert page_manager.current == page


@pytest.mark.django_db
def test_requestpagemanager_is_exact():
    rf = RequestFactory()

    homepage = PageFactory()
    subpage = PageFactory(parent=homepage)
    subsubpage = PageFactory(parent=subpage)

    page_manager = RequestPageManager(rf.get('/'))
    page_manager.path = ''
    page_manager.path_info = ''
    assert page_manager.is_exact is False

    request = rf.get(subsubpage.get_absolute_url())
    page_manager = RequestPageManager(request)
    assert page_manager.is_exact is True


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
    PageFactory.create_tree(2, 2)

    homepage = Page.objects.get_homepage()

    with django_assert_num_queries(4):
        response = client.get(homepage.get_absolute_url())
    assert response.status_code == 200

    top_level_page = homepage.children[0]
    with django_assert_num_queries(4):
        response = client.get(top_level_page.get_absolute_url())
    assert response.status_code == 200

    subpage = top_level_page.children[0]
    with django_assert_num_queries(4):
        response = client.get(subpage.get_absolute_url())
    assert response.status_code == 200
