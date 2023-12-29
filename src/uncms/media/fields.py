from django.contrib import admin
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.db import models

from uncms.conf import defaults
from uncms.media.filetypes import IMAGE_FILE_EXTENSIONS
from uncms.media.widgets import ImageThumbnailWidget


class FileRefField(models.ForeignKey):
    """A foreign key to a File."""

    def __init__(self, **kwargs):
        kwargs["to"] = defaults.MEDIA_FILE_MODEL
        kwargs.setdefault("related_name", "+")
        kwargs.setdefault("on_delete", models.PROTECT)
        super().__init__(**kwargs)

    def formfield(self, **kwargs):
        kwargs.setdefault(
            "widget", ForeignKeyRawIdWidget(self.remote_field, admin.site)
        )
        return super().formfield(**kwargs)


class RestrictedFileRefField(FileRefField):
    """
    A FileRefField that only allows files of certain extensions.
    """

    allowed_extensions = []

    def __init__(self, **kwargs):
        assert (
            self.allowed_extensions
        ), "using RestrictedFileRefField without allowed_extensions does not make sense"

        kwargs["limit_choices_to"] = {
            "file__iregex": "".join(
                [
                    r"\.",
                    "(",
                    "|".join(self.allowed_extensions),
                    ")",
                    "$",
                ]
            )
        }
        super().__init__(**kwargs)


class ImageRefField(RestrictedFileRefField):
    """
    A foreign key to a File, constrained to only select image files.
    """

    allowed_extensions = IMAGE_FILE_EXTENSIONS

    def formfield(self, **kwargs):
        kwargs.setdefault("widget", ImageThumbnailWidget(self.remote_field, admin.site))
        return super().formfield(**kwargs)


class VideoFileRefField(RestrictedFileRefField):
    """
    A foreign key to a File, constrained to only select video files.
    """

    allowed_extensions = ["mp4", "m4v"]
