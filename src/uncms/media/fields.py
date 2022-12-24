from django.contrib import admin
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.db import models

from uncms.conf import defaults
from uncms.media.filetypes import IMAGE_FILENAME_REGEX
from uncms.media.widgets import ImageThumbnailWidget


class FileRefField(models.ForeignKey):
    '''A foreign key to a File.'''

    def __init__(self, **kwargs):
        kwargs['to'] = defaults.MEDIA_FILE_MODEL
        kwargs.setdefault('related_name', '+')
        kwargs.setdefault('on_delete', models.PROTECT)
        super().__init__(**kwargs)

    def formfield(self, **kwargs):
        kwargs.setdefault('widget', ForeignKeyRawIdWidget(self.remote_field, admin.site))
        return super().formfield(**kwargs)


class ImageRefField(FileRefField):
    '''A foreign key to a File, constrained to only select image files.'''

    def __init__(self, **kwargs):
        # we have to use the regex here because Q objects don't work in
        # related popups in the admin
        kwargs['limit_choices_to'] = {
            'file__iregex': IMAGE_FILENAME_REGEX,
        }

        super().__init__(**kwargs)

    def formfield(self, **kwargs):
        kwargs.setdefault('widget', ImageThumbnailWidget(self.remote_field, admin.site))
        return super().formfield(**kwargs)


VIDEO_FILTER = {
    'file__iregex': r'\.(mp4|m4v)$'
}


class VideoFileRefField(FileRefField):

    '''A foreign key to a File, constrained to only select video files.'''

    def __init__(self, **kwargs):
        kwargs['limit_choices_to'] = VIDEO_FILTER
        super().__init__(**kwargs)
