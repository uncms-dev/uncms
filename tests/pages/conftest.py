from dataclasses import dataclass

import pytest


@pytest.fixture
def simple_page_tree(db):
    # pylint:disable=import-outside-toplevel
    from django.contrib.contenttypes.models import ContentType
    from watson import search

    from uncms.pages.models import Page
    from uncms.testhelpers.models import EmptyTestPage

    @dataclass
    class SimplePageTree:
        homepage: Page
        section: Page
        subsection: Page
        subsubsection: Page

    with search.update_index():
        content_type = ContentType.objects.get_for_model(EmptyTestPage)

        homepage = Page.objects.create(
            title="Homepage",
            slug="homepage",
            content_type=content_type,
        )

        EmptyTestPage.objects.create(
            page=homepage,
        )

        section = Page.objects.create(
            parent=homepage,
            title="Section",
            slug="section",
            content_type=content_type,
            hide_from_anonymous=True,
        )

        EmptyTestPage.objects.create(
            page=section,
        )

        subsection = Page.objects.create(
            parent=section,
            title="Subsection",
            slug="subsection",
            content_type=content_type,
        )

        EmptyTestPage.objects.create(
            page=subsection,
        )

        subsubsection = Page.objects.create(
            parent=subsection,
            title="Subsubsection",
            slug="subsubsection",
            content_type=content_type,
        )

        EmptyTestPage.objects.create(
            page=subsubsection,
        )

    return SimplePageTree(
        homepage=homepage,
        section=section,
        subsection=subsection,
        subsubsection=subsubsection,
    )
