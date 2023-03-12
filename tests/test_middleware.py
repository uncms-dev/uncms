import pytest
from django.contrib.auth.models import AnonymousUser
from django.template.response import SimpleTemplateResponse
from django.test import RequestFactory
from django.test.utils import override_settings

from uncms.middleware import PublicationMiddleware
from uncms.testhelpers.factories import UserFactory
from uncms.testhelpers.factories.pages import PageFactory


def test_publicationmiddleware_process_request():
    request = RequestFactory().get('/?preview=a')
    request.user = AnonymousUser()
    publication_middleware = PublicationMiddleware(lambda: None)
    publication_middleware.process_request(request)


def test_publicationmiddleware_process_response():
    # pylint:disable=duplicate-code
    class Context(dict):
        pass

    request = RequestFactory().get('/?preview=a')
    request.user = AnonymousUser()

    context = Context()
    context['page_obj'] = Context()
    context['page_obj'].has_other_pages = lambda: False

    response = SimpleTemplateResponse('pagination/pagination.html', context)
    publication_middleware = PublicationMiddleware(lambda: None)

    response = publication_middleware.process_response(request, response)

    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(
    MIDDLEWARE=[
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'uncms.middleware.PublicationMiddleware',
        'uncms.pages.middleware.PageMiddleware',
    ],
)
def test_publicationmiddleware_preview(client):
    page_obj = PageFactory(is_online=False)
    superuser = UserFactory(superuser=True)

    # Ensure getting the page fails.
    response = client.get(page_obj.get_absolute_url())
    assert response.status_code == 404

    # Ensure preview mode (without a valid token) fails for
    # non-authenticated users.
    response = client.get(page_obj.get_absolute_url() + '?preview=1')
    assert response.status_code == 404

    # Ensure getting its preview URL works.
    response = client.get(page_obj.get_preview_url())
    assert response.status_code == 200

    #
    # Logged-in tests
    #
    client.force_login(superuser)

    # Ensure that preview=1 works for superusers.
    response = client.get(page_obj.get_absolute_url() + '?preview=1')
    assert response.status_code == 200

    # Ensure getting its preview URL works.
    response = client.get(page_obj.get_preview_url())
    assert response.status_code == 200
