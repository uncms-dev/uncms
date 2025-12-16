import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.urls import reverse

from tests.testing_app.admin import InlineWithFkNameInline, InlineWithMultipleFkInline
from tests.testing_app.models import (
    InlineWithFkNameModel,
    InlineWithMultipleFkModel,
    NotRegisteredInAdminModel,
    OnlineBaseModel,
    PageBaseModel,
    UsageContentBaseModel,
    UsageContentBaseModelInline,
    UsageModelOne,
    UsageModelOneInline,
    UsageModelTwo,
)
from uncms.admin import (
    OnlineBaseAdmin,
    check_inline_for_admin_url,
    get_related_objects_admin_urls,
)
from uncms.testhelpers.factories import UserFactory
from uncms.testhelpers.factories.media import FileFactory
from uncms.testhelpers.factories.pages import PageFactory

# pylint:disable=redefined-outer-name
# ^ because of fixtures defined in this module


@pytest.fixture
def test_file(db):
    file_obj = FileFactory(minimal_gif=True)
    yield file_obj
    file_obj.file.delete(False)
    file_obj.delete()


@pytest.fixture
def other_test_file(db):
    file_obj = FileFactory(minimal_gif=True)
    yield file_obj
    file_obj.file.delete(False)
    file_obj.delete()


@pytest.fixture
def usage_models(db, test_file, other_test_file):
    test_model_1a = UsageModelOne.objects.create(image=test_file)
    test_model_1b = UsageModelOne.objects.create(image=test_file)
    test_model_1a_other = UsageModelOne.objects.create(image=other_test_file)
    test_model_2a_other = UsageModelTwo.objects.create(image=other_test_file)
    test_model_2a = UsageModelTwo.objects.create(image=test_file)

    return {
        "test_model_1a": test_model_1a,
        "test_model_1b": test_model_1b,
        "test_model_1a_other": test_model_1a_other,
        "test_model_2a_other": test_model_2a_other,
        "test_model_2a": test_model_2a,
    }


@pytest.mark.django_db
def test_onlinebaseadmin_publish_selected():
    page_admin = OnlineBaseAdmin(OnlineBaseModel, AdminSite())

    obj = OnlineBaseModel.objects.create(
        is_online=False,
    )
    assert obj.is_online is False

    page_admin.publish_selected(
        RequestFactory().get("/"), OnlineBaseModel.objects.all()
    )

    obj.refresh_from_db()
    assert obj.is_online is True


@pytest.mark.django_db
def test_onlinebaseadmin_unpublish_selected():
    page_admin = OnlineBaseAdmin(OnlineBaseModel, AdminSite())

    obj = OnlineBaseModel.objects.create(
        is_online=True,
    )

    assert obj.is_online is True

    page_admin.unpublish_selected(
        RequestFactory().get("/"), OnlineBaseModel.objects.all()
    )

    obj.refresh_from_db()
    assert obj.is_online is False


@pytest.mark.django_db
def test_quality_control_filter(client):
    client.force_login(UserFactory(superuser=True))
    image = FileFactory(minimal_gif=True)

    defaults = {
        "browser_title": "Browser title",
        "meta_description": "Meta description",
        "og_description": "OG description",
        "og_image": image,
    }

    overrides = {
        "no-meta-description": [{"meta_description": ""}],
        "no-browser-title": [{"browser_title": ""}],
        "incomplete-opengraph-fields": [{"og_description": ""}],
    }

    objects = {}

    for key, value in overrides.items():
        objects[key] = []
        for fields in value:
            objects[key].append(
                PageBaseModel.objects.create(**dict(defaults, **fields))
            )
    for key, objs in objects.items():
        # There's a bug in (probably) RequestFactory wherein passing one of
        # its requests to a SimpleListFilter ends up with only the last letter
        # of a GET parameter's value being passed to `queryset`. Life's too
        # short to work it out, and anyway getting the admin page directly is
        # probably a better test.
        response = client.get(
            reverse("admin:testing_app_pagebasemodel_changelist"),
            data={"seo_quality_control": key},
        )
        assert response.status_code == 200
        ids = sorted(obj.id for obj in response.context["cl"].result_list)
        assert ids == sorted(obj.id for obj in objs)


