from urllib.parse import urljoin

import pytest
from django.http import HttpResponse, HttpResponseNotFound
from django.test import RequestFactory, override_settings
from django.urls import reverse

from tests.mocks import MockRequestUser, request_with_pages
from tests.testing_app.models import MiddlewareURLsTestPage
from uncms.pages.middleware import PageMiddleware, RequestPageManager
from uncms.pages.models import Page
from uncms.pages.templatetags.uncms_pages import render_navigation
from uncms.testhelpers.factories import UserFactory
from uncms.testhelpers.factories.media import EmptyFileFactory
from uncms.testhelpers.factories.pages import PageFactory


@pytest.mark.django_db
def test_requestpagemanager_is_homepage():
    rf = RequestFactory()
    page_manager = RequestPageManager(rf.get("/"))
    assert page_manager.homepage is None

    homepage = PageFactory()
    page_manager = RequestPageManager(rf.get("/"))
    assert page_manager.is_homepage is True

    other_page = PageFactory(parent=homepage)
    page_manager = RequestPageManager(rf.get(other_page.get_absolute_url()))
    assert page_manager.is_homepage is False


@pytest.mark.django_db
def test_requestpagemanager_breadcrumbs():
    rf = RequestFactory()
    request = rf.get("/")
    page_manager = RequestPageManager(request)
    # pylint:disable-next=use-implicit-booleaness-not-comparison
    assert page_manager.breadcrumbs == []

    homepage = PageFactory()
    subpage = PageFactory(parent=homepage)
    subsubpage = PageFactory(parent=subpage)

    request = rf.get("/")
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

    page_manager = RequestPageManager(rf.get("/"))
    assert page_manager.section is None

    homepage = PageFactory()
    subpage = PageFactory(parent=homepage)
    subsubpage = PageFactory(parent=subpage)

    request = rf.get("/")
    page_manager = RequestPageManager(request)
    assert page_manager.section is None

    for page in [subpage, subsubpage]:
        request = rf.get(page.get_absolute_url())
        page_manager = RequestPageManager(request)
        assert page_manager.section == subpage


@pytest.mark.django_db
def test_requestpagemanager_subsection():
    rf = RequestFactory()
    page_manager = RequestPageManager(rf.get("/"))
    assert page_manager.section is None

    homepage = PageFactory()
    subpage = PageFactory(parent=homepage)
    subsubpage = PageFactory(parent=subpage)
    subsubsubpage = PageFactory(parent=subsubpage)

    request = rf.get("/")
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
    page_manager = RequestPageManager(rf.get("/"))
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

    page_manager = RequestPageManager(rf.get("/"))
    page_manager.path = ""
    page_manager.path_info = ""
    assert page_manager.is_exact is False

    request = rf.get(subsubpage.get_absolute_url())
    page_manager = RequestPageManager(request)
    assert page_manager.is_exact is True


@pytest.mark.django_db
def test_requestpagemanager_get_page():
    request = RequestFactory().get("/")
    # No pages should return None, rather than raising an exception.
    assert RequestPageManager(request).get_page(5) is None

    homepage = PageFactory.create_tree(5, 5)
    for find in [homepage, homepage.id]:
        assert RequestPageManager(request).get_page(find) == homepage

    subpage = PageFactory(parent=homepage)
    for find in [subpage, subpage.id]:
        assert RequestPageManager(request).get_page(find) == subpage

    subsubpage = PageFactory(parent=homepage)
    for find in [subsubpage, subsubpage.id]:
        assert RequestPageManager(request).get_page(find) == subsubpage

    assert RequestPageManager(request).get_page(-6) is None


@pytest.mark.django_db
def test_requestpagemanager_get_page_is_efficient(django_assert_num_queries):
    homepage = PageFactory.create_tree(5, 5)
    subsubpage = PageFactory(parent=PageFactory(parent=homepage))
    request = request_with_pages()

    # Render navigation, as we probably always will on any page on the site.
    render_navigation({"request": request}, pages=request.pages.homepage.navigation)

    with django_assert_num_queries(0):
        assert request.pages.get_page(subsubpage) == subsubpage
        # Make sure referencing the parent doesn't create a query, otherwise
        # this is pointless :)
        assert request.pages.get_page(subsubpage).parent.title.startswith("Page")
        assert request.pages.get_page(subsubpage).parent.parent.title.startswith("Page")


