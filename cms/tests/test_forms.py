import json

from django.test import TestCase
from django.utils.html import conditional_escape


from cms.conf import defaults
from ..forms import HtmlWidget


class TestForms(TestCase):

    def test_htmlwidget_init(self):
        widget = HtmlWidget()
        self.assertIsInstance(widget, HtmlWidget)

    def test_htmlwidget_get_media(self):
        widget = HtmlWidget()

        media = widget.get_media()

        self.assertDictEqual(media.__dict__, {
            '_css_lists': [{}],
            '_js_lists': [[
                '/static/cms/js/tinymce/tinymce.min.js',
                '/static/cms/js/jquery.cms.wysiwyg.js',
            ]],
        })

    def test_htmlwidget_render(self):
        # Sorry for the long strings in this one..
        widget = HtmlWidget()
        rendered = widget.render('foo', 'bar')
        self.assertInHTML(
            rendered,
            '<textarea name="foo" rows="10" cols="40" data-wysiwyg-settings="{}" class="wysiwyg">\nbar</textarea>'.format(
                conditional_escape(json.dumps(defaults.WYSIWYG_OPTIONS))
            ),
        )

        rendered = widget.render('foo', 'bar', attrs={'id': 'foo'})

        self.assertInHTML(
            '<textarea name="foo" class="wysiwyg" rows="10" cols="40" data-wysiwyg-settings="{}" id="foo">\nbar</textarea>'.format(
                conditional_escape(json.dumps(defaults.WYSIWYG_OPTIONS))
            ),
            rendered,
        )
