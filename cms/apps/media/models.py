from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from PIL import Image

from cms.apps.media.fields import FileRefField, ImageRefField, VideoFileRefField
from cms.apps.media.filetypes import get_icon, is_image


class Label(models.Model):
    '''
    A label used to organise static media.
    '''

    name = models.CharField(
        max_length=200,
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)


class File(models.Model):
    '''A static file.'''

    title = models.CharField(
        max_length=200,
    )

    labels = models.ManyToManyField(
        Label,
        blank=True,
        help_text='Labels are used to help organise your media. They are not visible to users on your website.',
    )

    file = models.FileField(
        upload_to='uploads/files',
        max_length=250,
    )

    width = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        default=0,
    )

    height = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        default=0,
    )

    attribution = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
    )

    copyright = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
    )

    alt_text = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='This text will be used for screen readers. Leave it empty for purely decorative images.',
    )

    date_added = models.DateTimeField(
        default=timezone.now,
    )

    def get_absolute_url(self):
        return self.file.url

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-date_added', '-pk']

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)
        if self.is_image():
            dimensions = self.get_dimensions()

            if dimensions:
                self.width, self.height = dimensions
                super().save(False, True, using=using, update_fields=update_fields)

    @cached_property
    def icon(self):
        return get_icon(self.file.name)

    def is_image(self):
        return is_image(self.file.name)

    def get_dimensions(self):
        try:
            with open(self.file.path, 'rb') as f:
                try:
                    image = Image.open(f)
                    image.verify()
                except IOError:
                    return (0, 0)

            return image.size
        except IOError:
            return (0, 0)


__all__ = [
    'File',
    'Label',
    'ImageRefField',
    'FileRefField',
    'VideoFileRefField',
]
