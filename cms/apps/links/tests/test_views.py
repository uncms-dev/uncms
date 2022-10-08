import pytest
from django.contrib.contenttypes.models import ContentType
from django.test.utils import override_settings
from watson.search import update_index

from cms.apps.links.models import Link
from cms.apps.pages.models import Page
from cms.tests.helpers import REQUIRED_PAGE_MIDDLEWARE


@pytest.mark.django_db
@pytest.mark.parametrize('permanent_redirect', [True, False])
@override_settings(MIDDLEWARE=REQUIRED_PAGE_MIDDLEWARE)
def test_link_page_redirect(permanent_redirect, client):
    with update_index():
        page = Page.objects.create(
            title='Homepage',
            content_type=ContentType.objects.get_for_model(Link),
        )

        Link.objects.create(
            page=page,
            link_url='http://www.example.com/',
            permanent_redirect=permanent_redirect,
        )

    response = client.get(page.get_absolute_url())
    assert (response.status_code == 301) is permanent_redirect
    assert (response.status_code == 302) is not permanent_redirect
    assert response['Location'] == 'http://www.example.com/'
