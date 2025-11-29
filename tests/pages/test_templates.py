import pytest
from django.template.loader import render_to_string
from django.test import RequestFactory

from uncms.pages.middleware import RequestPageManager
from uncms.testhelpers.factories.media import MinimalGIFFileFactory
from uncms.testhelpers.factories.pages import PageFactory


@pytest.mark.django_db
def test_head_meta_templates_render_identically(use_jinja2):
    """
    Ensure that pages/head_meta.html and pages/head_meta.jinja2 are identical
    (minus any trailing newlines) to ensure parity.
    """
    page = PageFactory()
    request = RequestFactory().get("/")
    request.pages = RequestPageManager(request)

    def assert_templates_equal():
        django_rendered = render_to_string(
            "pages/head_meta.html", {"request": request, "pages": request.pages}
        )
        jinja2_rendered = render_to_string(
            "pages/head_meta.jinja2", {"request": request, "pages": request.pages}
        )
        assert jinja2_rendered.strip() == django_rendered.strip()

    assert_templates_equal()

    for field in [
        "og_description",
        "og_title",
        "browser_title",
    ]:
        setattr(page, field, "Testing > &")
    page.og_image = MinimalGIFFileFactory()
    page.save()

    request = RequestFactory().get("/")
    request.pages = RequestPageManager(request)

    assert_templates_equal()
