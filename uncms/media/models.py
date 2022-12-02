from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from PIL import Image

from uncms.media.fields import FileRefField, ImageRefField, VideoFileRefField
from uncms.media.filetypes import get_icon, is_image
from uncms.media.types import Thumbnail
from uncms.models.base import path_token_generator


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
        help_text=_(
            'Labels are used to help organise your media. They are not visible to users on your website.'
        ),
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
        help_text=_(
            'This text will be used for screen readers. Leave it empty for purely decorative images.'
        ),
    )

    date_added = models.DateTimeField(
        default=timezone.now,
    )

    class Meta:
        ordering = ['-date_added', '-pk']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return self.file.url

    @cached_property
    def icon(self):
        return get_icon(self.file.name)

    def is_image(self):
        return is_image(self.file.name)

    def get_dimensions(self):
        try:
            with self.file.storage.open(self.file.name, 'rb') as f:
                try:
                    image = Image.open(f)
                    image.verify()
                except IOError:
                    return (0, 0)

            return image.size
        except IOError:
            return (0, 0)

    def get_thumbnail(self, *, width='auto', height='auto', crop='none', fmt='source', colorspace='auto', quality='default') -> Thumbnail:
        if width == 'auto' and height == 'auto':
            raise ValueError('no dimensions provided - specify either height or width')

        url = reverse('media_library:image_view', kwargs={
            'pk': self.pk,
            'width': str(width),
            'height': str(height),
            'crop': crop,
            'format': fmt,
            'colorspace': colorspace,
            'quality': quality,
        })

        # Now try and calculate the expected width. If they have specified
        # both height and width, that's going to be the expected height and
        # width, obvs.
        if width != 'auto' and height != 'auto':
            thumb_width, thumb_height = width, height
        elif height == 'auto':
            # They've specified a width but no height. "self.height or 1"
            # guards against a broken image file - this function should be
            # safe to use without throwing an exception.
            thumb_width, thumb_height = width, round(self.height * (width / (self.width or 1)))
        else:
            # due to the exception raised if both are 'auto', this is the only
            # other option: height specified, width auto
            thumb_width, thumb_height = round(self.width * (height / (self.height or 1))), height

        return Thumbnail(
            url=path_token_generator.make_url(url, token_parameter='signature'),
            width=thumb_width,
            height=thumb_height,
        )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)
        if self.is_image():
            dimensions = self.get_dimensions()

            if dimensions:
                self.width, self.height = dimensions
                super().save(False, True, using=using, update_fields=update_fields)


__all__ = [
    'File',
    'Label',
    'ImageRefField',
    'FileRefField',
    'VideoFileRefField',
]
