# pylint:disable=duplicate-code
import pytest
from bs4 import BeautifulSoup
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.views.main import IS_POPUP_VAR
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.utils import override_settings
from django.urls import reverse

from tests.mocks import MockSuperUser
from uncms.media.admin import FileAdmin
from uncms.media.models import File
from uncms.testhelpers.factories import AdminRequestFactory, UserFactory
from uncms.testhelpers.factories.media import (
    FileFactory,
    LabelFactory,
    data_file_path,
)


@pytest.mark.django_db
def test_fileadminbase_changelist_view():
    file_admin = FileAdmin(File, AdminSite())
    request = AdminRequestFactory().get("/")
    request.user = MockSuperUser()
    view = file_admin.changelist_view(request)

    assert view.status_code == 200
    assert view.template_name == "admin/media/file/change_list.html"
    assert "foo" not in view.context_data

    view = file_admin.changelist_view(request, extra_context={"foo": "bar"})
    assert view.status_code == 200
    assert view.template_name == "admin/media/file/change_list.html"
    assert "foo" in view.context_data


@pytest.mark.django_db
def test_fileadmin_add_label_action():
    file_admin = FileAdmin(File, AdminSite())

    obj = FileFactory(empty=True)
    label = LabelFactory()
    assert obj.labels.count() == 0

    file_admin.add_label_action(
        AdminRequestFactory().get("/"), File.objects.all(), label
    )
    assert obj.labels.count() == 1


@pytest.mark.django_db
def test_fileadmin_get_actions():
    site = AdminSite()
    rf = AdminRequestFactory()
    file_admin = FileAdmin(File, site)
    LabelFactory()

    request = rf.get("/")
    request.user = MockSuperUser()
    actions = file_admin.get_actions(request)
    assert len(actions) == 3

    request = rf.get("/?{}".format(IS_POPUP_VAR))
    request.user = MockSuperUser()
    actions = file_admin.get_actions(request)
    assert len(actions) == 0


@pytest.mark.django_db
def test_fileadmin_get_preview():
    file_admin = FileAdmin(File, AdminSite())

    obj = FileFactory(sample_png=True, title="Kittens")
    preview = file_admin.get_preview(obj)
    # We can't do an `assertEqual` here as the generated src URL is dynamic.
    assert preview.startswith(
        f'<img class="uncms-thumbnail" uncms:permalink="/library/redirect/{obj.pk}/"'
    )
    assert preview.endswith('width="200" height="112" alt="" title="Kittens"/>')

    obj = FileFactory(file="media/not/a/real.png")
    preview = file_admin.get_preview(obj)
    assert preview.startswith('<img class="uncms-thumbnail"')

    obj = FileFactory(sample_svg=True)
    preview = file_admin.get_preview(obj)
    assert preview.startswith('<img class="uncms-thumbnail uncms-thumbnail--svg')

    obj = FileFactory(title="Canary", file="media/not/a/real.file")
    preview = file_admin.get_preview(obj)
    assert (
        preview
        == f'<img class="uncms-fallback-icon" uncms:permalink="/library/redirect/{obj.pk}/" src="/static/media/img/text-x-generic-template.png" width="56" height="66" alt="" title="Canary"/>'
    )


@pytest.mark.django_db
def test_fileadmin_get_size():
    file_admin = FileAdmin(File, AdminSite())

    seven_bytes = FileFactory(file__data="abcdefg")
    assert file_admin.get_size(seven_bytes) == "7\xa0bytes"

    bad_file = FileFactory(file="media/not/a/real.file")
    assert file_admin.get_size(bad_file) == "0 bytes"


