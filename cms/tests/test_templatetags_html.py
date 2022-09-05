from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from cms.templatetags.html import html, truncate_paragraphs
from cms.apps.testing_models.models import HTMLModel


class HTMLTest(TestCase):

    def test_html(self):
        self.assertEqual(html(''), '')
        self.assertEqual(html(None), 'None')
        self.assertEqual(html('Hello'), 'Hello')
        self.assertEqual(html('<span>Hello</span>'), '<span>Hello</span>')

        obj = HTMLModel.objects.create()
        self.assertEqual(html('<a href="/r/{}-{}/">Hello</a>'.format(
            ContentType.objects.get_for_model(HTMLModel).pk,
            obj.pk
        )), '<a href="/foo/" title="Foo">Hello</a>')

    def test_truncate_paragraphs(self):
        self.assertEqual(truncate_paragraphs('<p>Foo', 1), '<p>Foo')
        self.assertEqual(truncate_paragraphs('<p>Foo</p><p>Bar</p>', 0), '')
        self.assertEqual(truncate_paragraphs('<p>Foo</p><p>Bar</p>', 1), '<p>Foo</p>')
        self.assertEqual(truncate_paragraphs('<p>Foo</p><p>Bar</p>', 2), '<p>Foo</p><p>Bar</p>')
