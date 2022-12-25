import pytest

from uncms.forms import HtmlWidget
from uncms.models.fields import HtmlField, LinkResolutionError, resolve_link


def test_resolve_link():
    assert resolve_link('http://www.example.com/foo/') == 'http://www.example.com/foo/'
    assert resolve_link('www.example.com/foo/') == 'http://www.example.com/foo/'
    assert resolve_link('www.example.com') == 'http://www.example.com/'
    assert resolve_link('/foo/') == '/foo/'
    with pytest.raises(LinkResolutionError):
        resolve_link('foo/')


def test_html_field():
    field = HtmlField()
    assert isinstance(field.formfield().widget, HtmlWidget)
