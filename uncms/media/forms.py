import base64
import os
from io import BytesIO

import magic
import reversion
from django import forms
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from PIL import Image

from uncms.media.filetypes import IMAGE_MIMETYPES
from uncms.media.models import File


def mime_check(file):
    '''
    Compares the MIME type implied by a image file's extension to that
    calculated by python-magic. Returns False if they do not match, True
    otherwise.
    '''
    guessed_filetype = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)
    claimed_filetype = file.content_type
    if claimed_filetype in IMAGE_MIMETYPES.values() and not guessed_filetype == claimed_filetype:
        return False
    return True


class FileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ['title', 'file', 'attribution', 'copyright', 'alt_text', 'labels']

    def clean_file(self):
        """
        `clean_file` checks nominal images to see if they do in fact match
        their declared contents. This comes from extensive experience of files
        being "converted" into some other format by simply changing the file
        extension.

        For most other formats, it doesn't matter if they upload with the
        wrong extension. With images, it means that exceptions will be raised
        when thumbnailing them.
        """
        uploaded_file = self.cleaned_data['file']

        # Catch if this is the initial creation or if the file is being changed.
        if not self.instance or not self.instance.file == uploaded_file:
            if not mime_check(uploaded_file):
                raise forms.ValidationError(_(
                    'The file extension for this image does not seem to match its contents. '
                    'Make sure the file extension is correct and try again.'
                ))
        return uploaded_file


class ImageEditForm(forms.ModelForm):
    changed_image = forms.CharField(
        widget=forms.HiddenInput,
        required=False,
    )

    class Meta:
        model = File
        fields = ['changed_image']

    def save(self, commit=True):
        if self.cleaned_data['changed_image']:
            # Get image data from canvas and decode it; this will always be
            # in base64-encoded PNG format:
            # data:image/png;base64,[...image data....]
            changed_image = self.cleaned_data['changed_image']
            image_data = base64.b64decode(changed_image.split(';base64,')[1])
            root_name, extension = os.path.splitext(
                os.path.basename(self.instance.file.name)
            )

            # Each time a file is saved, Django will append _XXXXX until the
            # file name is unique. Taking the part before the first underscore
            # will prevent files being given increasingly long names, e.g.
            # file_AS8Cs2_yb93Df_r87fdc.jpg if it's been edited 3 times.
            #
            # The tradeoff is that if an image is uploaded as
            # Flowering_Cherry_Tree.jpg, the first time it is edited it will
            # be saved as Flowering_Cherry.jpg. This is less bad than the
            # alternative.
            new_file_name = '{}{}'.format(root_name.rsplit('_', 1)[0], extension)
            content_file = ContentFile(image_data, name=new_file_name)

            if extension.lower() in ('.jpeg', '.jpg'):
                # Remove alpha channel for JPEGs - attempting to save with an
                # alpha channel still present will throw an exception.
                with Image.open(content_file) as image:
                    image.load()  # required for png.split()
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[3])  # 3 is the alpha channel
                    thumb_io = BytesIO()
                    # Each save of a JPEG results in a small amount of degradation;
                    # use quality=100 to limit this.
                    background.save(thumb_io, 'JPEG', quality=100)
                    self.instance.file.save(
                        new_file_name, content=ContentFile(thumb_io.getvalue()), save=False
                    )

            else:
                self.instance.file.save(new_file_name, content=content_file)
            with reversion.create_revision():
                return super().save(commit=commit)
        return self.instance
