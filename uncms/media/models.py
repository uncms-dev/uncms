from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from PIL import Image

from uncms.conf import defaults
from uncms.media.fields import FileRefField, ImageRefField, VideoFileRefField
from uncms.media.filetypes import (
    IMAGE_MIMETYPES,
    get_icon,
    is_image,
    normalised_file_extension,
)
from uncms.media.types import MultiThumbnail, Thumbnail
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

    @cached_property
    def file_extension(self):
        """
        file_extension returns a normalised lower-case version of this file's
        extension with no preceding ".".
        """
        return normalised_file_extension(self.file.name)

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

    def get_thumbnail(self, *, width='auto', height='auto', crop='none', fmt='source', colorspace='auto', quality=None) -> Thumbnail:
        """
        `get_thumbnail` returns a Thumbnail instance with the predicted width,
        height, and URL of a thumbnail for the given image, geometry and
        parameters.

        It does not do the actual thumbnailing, and must not contain any
        expensive operations; using this method should be close to free
        because it is called repeatedly by e.g. the render_multi_format
        method on this class.
        """
        if width == 'auto' and height == 'auto':
            raise ValueError('no dimensions provided - specify either height or width')

        url = reverse('media_library:image_view', kwargs={
            'pk': self.pk,
            'width': str(width),
            'height': str(height),
            'crop': crop,
            'format': fmt,
            'colorspace': colorspace,
            'quality': quality or 'default',
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

    def render_multi_format(
            self,
            *,
            width='auto',
            height='auto',
            colorspace='auto',
            quality=None,
            aspect=True,
            alt_text=None,
            webp=True,
            lazy=True,
            sizes_attribute='100vw',
    ):
        # Don't try and render a broken image or non-image. Nothing sensible
        # to do here, so render nothing.
        if not self.is_image or not (self.height and self.width):
            return ''

        context = {
            'original_url': self.get_absolute_url(),
            # Put ourself in the context in case a template override wants it.
            'original': self,
            'lazy': lazy,
            'class_prefix': defaults.IMAGE_CLASS_PREFIX,
        }

        # If an explicit empty alt text has been specified, then obey that
        if alt_text is not None:
            context['alt_text'] = alt_text

        # Otherwise, use an empty string (do not display "None")
        else:
            context['alt_text'] = self.alt_text or ''

        always_args = {'colorspace': colorspace, 'quality': quality}

        # Calculate our initial format, preserving the format. This will give
        # us an expected ratio for calculating all of our other sizes which
        # allows us to dedupe based on width alone.
        initial_thumb = self.get_thumbnail(
            width=width,
            height=height,
            fmt='source',
            **always_args,
        )

        original_mimetype = IMAGE_MIMETYPES[self.file_extension]

        multi = MultiThumbnail()
        multi.add_size(original_mimetype, initial_thumb)

        if webp:
            multi.add_size('image/webp', self.get_thumbnail(
                width=width,
                height=height,
                fmt='webp',
                **always_args,
            ))

        for default_width in defaults.IMAGE_WIDTHS:
            # IMAGE_WIDTHS are merely suggested widths; don't upscale past the
            # initial requested thumbnail width. We don't handle the
            # *same* size case here (hence >, rather than >=); that is handled
            # by MultiThumbnail's deduplication.
            if default_width > initial_thumb.width:
                continue
            height = round(default_width * initial_thumb.height_ratio)
            multi.add_size(original_mimetype, self.get_thumbnail(
                width=default_width,
                height=round(default_width * initial_thumb.height_ratio),
                **always_args,
            ))

            if webp:
                # In the unusual case that our source image is already a
                # WebP, we can let MultiThumbnail take care of duplicates.
                multi.add_size('image/webp', self.get_thumbnail(
                    width=default_width,
                    height=round(default_width * initial_thumb.height_ratio),
                    fmt='webp',
                    **always_args,
                ))

        # Add the "ratio" attribute so browsers can pre-size the image
        # appropriately.
        if aspect:
            context['aspect_ratio'] = initial_thumb.aspect_ratio_string

        context['formats'] = multi
        context['sizes_attribute'] = sizes_attribute
        return render_to_string(defaults.IMAGE_TEMPLATE, context)

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