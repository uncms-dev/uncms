from hashlib import sha256
from io import BytesIO

import pytest
from django.conf import settings
from django.contrib.auth.models import Permission
from django.test.utils import override_settings
from django.urls import reverse
from PIL import Image

from uncms.models.base import path_token_generator
from uncms.testhelpers.factories import UserFactory
from uncms.testhelpers.factories.media import (
    EmptyFileFactory,
    SampleJPEGFileFactory,
    SamplePNGFileFactory,
)


@pytest.mark.django_db
def test_file_redirect_view(client):
    def is_login_url(url):
        return url.startswith(settings.LOGIN_URL)

    obj = EmptyFileFactory()
    url = reverse("media_library:file_redirect", args=[obj.pk])

    response = client.get(url)
    assert response.status_code == 302
    assert is_login_url(response["Location"])

    user = UserFactory()
    client.force_login(user)

    response = client.get(url)
    assert response.status_code == 403

    user.is_staff = True
    user.user_permissions.add(Permission.objects.get(codename="view_file"))
    user.save()

    response = client.get(url)
    assert response.status_code == 302
    assert is_login_url(response["Location"]) is False
    assert response["Location"] == obj.get_absolute_url()


@pytest.mark.django_db
def test_image_view(client):  # pylint:disable=too-many-statements
    def image_view_kwargs(**kwargs):
        defaults = {
            "width": "auto",
            "height": "auto",
            "format": "source",
            "colorspace": "auto",
            "quality": "default",
            "crop": "none",
        }
        defaults.update(**kwargs)
        return defaults

    def check_image_at_location(
        url, *, expect_width, expect_height, expect_content_type
    ):
        response = client.get(url)
        assert response.status_code == 200
        response_content = response.getvalue()
        image = Image.open(BytesIO(response_content))
        assert image.size == (expect_width, expect_height)
        assert response["Content-Type"] == expect_content_type
        return sha256(response_content).hexdigest()

    # Try with a non-existent PK; the response should be 400, not 404, because
    # the signature check must be performed first.
    url = reverse("media_library:image_view", kwargs=image_view_kwargs(pk="0"))
    for bad_signature_url in [url, f"{url}?signature=fdsfsdf"]:
        with override_settings(DEBUG=False):
            response = client.get(bad_signature_url)
        assert response.status_code == 400
        assert response.content == b"Bad signature."

    # Check a good signature, non-existent PK.
    response = client.get(
        path_token_generator.make_url(url, token_parameter="signature")
    )
    assert response.status_code == 404

    empty_file = EmptyFileFactory.create()
    url = reverse(
        "media_library:image_view", kwargs=image_view_kwargs(pk=empty_file.pk)
    )
    response = client.get(
        path_token_generator.make_url(url, token_parameter="signature")
    )
    assert response.status_code == 404

    # SamplePNGFileFactory will create a 1920x1080 image.
    image_file = SamplePNGFileFactory.create()

    url = reverse(
        "media_library:image_view",
        kwargs=image_view_kwargs(pk=image_file.pk, width=960),
    )
    response = client.get(
        path_token_generator.make_url(url, token_parameter="signature")
    )
    assert response.status_code == 302
    # Check image dimensions at URL. This doubles as a check that the
    # thumbnail is actually being generated.
    check_image_at_location(
        response["Location"],
        expect_width=960,
        expect_height=540,
        expect_content_type="image/png",
    )

    # Check other formats are being generated if requested.
    for thumbnail_format, mime_type in (
        ("jpeg", "image/jpeg"),
        ("webp", "application/octet-stream"),
    ):
        url = reverse(
            "media_library:image_view",
            kwargs=image_view_kwargs(
                pk=image_file.pk, format=thumbnail_format, width=960
            ),
        )
        response = client.get(
            path_token_generator.make_url(url, token_parameter="signature")
        )
        assert response.status_code == 302
        check_image_at_location(
            response["Location"],
            expect_width=960,
            expect_height=540,
            expect_content_type=mime_type,
        )

    # Check auto-width is working
    url = reverse(
        "media_library:image_view",
        kwargs=image_view_kwargs(pk=image_file.pk, height=540),
    )
    response = client.get(
        path_token_generator.make_url(url, token_parameter="signature")
    )
    assert response.status_code == 302
    check_image_at_location(
        response["Location"],
        expect_width=960,
        expect_height=540,
        expect_content_type="image/png",
    )

    # Check cropping is working
    url = reverse(
        "media_library:image_view",
        kwargs=image_view_kwargs(pk=image_file.pk, width=60, height=60),
    )
    response = client.get(
        path_token_generator.make_url(url, token_parameter="signature")
    )
    assert response.status_code == 302
    # This time we want to look at the hash of the cropped file. We can't
    # reasonably check the image, but we can see if the hash changes when we
    # specify different crop parameters.
    center_cropped_hash = check_image_at_location(
        response["Location"],
        expect_width=60,
        expect_height=60,
        expect_content_type="image/png",
    )

    # Try specifying different crop parameters - we should get a different
    # response hash
    url = reverse(
        "media_library:image_view",
        kwargs=image_view_kwargs(pk=image_file.pk, width=60, height=60, crop="left"),
    )
    response = client.get(
        path_token_generator.make_url(url, token_parameter="signature")
    )
    assert response.status_code == 302
    left_cropped_hash = check_image_at_location(
        response["Location"],
        expect_width=60,
        expect_height=60,
        expect_content_type="image/png",
    )
    assert left_cropped_hash != center_cropped_hash

    # Try the GRAY colorspace parameter, again making sure the image actually
    # changes again
    url = reverse(
        "media_library:image_view",
        kwargs=image_view_kwargs(
            pk=image_file.pk, width=60, height=60, colorspace="gray"
        ),
    )
    response = client.get(
        path_token_generator.make_url(url, token_parameter="signature")
    )
    assert response.status_code == 302
    gray_hash = check_image_at_location(
        response["Location"],
        expect_width=60,
        expect_height=60,
        expect_content_type="image/png",
    )
    assert gray_hash != center_cropped_hash

    #
    # Try it with a JPEG file. "quality" has no effect on PNGs.
    #
    jpeg_file = SampleJPEGFileFactory()
    url = reverse(
        "media_library:image_view",
        kwargs=image_view_kwargs(pk=jpeg_file.pk, width=640, height=480),
    )
    response = client.get(
        path_token_generator.make_url(url, token_parameter="signature")
    )
    assert response.status_code == 302
    jpeg_hash = check_image_at_location(
        response["Location"],
        expect_width=640,
        expect_height=480,
        expect_content_type="image/jpeg",
    )

    url = reverse(
        "media_library:image_view",
        kwargs=image_view_kwargs(pk=jpeg_file.pk, width=640, height=480, quality=10),
    )
    response = client.get(
        path_token_generator.make_url(url, token_parameter="signature")
    )
    assert response.status_code == 302
    dodgy_jpeg_hash = check_image_at_location(
        response["Location"],
        expect_width=640,
        expect_height=480,
        expect_content_type="image/jpeg",
    )
    assert dodgy_jpeg_hash != jpeg_hash
