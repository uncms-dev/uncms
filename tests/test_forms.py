import json

from django.utils.html import conditional_escape

from uncms.conf import defaults
from uncms.forms import HtmlWidget


def test_htmlwidget_init():
    widget = HtmlWidget()
    assert isinstance(widget, HtmlWidget)


def test_htmlwidget_render():
    widget = HtmlWidget()
    rendered = widget.render('foo', 'bar')
    assert rendered.strip() == (
        '<textarea name="foo" cols="40" rows="30" class="wysiwyg" data-wysiwyg-upload-url="/admin/media/file/upload-api/" data-wysiwyg-image-list-url="/admin/media/file/image-list-api/" data-wysiwyg-settings="{}">\nbar</textarea>'.format(
            conditional_escape(json.dumps(defaults.WYSIWYG_OPTIONS))
        )
    )

    rendered = widget.render('foo', 'bar', attrs={'id': 'foo'})

    assert rendered.strip() == (
        '<textarea name="foo" cols="40" rows="30" id="foo" class="wysiwyg" data-wysiwyg-upload-url="/admin/media/file/upload-api/" data-wysiwyg-image-list-url="/admin/media/file/image-list-api/" data-wysiwyg-settings="{}">\nbar</textarea>'.format(
            conditional_escape(json.dumps(defaults.WYSIWYG_OPTIONS))
        )
    )
