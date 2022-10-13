import base64
import random
import sys
from io import BytesIO

import pytest
from django.contrib import admin
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, TransactionTestCase
from django.utils.timezone import now
from PIL import Image

from cms.apps.media.models import File, FileRefField, Label
from cms.apps.media.tests.factories import (
    EmptyFileFactory,
    MinimalGIFFileFactory,
    SamplePNGFileFactory
)
from cms.apps.testing_models.models import MediaTestModel


class TestLabel(TestCase):

    def test_label_unicode(self):
        obj = Label.objects.create(
            name="Foo"
        )

        self.assertEqual(repr(obj), "<Label: Foo>")
        self.assertEqual(str(obj), "Foo")
        self.assertEqual(obj.__str__(), "Foo")


class TestFile(TransactionTestCase):

    def setUp(self):
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
        self.assertEqual(self.obj_1.__str__(), 'Foo')
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