@pytest.mark.django_db
def test_pagemiddleware_process_response():  # pylint:disable=too-many-statements
    rf = RequestFactory()
    request = rf.get("/")

    middleware = PageMiddleware(lambda: None)

    # Ensure that non-404s are passed through.
    response = HttpResponse()
    assert middleware.process_response(request, response) is response

    response = HttpResponseNotFound()
    page_request = rf.get("")
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
            "testhelpers/emptytestpage.html",
            "testhelpers/base.html",
            "base.html",
        )

    request = rf.get("/")
    request_foo = rf.get(subpage.get_absolute_url())
    request.pages = RequestPageManager(request_foo)
    processed_response = middleware.process_response(request, response)

    assert processed_response["Location"] == subpage.get_absolute_url()
    assert processed_response.status_code == 301
    assert processed_response.content == b""

    request = rf.get("/foobar/")
    request.pages = RequestPageManager(request)
    processed_response = middleware.process_response(request, response)
    assert processed_response.status_code == 404

    middleware_page = PageFactory(
        parent=homepage, slug="urls", content=MiddlewareURLsTestPage()
    )
    request = rf.get("/urls/")
    request.pages = RequestPageManager(request)
    processed_response = middleware.process_response(request, HttpResponseNotFound())
    assert processed_response.status_code == 200
    assert processed_response.content == b"Hello!"

    request = rf.get(middleware_page.reverse("detail", kwargs={"slug": "example"}))
    request.pages = RequestPageManager(request)
    processed_response = middleware.process_response(request, HttpResponseNotFound())
    assert processed_response.status_code == 200
    assert processed_response.content == b"detail view: example"

    request = rf.get(middleware_page.reverse("not_found"))
    request.pages = RequestPageManager(request)
    processed_response = middleware.process_response(request, HttpResponseNotFound())
    assert processed_response.status_code == 404

    with override_settings(DEBUG=True):
        processed_response = middleware.process_response(
            request, HttpResponseNotFound()
        )
    assert processed_response.status_code == 404

    # Test the branch that handles a broken view (doesn't return an
    # HttpResponse)
    request = rf.get(middleware_page.reverse("broken_view"))
    request.pages = RequestPageManager(request)
    with override_settings(DEBUG=True):
        processed_response = middleware.process_response(
            request, HttpResponseNotFound()
        )
    assert processed_response.status_code == 500

    # Test a page that requires authentication with a user that is not
    # authenticated.
    PageFactory(requires_authentication=True, slug="auth")
    request = rf.get("/auth/")
    request.user = MockRequestUser(is_authenticated=False)
    request.pages = RequestPageManager(request)
    processed_response = middleware.process_response(request, response)
    assert processed_response.status_code == 302
    assert processed_response["Location"] == "/accounts/login/?next=/auth/"

    # Test a page that requires authentication with a user that *is*
    # authenticated.
    request = rf.get("/auth/")
    request.user = MockRequestUser(is_authenticated=True)
    request.pages = RequestPageManager(request)
    processed_response = middleware.process_response(request, response)
    assert processed_response.status_code == 200

    # Ensure that requests to /media/ are passed through.
    for path in ["/media/", "/static/"]:
        response = HttpResponseNotFound()
        request = rf.get(path)
        request.pages = RequestPageManager(request)
        processed_response = middleware.process_response(request, response)
        assert processed_response is response


@pytest.mark.django_db
def test_pagemiddleware_with_client(client):
    """
    Further to the above tests, we don't actually care about what
    process_response does or returns. That is an implementation detail; if
    Django's API changes underneath us we can pass tests while being totally
    broken in practice.

    What we actually care about is whether the middleware serves up pages.
    So let's test it with the test client.
    """

    # See what happens before we create any pages.
    response = client.get("/")
    assert response.status_code == 404

    homepage = PageFactory()

    # Test that non-404 pages are passed through. We have /admin/ in our
    # urlconf, so let's hit that.
    response = client.get(reverse("admin:index"))
    assert response.status_code == 302

    response = client.get("/")
    assert response.status_code == 200
    assert response.template_name == (
        "testhelpers/emptytestpage.html",
        "testhelpers/base.html",
        "base.html",
    )

    # Test a page with a urlconf.
    middleware_page = PageFactory(parent=homepage, content=MiddlewareURLsTestPage())
    response = client.get(middleware_page.get_absolute_url())
    assert response.status_code == 200
    assert response.content == b"Hello!"

    response = client.get(middleware_page.reverse("detail", kwargs={"slug": "hooray"}))
    assert response.status_code == 200
    assert response.content == b"detail view: hooray"

    # Test a 404 with a URL that doesn't exist in its urlconf.
    response = client.get(urljoin(middleware_page.get_absolute_url(), "hurf/hurrr/"))
    assert response.status_code == 404

    # Test a view on a page that raises a 404.
    for debug in [True, False]:
        with override_settings(DEBUG=debug):
            response = client.get(middleware_page.reverse("not_found"))
        assert response.status_code == 404

    # Test a view on a page that is broken and does not return an HttpResponse.
    response = client.get(middleware_page.reverse("broken_view"))
    assert response.status_code == 500

    # Test a page that requires authentication with a user which is not
    # authenticated.
    PageFactory(requires_authentication=True, slug="auth")
    response = client.get("/auth/")
    assert response.status_code == 302
    assert response["Location"] == "/accounts/login/?next=/auth/"

    # Test a page that requires authentication with a user that *is*
    # authenticated.
    client.force_login(UserFactory())
    response = client.get("/auth/")
    assert response.status_code == 200

    # Test the /media/ special case.
    file = EmptyFileFactory()
    response = client.get(file.get_absolute_url())
    assert response.status_code == 200
    assert bytes(response.streaming_content) == b""


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
