from dataclasses import dataclass
from pathlib import Path

import pytest


@pytest.fixture
def simple_page_tree(db):
    # pylint:disable=import-outside-toplevel
    from uncms.pages.models import Page
    from uncms.testhelpers.factories.pages import PageFactory

    @dataclass
    class SimplePageTree:
        homepage: Page
        section: Page
        subsection: Page
        subsubsection: Page

    homepage = PageFactory(title="Homepage", slug="homepage")
    section = PageFactory(
        parent=homepage,
        title="Section",
        slug="section",
        hide_from_anonymous=True,
    )
    subsection = PageFactory(parent=section, title="Subsection", slug="subsection")
    subsubsection = PageFactory(
        parent=subsection, title="Subsubsection", slug="subsubsection"
    )

    return SimplePageTree(
        homepage=homepage,
        section=section,
        subsection=subsection,
        subsubsection=subsubsection,
    )


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """
    Returns the root directory of the Git repository.
    """
    return Path(__file__).parent.parent
