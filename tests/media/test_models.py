import base64
import random
import sys
from io import BytesIO

import pytest
from bs4 import BeautifulSoup
from django.contrib import admin
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TransactionTestCase
from django.test.utils import override_settings
from django.utils.functional import cached_property
from django.utils.timezone import now
from PIL import Image

from tests.media.factories import (
    EmptyFileFactory,
    MinimalGIFFileFactory,
    SamplePNGFileFactory,
    SampleWebPFileFactory,
)
from tests.testing_app.models import MediaTestModel
from uncms.media.models import File, FileRefField, Label


class TestFile(TransactionTestCase):

    def setUp(self):  # pylint:disable=duplicate-code
        # An invalid JPEG
        self.name_1 = '{}-{}.jpg'.format(
            now().strftime('%Y-%m-%d_%H-%M-%S'),
            random.randint(0, sys.maxsize)
        )

        self.obj_1 = File.objects.create(
            title="Foo",
            file=SimpleUploadedFile(self.name_1, b"data", content_type="image/jpeg")
        )

        # Plain text file
        self.name_2 = '{}-{}.txt'.format(
            now().strftime('%Y-%m-%d_%H-%M-%S'),
            random.randint(0, sys.maxsize)
        )

        self.obj_2 = File.objects.create(
            title="Foo",
            file=SimpleUploadedFile(self.name_2, b"data", content_type="text/plain")
        )

        # A valid GIF.
        self.name_3 = '{}-{}.gif'.format(
            now().strftime('%Y-%m-%d_%H-%M-%S'),
            random.randint(0, sys.maxsize)
        )

        base64_string = b'R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
        self.obj_3 = File.objects.create(
            title="Foo",
            file=SimpleUploadedFile(self.name_3, base64.b64decode(base64_string), content_type="image/gif")
        )

        self.obj_4 = File.objects.create(
            title="Foo",
            file="abc123",
        )

    def tearDown(self):
        self.obj_1.file.delete(False)
        self.obj_1.delete()

        self.obj_2.file.delete(False)
        self.obj_2.delete()

        self.obj_3.file.delete(False)
        self.obj_3.delete()

        self.obj_4.file.delete(False)
        self.obj_4.delete()

    def test_file_get_absolute_url(self):
        self.assertEqual(self.obj_1.get_absolute_url(), '/media/uploads/files/{}'.format(
            self.name_1
        ))

    def test_file_unicode(self):
        self.assertEqual(str(self.obj_1), 'Foo')
        self.assertEqual(self.obj_1.file.name, 'uploads/files/' + self.name_1)

    def test_file_is_image(self):
        self.assertTrue(self.obj_1.is_image())
        self.assertFalse(self.obj_2.is_image())

    def test_file_width(self):
        self.assertEqual(self.obj_1.width, 0)
        self.assertEqual(self.obj_2.width, 0)
        self.assertEqual(self.obj_3.width, 1)
        self.assertEqual(self.obj_4.width, 0)

    def test_file_height(self):
        self.assertEqual(self.obj_1.height, 0)
        self.assertEqual(self.obj_2.height, 0)
        self.assertEqual(self.obj_3.height, 1)
        self.assertEqual(self.obj_4.height, 0)

    def test_filereffield_formfield(self):
        obj = MediaTestModel.objects.create(
            file=self.obj_1
        )

        field = obj._meta.get_field('file')
        widget = field.formfield().widget

        self.assertIsInstance(widget, ForeignKeyRawIdWidget)
        self.assertEqual(widget.rel, field.remote_field)
        self.assertEqual(widget.admin_site, admin.site)
        self.assertIsNone(widget.db)

    def test_file_init(self):
        field = FileRefField(
            to=MediaTestModel,
        )

        self.assertEqual(field.remote_field.model, 'media.File')


