import base64

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from tests.factories import UserFactory
from tests.media.factories import (
    MINIMAL_GIF_DATA,
    SampleJPEGFileFactory,
    SamplePNGFileFactory,
    data_file_path,
)
from uncms.media.forms import FileForm, ImageEditForm, mime_check


@pytest.mark.django_db
def test_fileform_user_can_upload_file():
    # Note: this test function uses `user = .... file = ....` even when that
    # causes repetition. This is intentional to keep it easier to read.
    # Continue to follow that form if adding new checks and do not be tempted
    # to simplify it by reusing variables.
    #
    # Check the default: don't allow users to upload files with unknown
    # extensions
    user = UserFactory()
    file = SimpleUploadedFile(name='sample.imaginary', content=b'')
    assert FileForm.user_can_upload_file(user, file) is False
    with override_settings(UNCMS={'MEDIA_UPLOAD_ALLOWED_EXTENSIONS': ['imaginary']}):
        assert FileForm.user_can_upload_file(user, file) is True

    with override_settings(UNCMS={'MEDIA_UPLOAD_ALLOWED_EXTENSIONS': ['*']}):
        assert FileForm.user_can_upload_file(user, file) is True

    # Check that the "allow images uploads" default works, and can be turned
    # off.
    user = UserFactory()
    file = SimpleUploadedFile(name='sample.jpg', content=b'')
    assert FileForm.user_can_upload_file(user, file) is True
    with override_settings(UNCMS={'MEDIA_UPLOAD_ALWAYS_ALLOW_IMAGES': False}):
        assert FileForm.user_can_upload_file(user, file) is False

    # Ensure that the permissions bypass works.
    file = SimpleUploadedFile(name='sample.imaginary', content=b'')
    user = UserFactory(permissions=['media.upload_dangerous_files'])
    assert FileForm.user_can_upload_file(user, file) is True
    with override_settings(UNCMS={'MEDIA_UPLOAD_PERMISSIONS_BYPASS': False}):
        assert FileForm.user_can_upload_file(user, file) is False

    # Ensure the same works for superusers. (probably pointless)
    file = SimpleUploadedFile(name='sample.imaginary', content=b'')
    user = UserFactory(superuser=True)
    assert FileForm.user_can_upload_file(user, file) is True
    with override_settings(UNCMS={'MEDIA_UPLOAD_PERMISSIONS_BYPASS': False}):
        assert FileForm.user_can_upload_file(user, file) is False


@pytest.mark.django_db
@override_settings(UNCMS={'MEDIA_UPLOAD_ALLOWED_EXTENSIONS': ['txt']})
def test_fileform_validation():
    user = UserFactory()
    # Ensure MIME type checking for images on ImageForm works.

    def assert_has_file_mismatch(form):
        assert form.is_valid() is False
        assert len(form.errors) == 1
        assert len(form.errors['file']) == 1
        assert 'Make sure the file extension is correct' in form.errors['file'][0]

    data = {'title': 'Example'}

    # Check that non-image files are not being validated.
    form = FileForm(user=user, data=data, files={
        'file': SimpleUploadedFile(name='sample.txt', content=b'XX', content_type='text/plain')
    })
    assert form.is_valid() is True

    # Check against a real GIF with the right content type.
    form = FileForm(user=user, data=data, files={
        'file': SimpleUploadedFile(name='sample.gif', content=MINIMAL_GIF_DATA, content_type='image/gif')
    })
    assert form.is_valid() is True

    for mimetype, extension in [('image/jpeg', 'jpg'), ('image/webp', 'webp')]:
        # Check uploading image with the wrong image content type.
        form = FileForm(user=user, data=data, files={
            'file': SimpleUploadedFile(name=f'sample.{extension}', content=MINIMAL_GIF_DATA, content_type=mimetype)
        })
        assert_has_file_mismatch(form)

        # Check uploading non-image data, with an image content type..
        form = FileForm(user=user, data=data, files={
            'file': SimpleUploadedFile(name=f'sample.{extension}', content=MINIMAL_GIF_DATA, content_type=mimetype)
        })
        assert_has_file_mismatch(form)

    # Check against uploading an unknown extension.
    form = FileForm(user=user, data=data, files={
        'file': SimpleUploadedFile(name='sample.imaginary', content=b'??')
    })
    assert form.is_valid() is False


@pytest.mark.django_db
# Test both the "it's a JPEG" branch and the implied "not a JPEG" branches.
@pytest.mark.parametrize('factory', [SampleJPEGFileFactory, SamplePNGFileFactory])
def test_imageeditform_save(factory):
    original = factory()
    assert original.width == 1920
    with open(data_file_path('800x600.png'), 'rb') as fd:
        changed_data = ''.join([';base64,', base64.b64encode(fd.read()).decode('utf-8')])
    form = ImageEditForm(
        instance=original,
        data={
            'changed_image': changed_data,
        },
    )
    assert form.is_valid()
    form.save()

    original.refresh_from_db()
    assert original.width == 800
    assert original.height == 600


@pytest.mark.django_db
def test_imageeditform_save_no_changes_branch():
    """
    Test the "changed_data is not present" branch.
    """
    original = SamplePNGFileFactory()
    assert original.width == 1920
    form = ImageEditForm(
        instance=original,
        data={
            'changed_image': '',
        },
    )
    assert form.is_valid()
    form.save()

    original.refresh_from_db()
    assert original.width == 1920


def test_mime_check():
    # An image whose contents match the given extension
    file_1 = SimpleUploadedFile('sample.gif', MINIMAL_GIF_DATA, content_type="image/gif")
    # ...and one whose contents do not...
    file_2 = SimpleUploadedFile('sample.jpg', MINIMAL_GIF_DATA, content_type="image/jpeg")
    # ...and one we should never check (we only care about images)
    file_3 = SimpleUploadedFile('sample.bin', MINIMAL_GIF_DATA, content_type="application/octet-stream")

    assert mime_check(file_1) is True
    assert mime_check(file_2) is False
    assert mime_check(file_3) is True
