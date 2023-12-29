import base64
import os.path
from io import BytesIO

import factory

from uncms.media.models import File, Label

# The very minimum data for a valid GIF.
MINIMAL_GIF_DATA = base64.b64decode(
    b"R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="
)


def data_file_path(filename):
    return os.path.join(os.path.dirname(__file__), "data", filename)


class FileFactory(factory.django.DjangoModelFactory):
    title = factory.Sequence(lambda n: f"File {n}")

    file = factory.django.FileField()

    class Meta:
        model = File


class EmptyFileFactory(FileFactory):
    file = factory.django.FileField(from_func=lambda: BytesIO(b""))


class SamplePNGFileFactory(FileFactory):
    file = factory.django.FileField(
        from_path=data_file_path("1920x1080.png"),
    )


class SampleJPEGFileFactory(FileFactory):
    file = factory.django.FileField(
        from_path=data_file_path("1920x1080.jpg"),
    )


class SampleWebPFileFactory(FileFactory):
    file = factory.django.FileField(
        from_path=data_file_path("1920x1080.webp"),
    )


class MinimalGIFFileFactory(FileFactory):
    file = factory.django.FileField(
        data=MINIMAL_GIF_DATA,
    )


class SVGFileFactory(FileFactory):
    file = factory.django.FileField(
        # from Remix Icon - https://remixicon.com/
        data=b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M7.83 11H20v2H7.83l5.36 5.36-1.41 1.42L4 12l7.78-7.78 1.41 1.42L7.83 11Z"/></svg>',
        filename="sample.svg",
    )


class LabelFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Label {n}")

    class Meta:
        model = Label
