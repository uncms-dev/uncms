from django.contrib import admin
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.db import models

from uncms.media.widgets import ImageThumbnailWidget
from uncms.conf import defaults


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


IMAGE_FILTER = {
    'file__iregex': r'\.(png|gif|jpg|jpeg)$'
}


class ImageRefField(FileRefField):
    '''A foreign key to a File, constrained to only select image files.'''

    def __init__(self, **kwargs):
        kwargs['limit_choices_to'] = IMAGE_FILTER
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