@pytest.mark.django_db
def test_check_inline_for_admin_url_with_fk_name_no_reverse_match():
    """
    Tests the branch for NoReverseMatch when fk_name is set but parent has no
    admin.
    """
    # Create a parent that doesn't have an admin registered
    parent = NotRegisteredInAdminModel.objects.create()

    # Create an inline object that has a FK to the unregistered parent
    inline_obj = InlineWithFkNameModel.objects.create(not_registered_parent=parent)

    # The inline has fk_name set, and the parent exists but has no admin
    # We pass UsageModelOne as the parent parameter (not NotRegisteredInAdminModel)
    # so the FK loop won't match and we test only the fk_name block (lines 43-50)
    result = check_inline_for_admin_url(
        inline_obj, InlineWithFkNameInline, UsageModelOne
    )

    # Should return None after catching NoReverseMatch in the fk_name block
    assert result is None


@pytest.mark.django_db
def test_check_inline_for_admin_url_with_null_fk():
    """
    Tests the branch where FK field value is None.

    This test was written with AI assistance.
    """
    # Create an inline object with null FKs. This model has two FK fields:
    # parent (to UsageModelOne) and other_parent (to UsageModelTwo) The loop
    # will process other_parent first (doesn't match UsageModelOne). Then it
    # processes parent (matches UsageModelOne but value is None).
    inline_obj = InlineWithMultipleFkModel.objects.create(
        parent=None, other_parent=None
    )

    # Call check_inline_for_admin_url with UsageModelOne as parent
    result = check_inline_for_admin_url(
        inline_obj, InlineWithMultipleFkInline, UsageModelOne
    )

    # Should return None because the FK field is null
    assert result is None


def test_get_related_objects_admin_urls_from_models_with_image(test_file, usage_models):
    assert get_related_objects_admin_urls(test_file) == [
        {
            "title": str(obj),
            "model_name": obj._meta.verbose_name,
            "admin_url": reverse(
                f"admin:testing_app_{obj._meta.model_name}_change",
                args=[obj.pk],
            ),
        }
        for obj in [
            usage_models["test_model_1a"],
            usage_models["test_model_1b"],
            usage_models["test_model_2a"],
        ]
    ]


def test_get_related_objects_admin_urls_from_models_with_other_image(
    other_test_file, usage_models
):
    assert get_related_objects_admin_urls(other_test_file) == [
        {
            "title": str(obj),
            "model_name": obj._meta.verbose_name,
            "admin_url": reverse(
                f"admin:testing_app_{obj._meta.model_name}_change",
                args=[obj.pk],
            ),
        }
        for obj in [
            usage_models["test_model_1a_other"],
            usage_models["test_model_2a_other"],
        ]
    ]


def test_get_related_objects_admin_urls_from_contentbase_with_image(test_file):
    test_page_model = PageFactory(
        content=UsageContentBaseModel(
            image=test_file,
        ),
    )

    assert get_related_objects_admin_urls(test_file) == [
        {
            "title": str(test_page_model.content),
            "model_name": test_page_model.content._meta.verbose_name,
            "admin_url": reverse("admin:pages_page_change", args=[test_page_model.pk]),
        },
    ]


def test_get_related_objects_from_contentbase_inline_with_image(test_file):
    test_page_model = PageFactory(
        content=UsageContentBaseModel(),
    )

    test_content_base_inline = UsageContentBaseModelInline.objects.create(
        page=test_page_model,
        image=test_file,
    )

    assert get_related_objects_admin_urls(test_file) == [
        {
            "title": str(test_content_base_inline),
            "model_name": test_content_base_inline._meta.verbose_name,
            "admin_url": reverse("admin:pages_page_change", args=[test_page_model.pk]),
        }
    ]


def test_get_related_objects_admin_urls_from_model_inline_with_image(test_file):
    test_model_1a = UsageModelOne.objects.create()
    test_model_1a_inline = UsageModelOneInline.objects.create(
        parent=test_model_1a, image=test_file
    )

    assert get_related_objects_admin_urls(test_file) == [
        {
            "title": str(test_model_1a_inline),
            "model_name": test_model_1a_inline._meta.verbose_name,
            "admin_url": reverse(
                "admin:testing_app_usagemodelone_change",
                args=[test_model_1a.pk],
            ),
        },
    ]
