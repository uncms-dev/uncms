import base64
import random
import sys
from unittest import mock

from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.timezone import now

from uncms.html import clean_all, clean_html, process_html
from uncms.media.models import File


class TestHTML(TestCase):
    def setUp(self):
        self.name = '{}-{}.gif'.format(
            now().strftime('%Y-%m-%d_%H-%M-%S'),
            random.randint(0, sys.maxsize)
        )

        base64_string = b'R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
        self.image = File.objects.create(
            title="Foo",
            file=SimpleUploadedFile(self.name, base64.b64decode(base64_string),
                                    content_type="image/gif")
        )

        self.image_copyright = File.objects.create(
            title="Foo c",
            file=SimpleUploadedFile(self.name, base64.b64decode(base64_string),
                                    content_type="image/gif"),
            copyright="Foo copyright"
        )

        self.image_attribution = File.objects.create(
            title="Foo a",
            file=SimpleUploadedFile(self.name, base64.b64decode(base64_string),
                                    content_type="image/gif"),
            attribution="Foo attribution"
        )

        # An invalid JPEG
        self.invalid_jpeg_name = '{}-{}.jpg'.format(
            now().strftime('%Y-%m-%d_%H-%M-%S'),
            random.randint(0, sys.maxsize)
        )

        self.invalid_jpeg = File.objects.create(
            title="Foo",
            file=SimpleUploadedFile(self.invalid_jpeg_name, b"data",
                                    content_type="image/jpeg")
        )

    def tearDown(self):
        self.image.file.delete(False)
        self.image.delete()

        self.image_copyright.file.delete(False)
        self.image_copyright.delete()

        self.image_attribution.file.delete(False)
        self.image_attribution.delete()

        self.invalid_jpeg.file.delete(False)
        self.invalid_jpeg.delete()

    def test_process(self):
        string = ''
        self.assertEqual(process_html(string), string)

        string = '<a href="/">Link</a>'
        self.assertEqual(process_html(string), string)

        string = '<img src="test.png">'
        self.assertEqual(process_html(string), string)

        string = '<img>'
        self.assertEqual(process_html(string), string)

        content_type = ContentType.objects.get_for_model(File).pk
        string = '<img src="/r/{}-{}/" width="10" height="10"/>'.format(
            content_type,
            self.image.pk
        )
        output = process_html(string)

        self.assertIn('src="/media/cache/', output)
        self.assertIn('height="10"', output)
        self.assertIn('width="10"', output)
        self.assertIn('title="Foo"', output)

        with mock.patch('uncms.html.get_thumbnail', side_effect=IOError):
            output = process_html(string)

        self.assertEqual(output,
                         '<img height="10" src="/media/uploads/files/' + self.name + '" title="Foo" width="10">')

        content_type = ContentType.objects.get_for_model(File).pk
        string = '<img src="/r/{}-{}/"/>'.format(
            content_type,
            self.image.pk
        )
        self.assertEqual(process_html(string),
                         '<img src="' + self.image.file.url + '" title="Foo">')

        string = '<img src="/r/{}-{}/"/>'.format(
            content_type,
            self.image_copyright.pk
        )
        self.assertEqual(process_html(string),
                         '<img src="' + self.image_copyright.file.url + '" title="&copy; Foo copyright. ">')

        string = '<img src="/r/{}-{}/"/>'.format(
            content_type,
            self.image_attribution.pk
        )
        self.assertEqual(process_html(string),
                         '<img src="' + self.image_attribution.file.url + '" title="Foo attribution">')


def example_processor(html):
    # sample processor for testing config overrides
    return html.replace('woof', 'meow')


def test_html_clean():
    html = '<script>alert("Hello!")><img loading="lazy" onload="alert(&quot;whoops&quot;)" title="example" class="test" src="/example.png"><p>woof</p>'

    for clean_func in clean_html, clean_all:
        assert clean_func(html) == '&lt;script&gt;alert("Hello!")&gt;<img loading="lazy" title="example" class="test" src="/example.png"><p>woof</p>'

    # check settings overrides work
    with override_settings(UNCMS={'HTML_CLEANERS': ['uncms.html.clean_html', 'tests.test_html.example_processor']}):
        assert clean_all(html) == '&lt;script&gt;alert("Hello!")&gt;<img loading="lazy" title="example" class="test" src="/example.png"><p>meow</p>'
