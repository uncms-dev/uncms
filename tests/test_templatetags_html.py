import pytest

from uncms.templatetags.uncms_html import html


@pytest.mark.django_db
def test_html():
    assert html("") == ""
    assert html(None) == ""
    assert html("Hello") == "Hello"
    assert html("<span>Hello</span>") == "<span>Hello</span>"
