import pytest
from django.contrib.contenttypes.models import ContentType

from tests.testing_app.models import HTMLModel
from uncms.templatetags.html import html


@pytest.mark.django_db
def test_html():
    assert html('') == ''
    assert html(None) == ''
    assert html('Hello') == 'Hello'
    assert html('<span>Hello</span>') == '<span>Hello</span>'

    obj = HTMLModel.objects.create()
    assert html('<a href="/r/{}-{}/">Hello</a>'.format(
        ContentType.objects.get_for_model(HTMLModel).pk,
        obj.pk
    )) == '<a href="/foo/" title="Foo">Hello</a>'
