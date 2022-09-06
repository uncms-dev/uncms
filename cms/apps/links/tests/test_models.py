import pytest
from django.contrib.contenttypes.models import ContentType
from watson.search import update_index

from cms.apps.links.models import Link
from cms.apps.pages.models import Page


@pytest.mark.django_db
def test_link_str():
    with update_index():
        page = Page.objects.create(
            title='Homepage',
            content_type=ContentType.objects.get_for_model(Link),
        )

        link = Link.objects.create(
            page=page,
            link_url='http://www.example.com/',
        )

    assert str(link) == 'Homepage'
