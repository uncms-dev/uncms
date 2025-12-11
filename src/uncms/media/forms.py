import os

import magic
from django import forms
from django.apps import apps
from django.utils.translation import gettext_lazy as _

from uncms.conf import defaults
from uncms.media.filetypes import IMAGE_MIMETYPES, is_image, normalised_file_extension


def mime_check(file):
    """
    Compares the MIME type implied by a image file's extension to that
    calculated by python-magic. Returns False if they do not match, True
    otherwise.
    """
    guessed_filetype = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)
    claimed_filetype = file.content_type
    if (
        claimed_filetype in IMAGE_MIMETYPES.values()
        and not guessed_filetype == claimed_filetype
    ):
        return False
    return True


class FileForm(forms.ModelForm):
    class Meta:
        # make swappable
        model = apps.get_model(defaults.MEDIA_FILE_MODEL)
        fields = ["title", "file", "attribution", "copyright", "alt_text", "labels"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean_file(self):
        """
        `clean_file` checks that the given file is allowed to be uploaded
        based on the file extension. This is to prevent e.g. a .html file
        being uploaded; a less-privileged user might be able to cause a
        privilege escalation by uploading a .html file with malicious JS in
        it, then tricking a more-privileged user into visiting the URL, which
        could result in a privilege escalation.

        The default is to only allow images to be uploaded, unless the user
        has an explicit permission to upload dangerous files, or they are a
        superuser, in which case they can cause any amount of destruction like
        deleting everything on the site.

        It also checks nominal images to see if they do in fact match their
        declared contents. This comes from extensive experience of files being
        "converted" into some other format by changing the file extension.

        For most other formats, it doesn't matter if they upload with the
        wrong extension. With images, it means that exceptions will be raised
        when thumbnailing them. Note that this trusts the MIME type coming
        from the client; this is intended to prevent deliberate uploading of
        the wrong file type.
        """
        uploaded_file = self.cleaned_data["file"]

        # Catch if this is the initial creation or if the file is being changed.
        if not self.instance or not self.instance.file == uploaded_file:
            if not mime_check(uploaded_file):
                raise forms.ValidationError(
                    _(
                        "The file extension for this image does not seem to match its contents. "
                        "Make sure the file extension is correct and try again."
                    )
                )

            # Check that the user can upload files of this type.
            if not self.user_can_upload_file(self.user, uploaded_file):
                _ignore, extension = os.path.splitext(uploaded_file.name)
                raise forms.ValidationError(
                    _(
                        'You do not have permission to upload "{extension}" files.'
                    ).format(extension=extension),
                )
        return uploaded_file

    @classmethod
    def user_can_upload_file(cls, user, file):
        # Only permit a value of "*" if it is the only value - this reduces
        # the risk of accidentally configuring it this way.
        if list(defaults.MEDIA_UPLOAD_ALLOWED_EXTENSIONS) == ["*"]:
            return True

        # Allow the permissions bypass if it is enabled. Note the comparison
        # is `is True`, to avoid accidental misconfiguration. Note also
        # our form's app label - this should make it swappable.
        if defaults.MEDIA_UPLOAD_PERMISSIONS_BYPASS is True and user.has_perm(
            f"{cls._meta.model._meta.app_label}.upload_dangerous_files"
        ):
            return True

        if is_image(file.name) and defaults.MEDIA_UPLOAD_ALWAYS_ALLOW_IMAGES is True:
            return True

        return (
            normalised_file_extension(file.name)
            in defaults.MEDIA_UPLOAD_ALLOWED_EXTENSIONS
        )


class ImageUploadForm(FileForm):
    """
    A variant of FileForm which only permits uploading images. This is
    intended for use with the admin WYSIWYG upload view.

    The frontend uploader has a single "description" field, which it passes
    through as "alt". We use that for both the image's description and "Title"
    field if it is present. Otherwise, we set the "Title" field from the file
    name and save an empty alt text.
    """

    # named such by Trumbowyg with no override
    alt = forms.CharField(
        required=False,
    )

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        if not is_image(uploaded_file.name):
            raise forms.ValidationError(
                _("{name} does not appear to be an image file.").format(
                    name=uploaded_file.name
                )
            )
        return super().clean_file()

    def save(self, commit=True):
        file_meta = apps.get_model(defaults.MEDIA_FILE_MODEL)._meta
        title_max_length = file_meta.get_field("title").max_length
        alt_max_length = file_meta.get_field("alt_text").max_length

        if not self.instance.title:
            if self.cleaned_data.get("alt"):
                self.instance.title = self.cleaned_data["alt"][:title_max_length]
            else:
                self.instance.title = os.path.splitext(self.cleaned_data["file"].name)[
                    0
                ][:title_max_length]

        self.instance.alt_text = self.cleaned_data.get("alt", "")[:alt_max_length]

        return super().save(commit=commit)

    class Meta(FileForm.Meta):
        fields = ["file"]