@pytest.mark.django_db
def test_file_get_thumbnail(client):
    image = SamplePNGFileFactory()

    # tuple of (kwargs, expected height, expected width)
    tests = [
        # Is height being guessed correctly if it is auto?
        ({'width': 960}, 960, 540),
        # Is width being guessed correctly if it is auto?
        ({'height': 540}, 960, 540),
        # And if we've specified both?
        ({'width': 240, 'height': 240}, 240, 240),
        # And if numbers don't divide neatly into each other?
        ({'width': 1919}, 1919, 1079),
        ({'height': 1079}, 1918, 1079),
        # And if we're feeding it pretty much garbage inputs? WHAT THEN HUH
        ({'width': 2}, 2, 1),
        # why not test the other things while we're here?
        ({'width': 960, 'colorspace': 'gray', 'quality': 90}, 960, 540),
    ]
    for thumb_kwargs, width, height in tests:
        thumbnail = image.get_thumbnail(**thumb_kwargs)
        assert thumbnail.width == width
        assert thumbnail.height == height

        # But do they match up with what the image view will actually do?
        response = client.get(thumbnail.url)
        assert response.status_code == 302

        response = client.get(response['Location'])
        assert response.status_code == 200
        assert response['Content-Type'] == 'image/png'
        response_content = response.getvalue()
        pil_image = Image.open(BytesIO(response_content))
        # not gonna try and work out EXACTLY how Sorl decides how to round
        # dimensions - if there's less than 1px different call it close enough
        assert abs(pil_image.size[0] - thumbnail.width) <= 1
        assert abs(pil_image.size[1] - thumbnail.height) <= 1
        pil_image.close()


@pytest.mark.django_db
def test_file_get_thumbnail_on_garbage():
    # What happens when we feed get_thumbnail total nonsense? As get_thumbnail
    # can be called in-request, on user-facing sites, we don't want to crash
    # other than being called with no target height or width (which is a
    # programmer's error).

    # Test "your code is bad" branch
    image = SamplePNGFileFactory()
    with pytest.raises(ValueError) as excinfo:
        image.get_thumbnail()
    assert 'no dimensions provided' in str(excinfo.value)

    # Give it something that isn't an image
    garbage = EmptyFileFactory()
    thumbnail = garbage.get_thumbnail(width=2)
    assert thumbnail.width == 2
    assert thumbnail.height == 0

    # what happens on a 0x0 gif?
    garbage_gif = MinimalGIFFileFactory()
    thumbnail = garbage_gif.get_thumbnail(width=10)
    assert thumbnail.width == 10
    assert thumbnail.height == 0


@pytest.mark.django_db
def test_label_str():
    obj = Label.objects.create(name="Foo")
    assert str(obj) == "Foo"


#
# Below begin the multiformat rendering tests. This is a section divider!
#

class MultiFormatSoupParser:
    def __init__(self, html):
        self.soup = BeautifulSoup(html, 'html.parser')

    @cached_property
    def srcsets(self):
        formats = {}
        for source_tag in self.soup.find_all('source'):
            formats[source_tag['type']] = []
            for source in source_tag['srcset'].split(', '):
                source_parts = source.split(' ')
                assert len(source_parts) == 2
                # int has the side-effect of raising ValueError if it is not
                # an integer :)
                formats[source_tag['type']].append(
                    (source_parts[0], int(source_parts[1].rstrip('w'))),
                )
        return formats

    @cached_property
    def alt_text(self):
        return self.img_tag['alt']

    @cached_property
    def img_tag(self):
        return self.soup.find('img')

    @cached_property
    def loading_attribute(self):
        return self.img_tag.get('loading')

    @cached_property
    def sizes_attributes(self):
        return [
            element['sizes']
            for element in self.soup.find_all('source')
        ]

    @cached_property
    def style_attribute(self):
        return self.img_tag.get('style')

    def validate_srcsets(self):
        client = Client()

        for fmt, sources in self.srcsets.items():
            for url, width in sources:
                response = client.get(url)
                assert response.status_code == 302

                response = client.get(response['Location'])
                assert response.status_code == 200
                if fmt == 'image/webp':
                    expect_content_type = 'application/octet-stream'
                else:
                    expect_content_type = fmt
                assert response['Content-Type'] == expect_content_type

                response_content = response.getvalue()
                image = Image.open(BytesIO(response_content))
                assert image.size[0] == width


