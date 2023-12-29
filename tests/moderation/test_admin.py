import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from tests.mocks import MockRequestUser
from tests.testing_app.models import ModerationModel
from uncms.moderation.admin import ModerationAdminBase


@pytest.mark.django_db
def test_formfield_for_choice_field_has_permission():
    moderation_admin = ModerationAdminBase(ModerationModel, AdminSite())
    obj = ModerationModel.objects.create()
    request = RequestFactory().get("/")
    request.user = MockRequestUser(
        is_authenticated=True, permission=True, is_staff=True
    )

    formfield = moderation_admin.formfield_for_choice_field(
        obj._meta.get_field("status"), request
    )

    assert formfield.choices == [
        (1, "Draft"),
        (2, "Submitted for approval"),
        (3, "Approved"),
    ]


@pytest.mark.django_db
def test_formfield_for_choice_field_has_no_permission():
    moderation_admin = ModerationAdminBase(ModerationModel, AdminSite())
    obj = ModerationModel.objects.create()
    request = RequestFactory().get("/")
    request.user = MockRequestUser(
        is_authenticated=True, permission=False, is_staff=True
    )

    formfield = moderation_admin.formfield_for_choice_field(
        obj._meta.get_field("status"), request
    )

    assert formfield.choices == [(1, "Draft"), (2, "Submitted for approval")]
