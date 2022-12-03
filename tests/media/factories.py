import base64
import os.path
from io import BytesIO

import factory

from uncms.media.models import File

# The very minimum data for a valid GIF.
MINIMAL_GIF_DATA = base64.b64decode(b'R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==')


def data_file_path(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)


class FileFactory(factory.django.DjangoModelFactory):
    title = factory.Sequence(lambda n: f'File {n}')

    file = factory.django.FileField()

    class Meta:
        model = File


class EmptyFileFactory(FileFactory):
    file = factory.django.FileField(from_func=lambda: BytesIO(b''))


class SamplePNGFileFactory(FileFactory):

    file = factory.django.FileField(
        from_path=data_file_path('1920x1080.png'),
    )


class SampleJPEGFileFactory(FileFactory):

    file = factory.django.FileField(
        from_path=data_file_path('1920x1080.jpg'),
    )


class SampleWebPFileFactory(FileFactory):

    file = factory.django.FileField(
        from_path=data_file_path('1920x1080.webp'),
    )


class MinimalGIFFileFactory(FileFactory):
    file = factory.django.FileField(
        from_string=b'R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==',
    )
