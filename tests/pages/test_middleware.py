import pytest
from django.http import HttpResponse, HttpResponseNotFound
from django.test import RequestFactory, override_settings

from tests.mocks import MockRequestUser
from tests.pages.factories import PageFactory
from tests.testing_app.models import MiddlewareURLsTestPage
from uncms.pages.middleware import PageMiddleware, RequestPageManager
from uncms.pages.models import Page


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


@pytest.mark.django_db
def test_pagemiddleware_process_response():  # pylint:disable=too-many-statements
    rf = RequestFactory()
    request = rf.get('/')

    middleware = PageMiddleware(lambda: None)

    # Ensure that non-404s are passed through.
    response = HttpResponse()
    assert middleware.process_response(request, response) is response

    response = HttpResponseNotFound()
    page_request = rf.get('')
    request.pages = RequestPageManager(page_request)
    assert middleware.process_response(request, response) is response

    homepage = PageFactory()
    subpage = PageFactory(parent=homepage)

    for page in [homepage, subpage]:
        request = rf.get(page.get_absolute_url())
        request.pages = RequestPageManager(request)
        processed_response = middleware.process_response(request, response)

        assert processed_response.status_code == 200
        assert processed_response.template_name == (
            'testing_app/emptytestpage.html',
            'testing_app/base.html',
            'base.html',
        )

    request = rf.get('/')
    request_foo = rf.get(subpage.get_absolute_url())
    request.pages = RequestPageManager(request_foo)
    processed_response = middleware.process_response(request, response)

    assert processed_response['Location'] == subpage.get_absolute_url()
    assert processed_response.status_code == 301
    assert processed_response.content == b''

    request = rf.get('/foobar/')
    request.pages = RequestPageManager(request)
    processed_response = middleware.process_response(request, response)
    assert processed_response.status_code == 404

    PageFactory(parent=homepage, slug='urls', content=MiddlewareURLsTestPage())
    request = rf.get('/urls/')
    request.pages = RequestPageManager(request)
    processed_response = middleware.process_response(request, HttpResponseNotFound())
    assert processed_response.status_code == 200
    assert processed_response.content == b'Hello!'

    middleware_page = PageFactory(parent=homepage, content=MiddlewareURLsTestPage())
    request = rf.get(middleware_page.reverse('not_found'))
    request.pages = RequestPageManager(request)
    processed_response = middleware.process_response(request, HttpResponseNotFound())
    assert processed_response.status_code == 404

    request = rf.get(middleware_page.reverse('not_found'))
    request.pages = RequestPageManager(request)
    with override_settings(DEBUG=True):
        processed_response = middleware.process_response(request, HttpResponseNotFound())
    assert processed_response.status_code == 404

    # Test the branch that handles a broken view (doesn't return an
    # HttpResponse)
    request = rf.get(middleware_page.reverse('broken_view'))
    request.pages = RequestPageManager(request)
    with override_settings(DEBUG=True):
        processed_response = middleware.process_response(request, HttpResponseNotFound())
    assert processed_response.status_code == 500

    # Test a page that requires authentication with a user that is not
    # authenticated.
    PageFactory(requires_authentication=True, slug='auth')
    request = rf.get('/auth/')
    request.user = MockRequestUser(is_authenticated=False)
    request.pages = RequestPageManager(request)
    processed_response = middleware.process_response(request, response)
    assert processed_response.status_code == 302
    assert processed_response['Location'] == '/accounts/login/?next=/auth/'

    # Test a page that requires authentication with a user that *is*
    # authenticated.
    request = rf.get('/auth/')
    request.user = MockRequestUser(is_authenticated=True)
    request.pages = RequestPageManager(request)
    processed_response = middleware.process_response(request, response)
    assert processed_response.status_code == 200

    # Ensure that requests to /media/ are passed through.
    response = HttpResponseNotFound()
    request = rf.get('/media/')
    request.pages = RequestPageManager(request)
    processed_response = middleware.process_response(request, response)
    assert processed_response is response


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
