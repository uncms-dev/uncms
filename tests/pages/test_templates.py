import pkg_resources
import pytest
from django.template.loader import render_to_string
from django.test import RequestFactory

from uncms.pages.middleware import RequestPageManager
from uncms.testhelpers.factories.media import MinimalGIFFileFactory
from uncms.testhelpers.factories.pages import PageFactory


@pytest.mark.parametrize(
    "django_template, jinja2_template",
    [
        (
            "pages/templates/pages/breadcrumbs.html",
            "pages/jinja2/pages/breadcrumbs.jinja2",
        )
    ],
)
def test_django_and_jinja_templates_are_identical(django_template, jinja2_template):
    """
    To reduce the maintenance burden of having both Jinja2 and Django
    templates, we should make sure that they are byte-for-byte identical.
    We have to go to minor extra efforts elsewhere to ensure that they *can*
    be (e.g. we track indexes in Python, rather than using "loop.index" or
    "forloop.counter" in the templates). This is worthwhile.
    """
    jinja2_path = pkg_resources.resource_filename("uncms", jinja2_template)
    django_path = pkg_resources.resource_filename("uncms", django_template)

    with open(jinja2_path, encoding="utf-8") as fd:
        jinja2_template_code = fd.read()

    with open(django_path, encoding="utf-8") as fd:
        django_template_code = fd.read()

    assert jinja2_template_code == django_template_code


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
