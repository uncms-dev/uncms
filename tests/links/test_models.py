import pytest

from uncms.links.models import Link
from uncms.testhelpers.factories.pages import PageFactory


@pytest.mark.django_db
def test_link_str():
    link = PageFactory(
        title="Link test",
        content=Link(link_url="http://www.example.com/"),
    )
    assert str(link.content) == "Link test"
