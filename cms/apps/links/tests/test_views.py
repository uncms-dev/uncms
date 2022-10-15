import pytest

from cms.apps.links.models import Link
from cms.apps.pages.tests.factories import PageFactory


@pytest.mark.django_db
@pytest.mark.parametrize('permanent_redirect', [True, False])
def test_link_page_redirect(permanent_redirect, client):
    page = PageFactory.create(
        content=Link(
            link_url='http://www.example.com/',
            permanent_redirect=permanent_redirect,
        )
    )
    response = client.get(page.get_absolute_url())
    assert (response.status_code == 301) is permanent_redirect
    assert (response.status_code == 302) is not permanent_redirect
    assert response['Location'] == 'http://www.example.com/'
