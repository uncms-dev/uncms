import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from uncms.media.forms import FileForm, ImageUploadForm, mime_check
from uncms.testhelpers.factories import UserFactory
from uncms.testhelpers.factories.media import (
    MINIMAL_GIF_DATA,
    FileFactory,
)


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
    file = SimpleUploadedFile(name="sample.imaginary", content=b"")
    assert FileForm.user_can_upload_file(user, file) is False
    with override_settings(UNCMS={"MEDIA_UPLOAD_ALLOWED_EXTENSIONS": ["imaginary"]}):
        assert FileForm.user_can_upload_file(user, file) is True

    with override_settings(UNCMS={"MEDIA_UPLOAD_ALLOWED_EXTENSIONS": ["*"]}):
        assert FileForm.user_can_upload_file(user, file) is True

    # Check that the "allow images uploads" default works, and can be turned
    # off.
    user = UserFactory()
    file = SimpleUploadedFile(name="sample.jpg", content=b"")
    assert FileForm.user_can_upload_file(user, file) is True
    with override_settings(UNCMS={"MEDIA_UPLOAD_ALWAYS_ALLOW_IMAGES": False}):
        assert FileForm.user_can_upload_file(user, file) is False

    # Ensure that the permissions bypass works.
    file = SimpleUploadedFile(name="sample.imaginary", content=b"")
    user = UserFactory(permissions=["media.upload_dangerous_files"])
    assert FileForm.user_can_upload_file(user, file) is True
    with override_settings(UNCMS={"MEDIA_UPLOAD_PERMISSIONS_BYPASS": False}):
        assert FileForm.user_can_upload_file(user, file) is False

    # Ensure the same works for superusers. (probably pointless)
    file = SimpleUploadedFile(name="sample.imaginary", content=b"")
    user = UserFactory(superuser=True)
    assert FileForm.user_can_upload_file(user, file) is True
    with override_settings(UNCMS={"MEDIA_UPLOAD_PERMISSIONS_BYPASS": False}):
        assert FileForm.user_can_upload_file(user, file) is False


@pytest.mark.django_db
@override_settings(UNCMS={"MEDIA_UPLOAD_ALLOWED_EXTENSIONS": ["txt"]})
def test_fileform_validation():
    user = UserFactory()
    # Ensure MIME type checking for images on ImageForm works.

    def assert_has_file_mismatch(form):
        assert form.is_valid() is False
        assert len(form.errors) == 1
        assert len(form.errors["file"]) == 1
        assert "Make sure the file extension is correct" in form.errors["file"][0]

    data = {"title": "Example"}

    # Check that non-image files are not being validated.
    form = FileForm(
        user=user,
        data=data,
        files={
            "file": SimpleUploadedFile(
                name="sample.txt", content=b"XX", content_type="text/plain"
            )
        },
    )
    assert form.is_valid() is True

    # Check against a real GIF with the right content type.
    form = FileForm(
        user=user,
        data=data,
        files={
            "file": SimpleUploadedFile(
                name="sample.gif", content=MINIMAL_GIF_DATA, content_type="image/gif"
            )
        },
    )
    assert form.is_valid() is True

    for mimetype, extension in [("image/jpeg", "jpg"), ("image/webp", "webp")]:
        # Check uploading image with the wrong image content type.
        form = FileForm(
            user=user,
            data=data,
            files={
                "file": SimpleUploadedFile(
                    name=f"sample.{extension}",
                    content=MINIMAL_GIF_DATA,
                    content_type=mimetype,
                )
            },
        )
        assert_has_file_mismatch(form)

        # Check uploading non-image data, with an image content type..
        form = FileForm(
            user=user,
            data=data,
            files={
                "file": SimpleUploadedFile(
                    name=f"sample.{extension}",
                    content=MINIMAL_GIF_DATA,
                    content_type=mimetype,
                )
            },
        )
        assert_has_file_mismatch(form)

    # Check against uploading an unknown extension.
    form = FileForm(
        user=user,
        data=data,
        files={"file": SimpleUploadedFile(name="sample.imaginary", content=b"??")},
    )
    assert form.is_valid() is False


