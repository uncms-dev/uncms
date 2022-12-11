import json

from django.utils.html import conditional_escape

from uncms.conf import defaults
from uncms.forms import HtmlWidget


def test_htmlwidget_init():
    widget = HtmlWidget()
    assert isinstance(widget, HtmlWidget)


def test_htmlwidget_get_media():
    widget = HtmlWidget()

    media = widget.get_media()

    assert media.__dict__ == {
        '_css_lists': [{'screen': ['/static/cms/css/tinymce-tweak.css']}],
        '_js_lists': [[
            '/static/cms/js/tinymce/tinymce.min.js',
            '/static/cms/js/wysiwyg.js',
        ]],
    }


def test_htmlwidget_render():
    widget = HtmlWidget()
    rendered = widget.render('foo', 'bar')
    assert rendered.strip() == (
        '<textarea name="foo" cols="40" rows="10" class="wysiwyg" data-wysiwyg-settings="{}">\nbar</textarea>'.format(
            conditional_escape(json.dumps(defaults.WYSIWYG_OPTIONS))
        )
    )

    rendered = widget.render('foo', 'bar', attrs={'id': 'foo'})

    assert rendered.strip() == (
        '<textarea name="foo" cols="40" rows="10" id="foo" class="wysiwyg" data-wysiwyg-settings="{}">\nbar</textarea>'.format(
            conditional_escape(json.dumps(defaults.WYSIWYG_OPTIONS))
        )
    )