@pytest.mark.django_db
def test_file_render_multi_format_obeys_formats(django_assert_num_queries):
    # Basic test: does it output webp and png?
    image = SamplePNGFileFactory()
    with django_assert_num_queries(0):
        parsed = MultiFormatSoupParser(image.render_multi_format(width=800, height=600))
    assert list(parsed.srcsets) == ['image/png', 'image/webp']
    parsed.validate_srcsets()

    # Does it output only PNG when asked?
    parsed = MultiFormatSoupParser(image.render_multi_format(width=800, height=600, webp=False))
    assert list(parsed.srcsets) == ['image/png']
    parsed.validate_srcsets()

    # If we have or have not specified webp
    image = SampleWebPFileFactory()
    for use_webp in [True, False]:
        parsed = MultiFormatSoupParser(image.render_multi_format(width=800, height=600, webp=use_webp))
        assert list(parsed.srcsets) == ['image/webp']


@pytest.mark.django_db
@override_settings(UNCMS={'IMAGE_WIDTHS': [900, 901, 1024]})
def test_file_render_multi_format_sizing():
    # Ensure that deduplication works - that no width in IMAGE_WIDTHS is
    # ever added to an srcset if it is larger than the requested width
    image = SamplePNGFileFactory()
    parsed = MultiFormatSoupParser(image.render_multi_format(width=900))
    assert list(parsed.srcsets) == ['image/png', 'image/webp']
    for sources in parsed.srcsets.values():
        assert len(sources) == 1
        assert sources[0][1] == 900

    # and while we're here...
    parsed.validate_srcsets()


@pytest.mark.django_db
def test_file_render_multi_format_obeys_alt_text():
    # Ensure "None" is not displayed as the alt text if nothing has been
    # specified.
    image = SamplePNGFileFactory(alt_text=None)
    parsed = MultiFormatSoupParser(image.render_multi_format(width=800, height=600))
    assert parsed.alt_text == ''

    # Test branch wherein an alt text is set on the image.
    image.alt_text = 'Testing'
    parsed = MultiFormatSoupParser(image.render_multi_format(width=800, height=600))
    assert parsed.alt_text == 'Testing'

    # Test branch wherein an alt text is set on the image, but we've
    # overridden it.
    image.alt_text = 'Testing 2'
    parsed = MultiFormatSoupParser(image.render_multi_format(width=800, height=600, alt_text='Override'))
    assert parsed.alt_text == 'Override'

    # Test branch wherein we've explicitly requested that it is the empty
    # string (e.g. for a decorative image).
    image.alt_text = 'Testing 3'
    parsed = MultiFormatSoupParser(image.render_multi_format(width=800, height=600, alt_text=''))
    assert parsed.alt_text == ''


@pytest.mark.django_db
def test_file_render_multi_format_obeys_lazy():
    image = SamplePNGFileFactory()
    parsed = MultiFormatSoupParser(image.render_multi_format(width=800, height=600))
    assert parsed.loading_attribute == 'lazy'

    parsed = MultiFormatSoupParser(image.render_multi_format(width=800, height=600, lazy=False))
    assert parsed.loading_attribute is None


@pytest.mark.django_db
def test_file_render_multi_format_obeys_aspect():
    image = SamplePNGFileFactory()
    parsed = MultiFormatSoupParser(image.render_multi_format(width=960))
    assert parsed.style_attribute == 'aspect-ratio: 960 / 540'

    parsed = MultiFormatSoupParser(image.render_multi_format(width=960, aspect=False))
    assert parsed.style_attribute is None


@pytest.mark.django_db
def test_file_render_multi_format_obeys_sizes_attribute():
    image = SamplePNGFileFactory()
    parsed = MultiFormatSoupParser(image.render_multi_format(width=960))
    assert parsed.sizes_attributes == ['100vw', '100vw']

    parsed = MultiFormatSoupParser(image.render_multi_format(width=960, sizes_attribute='50vw'))
    assert parsed.sizes_attributes == ['50vw', '50vw']


@pytest.mark.django_db
def test_file_render_multi_format_on_nonsense():
    garbage = EmptyFileFactory()
    assert garbage.render_multi_format(width=400, height=200) == ''