def test_mime_check():
    # An image whose contents match the given extension
    file_1 = SimpleUploadedFile(
        "sample.gif", MINIMAL_GIF_DATA, content_type="image/gif"
    )
    # ...and one whose contents do not...
    file_2 = SimpleUploadedFile(
        "sample.jpg", MINIMAL_GIF_DATA, content_type="image/jpeg"
    )
    # ...and one we should never check (we only care about images)
    file_3 = SimpleUploadedFile(
        "sample.bin", MINIMAL_GIF_DATA, content_type="application/octet-stream"
    )

    assert mime_check(file_1) is True
    assert mime_check(file_2) is False
    assert mime_check(file_3) is True


@pytest.mark.django_db
def test_fileform_validation_editing_existing_file():
    """
    Test validation when editing an existing file (branch 71->88 false branch).
    When updating a file instance without changing the file itself, validation
    should be skipped.
    """
    user = UserFactory()
    existing_file = FileFactory(minimal_gif=True)

    # Update metadata only, without changing the file - should skip validation
    form = FileForm(
        user=user,
        instance=existing_file,
        data={"title": "Updated Title"},
    )
    assert form.is_valid() is True

    # Try to update an existing file with a mismatched MIME type
    form = FileForm(
        user=user,
        instance=existing_file,
        data={"title": "Updated"},
        files={
            "file": SimpleUploadedFile(
                name="updated.jpg",
                content=MINIMAL_GIF_DATA,
                content_type="image/jpeg",
            )
        },
    )
    assert form.is_valid() is False
    assert "Make sure the file extension is correct" in form.errors["file"][0]

    # Try to update with a disallowed file type
    form = FileForm(
        user=user,
        instance=existing_file,
        data={"title": "Updated"},
        files={
            "file": SimpleUploadedFile(
                name="updated.html",
                content=b"<html></html>",
                content_type="text/html",
            )
        },
    )
    assert form.is_valid() is False
    assert "permission" in form.errors["file"][0]


@pytest.mark.django_db
def test_imageuploadform_clean_file_non_image():
    """
    Test ImageUploadForm.clean_file() when file is not an image (line 133).
    """
    user = UserFactory()
    form = ImageUploadForm(
        user=user,
        data={"alt": "Not an image"},
        files={
            "file": SimpleUploadedFile(
                name="sample.txt", content=b"text content", content_type="text/plain"
            )
        },
    )
    assert form.is_valid() is False
    assert "does not appear to be an image file" in form.errors["file"][0]


@pytest.mark.django_db
def test_imageuploadform_save_with_alt_text():
    """
    Test ImageUploadForm.save() when alt text is provided (branch 145->147).
    """
    user = UserFactory()
    form = ImageUploadForm(
        user=user,
        data={"alt": "A beautiful image"},
        files={
            "file": SimpleUploadedFile(
                name="sample.gif", content=MINIMAL_GIF_DATA, content_type="image/gif"
            )
        },
    )
    assert form.is_valid()
    instance = form.save()

    assert instance.title == "A beautiful image"
    assert instance.alt_text == "A beautiful image"


@pytest.mark.django_db
def test_imageuploadform_save_without_alt_text():
    """
    Test ImageUploadForm.save() when alt text is NOT provided (branch 148->151).
    """
    user = UserFactory()
    form = ImageUploadForm(
        user=user,
        data={"alt": ""},
        files={
            "file": SimpleUploadedFile(
                name="my_sample_image.gif",
                content=MINIMAL_GIF_DATA,
                content_type="image/gif",
            )
        },
    )
    assert form.is_valid()
    instance = form.save()

    assert instance.title == "my_sample_image"
    assert instance.alt_text == ""


@pytest.mark.django_db
def test_imageuploadform_save_with_existing_title():
    """
    Test ImageUploadForm.save() when instance already has a title.
    """
    user = UserFactory()
    existing_file = FileFactory(minimal_gif=True, title="Existing title")

    form = ImageUploadForm(
        user=user,
        instance=existing_file,
        data={"alt": "New alt text"},
        files={
            "file": SimpleUploadedFile(
                name="updated.gif",
                content=MINIMAL_GIF_DATA,
                content_type="image/gif",
            )
        },
    )
    assert form.is_valid()
    instance = form.save()

    assert instance.title == "Existing title"
    assert instance.alt_text == "New alt text"