@pytest.mark.django_db
def test_fileadmin_image_list_api_view(client):
    file_1 = FileFactory(sample_png=True)
    file_2 = FileFactory(sample_png=True, alt_text="Alt text test")
    user = UserFactory()
    client.force_login(user)

    # Ensure non-staff members can't fetch it
    url = reverse("admin:media_file_image_list_api")
    response = client.get(url)
    assert response.status_code == 302
    assert response["Location"].startswith("/admin/login/")

    # Check underpermissioned staff users
    user.is_staff = True
    user.save()
    response = client.get(url)
    assert response.status_code == 403
    assert response.content == b"Forbidden"

    # Test with the correct permissions.
    user.user_permissions.add(Permission.objects.get(codename="view_file"))
    response = client.get(url)
    assert response.status_code == 200
    response_json = response.json()
    assert response_json[0]["url"] == f"/library/redirect/{file_2.pk}/"
    assert response_json[0]["title"] == file_2.title
    assert response_json[0]["altText"] == "Alt text test"

    assert response_json[1]["url"] == f"/library/redirect/{file_1.pk}/"
    assert response_json[1]["title"] == file_1.title
    assert response_json[1]["altText"] is None

    # Ensure that both the thumbnails & image URLs work.
    for item in response_json:
        for key in ["url", "thumbnail"]:
            # Ensure we're redirected to something...
            response = client.get(item[key])
            assert response.status_code == 302
            # ...which actually exists.
            response = client.get(response["Location"])
            assert response.status_code == 200


@pytest.mark.django_db
def test_fileadmin_image_upload_api_view(client):
    user = UserFactory()
    client.force_login(user)
    url = reverse("admin:media_file_image_upload_api")
    with open(data_file_path("1920x1080.png"), "rb") as fd:
        image_data = fd.read()
    data = {
        "file": SimpleUploadedFile(
            name="Sample PNG.png", content=image_data, content_type="image/png"
        ),
    }

    response = client.post(url, data=data)
    assert response.status_code == 302
    assert response["location"].startswith("/admin/login/")
    assert File.objects.count() == 0

    data["file"].seek(0)

    # Test staff with insufficient permission
    user.is_staff = True
    user.save()
    response = client.post(url, data=data)
    assert response.status_code == 403
    assert response.content == b"Forbidden"
    assert File.objects.count() == 0

    data["file"].seek(0)

    # give it the right permission, try again
    user.user_permissions.add(Permission.objects.get(codename="add_file"))
    response = client.post(url, data=data).json()
    assert response["success"] is True
    latest_file = File.objects.order_by("-id").first()
    assert latest_file.title == "Sample PNG"
    assert latest_file.alt_text == ""

    # Manually add alt text/title (the Trumbowyg uploader has one field for
    # "description" which can be used for both)
    data["file"].seek(0)
    data["alt"] = "Manual alt/title"
    response = client.post(url, data=data).json()
    assert response["success"] is True
    latest_file = File.objects.order_by("-id").first()
    assert latest_file.title == "Manual alt/title"
    assert latest_file.alt_text == "Manual alt/title"

    # Test branches that deal with a non-image
    data["file"] = SimpleUploadedFile(
        name="Text file.txt", content=b"Dear John,", content_type="text/plain"
    )
    response = client.post(url, data=data).json()
    assert response["success"] is False
    assert (
        response["detail"]["file"][0]["message"]
        == "Text file.txt does not appear to be an image file."
    )


@pytest.mark.django_db
def test_fileadmin_remove_label_action():
    file_admin = FileAdmin(File, AdminSite())

    label = LabelFactory()
    obj = FileFactory(empty=True)
    assert obj.labels.count() == 0

    obj.labels.add(label)
    assert obj.labels.count() == 1

    file_admin.remove_label_action(
        AdminRequestFactory().get("/"), File.objects.all(), label
    )
    assert obj.labels.count() == 0


@pytest.mark.django_db
def test_fileadmin_response_add():
    file_admin = FileAdmin(File, AdminSite())
    obj = FileFactory(empty=True)

    request = AdminRequestFactory().get("/")
    # Allow the messages framework to work.
    request.user = MockSuperUser()

    response = file_admin.response_add(request, obj)
    assert response.status_code == 302


@pytest.mark.django_db
def test_media_list_shows_stylesheet(client):
    """
    Ensure the stylesheet is correctly conditionally loaded on the media file
    list page depending on the MEDIA_LIST_GRID_VIEW setting.
    """
    client.force_login(UserFactory(superuser=True))

    for fancy_view in [True, False]:
        with override_settings(UNCMS={"MEDIA_LIST_GRID_VIEW": fancy_view}):
            response = client.get(reverse("admin:media_file_changelist"))
        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")
        assert (
            bool(
                soup.find(
                    "link",
                    attrs={
                        "rel": "stylesheet",
                        "href": "/static/media/css/media-list.css",
                    },
                )
            )
            is fancy_view
        )


