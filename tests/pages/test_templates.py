import pytest
from django.template.loader import render_to_string
from django.test import RequestFactory

from tests.media.factories import MinimalGIFFileFactory
from tests.pages.factories import PageFactory
from uncms.pages.middleware import RequestPageManager


@pytest.mark.django_db
def test_head_meta_templates_are_identical(use_jinja2):
    """
    Ensure that pages/head_meta.html and pages/head_meta.jinja2 are identical
    (minus any trailing newlines) to ensure parity.
    """
    page = PageFactory()
    request = RequestFactory().get('/')
    request.pages = RequestPageManager(request)

    def assert_templates_equal():
        django_rendered = render_to_string('pages/head_meta.html', {'request': request, 'pages': request.pages})
        jinja2_rendered = render_to_string('pages/head_meta.jinja2', {'request': request, 'pages': request.pages})
        assert jinja2_rendered.strip() == django_rendered.strip()

    assert_templates_equal()

    for field in [
        'twitter_title',
        'twitter_description',
        'og_description',
        'og_title',
        'browser_title',
    ]:
        setattr(page, field, 'Testing > &')
    page.og_image = MinimalGIFFileFactory()
    page.twitter_image = MinimalGIFFileFactory()
    page.save()

    request = RequestFactory().get('/')
    request.pages = RequestPageManager(request)

    assert_templates_equal()
