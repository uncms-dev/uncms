import os.path
from io import BytesIO

import factory

from cms.apps.media.models import File


class FileFactory(factory.django.DjangoModelFactory):
    title = factory.Sequence(lambda n: f'File {n}')

    file = factory.django.FileField()

    class Meta:
        model = File


class EmptyFileFactory(FileFactory):
    file = factory.django.FileField(from_func=lambda: BytesIO(b''))


class SamplePNGFileFactory(FileFactory):

    file = factory.django.FileField(
        from_path=os.path.join(os.path.dirname(__file__), 'data', '1920x1080.png'),
    )


class SampleJPEGFileFactory(FileFactory):

    file = factory.django.FileField(
        from_path=os.path.join(os.path.dirname(__file__), 'data', '1920x1080.jpg'),
    )