@pytest.mark.django_db
def test_file_detail_conditionally_shows_fieldsets(client):
    def has_usage_fieldset(context):
        return any(
            fieldset[0] == "Usage" for fieldset in context["adminform"].fieldsets
        )

    client.force_login(UserFactory(superuser=True))

    response = client.get(reverse("admin:media_file_add"))
    assert response.status_code == 200
    assert has_usage_fieldset(response.context_data) is False

    file = FileFactory(minimal_gif=True)
    response = client.get(reverse("admin:media_file_change", args=[file.pk]))
    assert response.status_code == 200
    assert has_usage_fieldset(response.context_data) is True


@pytest.mark.django_db
def test_file_list_type_filter(client):
    def context_pks(context):
        return sorted([obj.pk for obj in context["cl"].result_list])

    client.force_login(UserFactory(superuser=True))

    sample_jpeg = FileFactory(sample_jpeg=True)
    sample_png = FileFactory(sample_png=True)
    sample_not_image = FileFactory(empty=True)

    url = reverse("admin:media_file_changelist")

    response = client.get(url)
    assert response.status_code == 200
    assert context_pks(response.context_data) == sorted(
        [sample_jpeg.pk, sample_png.pk, sample_not_image.pk]
    )

    response = client.get(url, {"filetype": "image"})
    assert response.status_code == 200
    assert context_pks(response.context_data) == sorted([sample_jpeg.pk, sample_png.pk])


@pytest.mark.django_db
def test_media_get_form(client):
    # Test the get_form override - rather than testing the function directly,
    # which is silly, ensure that the form in the context has the attributes
    # we are expecting.
    user = UserFactory(superuser=True)
    client.force_login(user)
    response = client.get(reverse("admin:media_file_add"))
    assert response.status_code == 200
    assert response.context_data["adminform"].form.user == user


@pytest.mark.django_db
@pytest.mark.parametrize("give_view_permission", [True, False])
def test_bulk_add_view_with_add_permission(client, give_view_permission):
    """
    Test that staff users with the correct permissions can see the bulk upload
    page.
    """
    permissions = ["media.add_file"]
    if give_view_permission:
        permissions.append("media.view_file")
    user = UserFactory(is_staff=True, permissions=permissions)
    client.force_login(user)
    url = reverse("admin:media_file_image_bulk_add")

    response = client.get(url)
    assert response.status_code == 200
    assert response.context["title"] == "Bulk upload"
    assert "opts" in response.context
    assert response.context["has_view_permission"] is give_view_permission
    assert response.context["upload_api_url"] == "/admin/media/file/bulk-upload-api/"


@pytest.mark.django_db
def test_bulk_add_view_non_staff(client):
    """
    Test that non-staff users should be redirected to the login page when
    accessing the bulk upload page.
    """
    user = UserFactory()
    client.force_login(user)

    response = client.get(reverse("admin:media_file_image_bulk_add"))
    assert response.status_code == 302
    assert response["Location"].startswith("/admin/login/")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "settings_overrides, user_permissions",
    [
        # User has the correct permissions, but bulk uploading is disabled.
        ({"UNCMS": {"MEDIA_BULK_UPLOAD_ENABLED": False}}, ["media.add_file"]),
        # Bulk uploading is disabled *and* user does not have the correct
        # permissions.
        ({"UNCMS": {"MEDIA_BULK_UPLOAD_ENABLED": False}}, []),
        # Bulk uploading is enabled, but user does not have the correct
        # permissions.
        ({"UNCMS": {}}, []),
    ],
)
def test_bulk_add_view_disabled(client, settings_overrides, user_permissions):
    """
    Test that the the bulk add view returns a 403 when bulk upload is disabled in
    settings or when the user does not have the correct permissions.
    """
    user = UserFactory(is_staff=True, permissions=user_permissions)
    client.force_login(user)

    with override_settings(**settings_overrides):
        response = client.get(reverse("admin:media_file_image_bulk_add"))
    assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("give_view_permission", [True, False])
