import base64
import os
from io import BytesIO

import magic
import reversion
from django import forms
from django.apps import apps
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from PIL import Image

from uncms.conf import defaults
from uncms.media.filetypes import (
    IMAGE_MIMETYPES,
    is_image,
    normalised_file_extension,
)


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
        # make swappable
        model = apps.get_model(defaults.MEDIA_FILE_MODEL)
        fields = ['title', 'file', 'attribution', 'copyright', 'alt_text', 'labels']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
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
        uploaded_file = self.cleaned_data['file']

        # Catch if this is the initial creation or if the file is being changed.
        if not self.instance or not self.instance.file == uploaded_file:
            if not mime_check(uploaded_file):
                raise forms.ValidationError(_(
                    'The file extension for this image does not seem to match its contents. '
                    'Make sure the file extension is correct and try again.'
                ))

            # Check that the user can upload files of this type.
            if not self.user_can_upload_file(self.user, uploaded_file):
                _ignore, extension = os.path.splitext(uploaded_file.name)
                raise forms.ValidationError(
                    _('You do not have permission to upload "{extension}" files.').format(extension=extension),
                )
        return uploaded_file

    @classmethod
    def user_can_upload_file(cls, user, file):
        # Only permit a value of "*" if it is the only value - this reduces
        # the risk of accidentally configuring it this way.
        if list(defaults.MEDIA_UPLOAD_ALLOWED_EXTENSIONS) == ['*']:
            return True

        # Allow the permissions bypass if it is enabled. Note the comparison
        # is `is True`, to avoid accidental misconfiguration. Note also
        # our form's app label - this should make it swappable.
        if defaults.MEDIA_UPLOAD_PERMISSIONS_BYPASS is True and user.has_perm(f'{cls._meta.model._meta.app_label}.upload_dangerous_files'):
            return True

        if is_image(file.name) and defaults.MEDIA_UPLOAD_ALWAYS_ALLOW_IMAGES is True:
            return True

        return normalised_file_extension(file.name) in defaults.MEDIA_UPLOAD_ALLOWED_EXTENSIONS


class ImageUploadForm(FileForm):
    """
    A variant of FileForm which only permits uploading images. This is
    intended for use with the admin WYSIWYG upload view.
    """
    # named such by Trumbowyg with no override
    alt = forms.CharField(
        required=False,
    )

    def clean_file(self):
        uploaded_file = self.cleaned_data['file']
        if not is_image(uploaded_file.name):
            raise forms.ValidationError(_('{name} does not appear to be an image file.').format(name=uploaded_file.name))
        return super().clean_file()

    def save(self, commit=True):
        file_meta = apps.get_model(defaults.MEDIA_FILE_MODEL)._meta
        title_max_length = file_meta.get_field('title').max_length
        alt_max_length = file_meta.get_field('alt_text').max_length

        if not self.instance.title:
            if self.cleaned_data.get('alt'):
                self.instance.title = self.cleaned_data['alt'][:title_max_length]
            else:
                self.instance.title = os.path.splitext(self.cleaned_data['file'].name)[0][:title_max_length]

        self.instance.alt_text = self.cleaned_data.get('alt', '')[:alt_max_length]

        return super().save(commit=commit)

    class Meta(FileForm.Meta):
        fields = ['file']


class ImageEditForm(forms.ModelForm):
    changed_image = forms.CharField(
        widget=forms.HiddenInput,
        required=False,
    )

    class Meta:
        # make swappable
        model = apps.get_model(defaults.MEDIA_FILE_MODEL)
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
