import pytest

from tests.pages.factories import PageFactory
from uncms.links.models import Link


@pytest.mark.django_db
def test_link_str():
    link = PageFactory(
        title='Link test',
        content=Link(link_url='http://www.example.com/'),
    )
    assert str(link.content) == 'Link test'
