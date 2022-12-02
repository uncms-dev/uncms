from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

from tests.testing_app.models import ModerationModel
from uncms.moderation.admin import ModerationAdminBase


class MockUser:
    pk = 1

    def __init__(self, permission):
        self.permission = permission

    def has_perm(self, perm):
        return self.permission


class TestModerationAdmin(TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.moderation_admin = ModerationAdminBase(ModerationModel, self.site)

        self.object = ModerationModel.objects.create()

        self.factory = RequestFactory()
        self.request = self.factory.get('/')

    def test_formfield_for_choice_field_has_permission(self):
        self.request.user = MockUser(True)

        formfield = self.moderation_admin.formfield_for_choice_field(
            self.object._meta.get_field('status'),
            self.request
        )

        self.assertListEqual(
            formfield.choices,
            [(1, 'Draft'), (2, 'Submitted for approval'), (3, 'Approved')]
        )

    def test_formfield_for_choice_field_has_no_permission(self):
        self.request.user = MockUser(False)

        formfield = self.moderation_admin.formfield_for_choice_field(
            self.object._meta.get_field('status'),
            self.request
        )

        self.assertListEqual(
            formfield.choices,
            [(1, 'Draft'), (2, 'Submitted for approval')]
        )