@pytest.mark.parametrize("image_upload", [True, False])
@override_settings(UNCMS={"MEDIA_UPLOAD_ALLOWED_EXTENSIONS": ["txt"]})
def test_bulk_add_api_view(client, give_view_permission, image_upload):
    """
    Test successful file upload via the bulk upload API.
    """
    permissions = ["media.add_file"]
    if give_view_permission:
        permissions.append("media.view_file")

    user = UserFactory(is_staff=True, permissions=permissions)
    client.force_login(user)

    if image_upload:
        filename = "1920x1080.png"
    else:
        filename = "text-file.txt"

    with open(data_file_path(filename), "rb") as fd:
        data = {"file": fd}
        response = client.post(reverse("admin:media_file_bulk_upload_api"), data=data)

    assert response.status_code == 200

    latest_file = File.objects.order_by("-id").first()

    response_json = response.json()
    if image_upload:
        assert response_json["size"] == 7940
        assert response_json["sizeFormatted"] == "7.8\xa0KB"
        assert latest_file.title == "1920x1080"
        # Make sure the thumbnail URL is a redirect, which redirects to a
        # thing which exists.
        thumbnail_response = client.get(response_json["thumbnail"])
        assert thumbnail_response.status_code == 302
        assert client.get(thumbnail_response.headers["Location"]).status_code == 200
    else:
        assert response_json["size"] == 5
        assert response_json["sizeFormatted"] == "5\xa0bytes"
        assert latest_file.title == "text-file"
        assert response_json["thumbnail"] is None

    if give_view_permission:
        assert (
            response_json["adminUrl"] == f"/admin/media/file/{latest_file.pk}/change/"
        )
    else:
        assert "adminUrl" not in response_json

    assert File.objects.count() == 1
    assert list(latest_file.labels.values_list("name", flat=True)) == ["Bulk upload"]


@pytest.mark.django_db
def test_bulk_add_api_view_non_staff(client):
    """
    Test that non-staff users are redirected to login when accessing the bulk
    API upload view.
    """
    user = UserFactory()
    client.force_login(user)

    with open(data_file_path("1920x1080.png"), "rb") as fd:
        response = client.post(
            reverse("admin:media_file_bulk_upload_api"), data={"file": fd}
        )

    assert response.status_code == 302
    assert response["Location"].startswith("/admin/login/")
    assert File.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "settings_overrides, user_permissions",
    [
        # User has the correct permissions, but bulk uploading is disabled.
        ({"UNCMS": {"MEDIA_BULK_UPLOAD_ENABLED": False}}, ["media.add_file"]),
        # Bulk uploading is disabled *and* user does not have the correct
        # permissions.
        ({"UNCMS": {"MEDIA_BULK_UPLOAD_ENABLED": False}}, []),
        # Bulk uploading is enabled, but user does not have the correct
        # permissions.
        ({"UNCMS": {}}, []),
    ],
)
def test_bulk_add_api_view_staff_with_bulk_upload_not_allowed(
    client, settings_overrides, user_permissions
):
    """
    Test that we get a 403 on the bulk upload API in these cases:
    * when the user is a staff user without the add permission
    * when MEDIA_BULK_UPLOAD_ENABLED is False
    """
    user = UserFactory(is_staff=True, permissions=user_permissions)
    client.force_login(user)

    with override_settings(**settings_overrides), open(
        data_file_path("1920x1080.png"), "rb"
    ) as fd:
        response = client.post(
            reverse("admin:media_file_bulk_upload_api"), data={"file": fd}
        )

    assert response.status_code == 403
    assert response.content == b"Forbidden"
    assert File.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize("data", [{}, {"file": "not a file"}])
def test_bulk_add_api_view_missing_file(client, data):
    """
    Test bulk upload API view with missing `file` field. This branch is
    defensive and should never be seen in normal use.
    """
    user = UserFactory(is_staff=True, permissions=["media.add_file"])
    client.force_login(user)

    response = client.post(reverse("admin:media_file_bulk_upload_api"), data=data)
    assert response.status_code == 400
    assert response.json()["error"] == "This field is required."
