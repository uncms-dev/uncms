import pytest
from django.contrib.contenttypes.models import ContentType

from cms.apps.testing_models.models import HTMLModel
from cms.templatetags.html import html, truncate_paragraphs


@pytest.mark.django_db
def test_html():
    assert html('') == ''
    assert html(None) == 'None'
    assert html('Hello') == 'Hello'
    assert html('<span>Hello</span>') == '<span>Hello</span>'

    obj = HTMLModel.objects.create()
    assert html('<a href="/r/{}-{}/">Hello</a>'.format(
        ContentType.objects.get_for_model(HTMLModel).pk,
        obj.pk
    )) == '<a href="/foo/" title="Foo">Hello</a>'


def test_truncate_paragraphs():
    assert truncate_paragraphs('<p>Foo', 1) == '<p>Foo'
    assert truncate_paragraphs('<p>Foo</p><p>Bar</p>', 0) == ''
    assert truncate_paragraphs('<p>Foo</p><p>Bar</p>', 1) == '<p>Foo</p>'
    assert truncate_paragraphs('<p>Foo</p><p>Bar</p>', 2) == '<p>Foo</p><p>Bar</p>'
