from django.core.files.uploadedfile import SimpleUploadedFile

from tests.media.factories import MINIMAL_GIF_DATA
from uncms.media.forms import FileForm


def test_fileform_validation():
    # Ensure MIME type checking for images on ImageForm works.

    def assert_has_file_mismatch(form):
        assert form.is_valid() is False
        assert len(form.errors) == 1
        assert len(form.errors['file']) == 1
        assert 'Make sure the file extension is correct' in form.errors['file'][0]

    data = {'title': 'Example'}

    # Check that non-image files are not being validated.
    form = FileForm(data=data, files={
        'file': SimpleUploadedFile(name='sample.txt', content=b'XX', content_type='text/plain')
    })
    assert form.is_valid() is True

    # Check against a real GIF with the right content type.
    form = FileForm(data=data, files={
        'file': SimpleUploadedFile(name='sample.gif', content=MINIMAL_GIF_DATA, content_type='image/gif')
    })
    assert form.is_valid() is True

    for mimetype, extension in [('image/jpeg', 'jpg'), ('image/webp', 'webp')]:
        # Check uploading image with the wrong image content type.
        form = FileForm(data=data, files={
            'file': SimpleUploadedFile(name=f'sample.{extension}', content=MINIMAL_GIF_DATA, content_type=mimetype)
        })
        assert_has_file_mismatch(form)

        # Check uploading non-image data, with an image content type..
        form = FileForm(data=data, files={
            'file': SimpleUploadedFile(name=f'sample.{extension}', content=MINIMAL_GIF_DATA, content_type=mimetype)
        })
        assert_has_file_mismatch(form)
