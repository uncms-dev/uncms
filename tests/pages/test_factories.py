import pytest

from uncms.pages.models import Page
from uncms.testhelpers.factories.pages import PageFactory


@pytest.mark.django_db
def test_page_factory_is_sane():
    """
    What is this, a test for the tests?

    Well, PageFactory.create_tree is essential to some important performance
    tests. It would be good to know that it is working properly.
    """
    PageFactory.create_tree(3, 5, 4)
    homepage = Page.objects.get_homepage()

    assert len(homepage.children) == 3
    for page in homepage.children:
        assert len(page.children) == 5
        for subpage in page.children:
            assert len(subpage.children) == 4

            for subsubpage in subpage.children:
                assert len(subsubpage.children) == 0
