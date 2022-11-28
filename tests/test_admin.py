from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

from tests.testing_app.models import OnlineBaseModel
from uncms.admin import OnlineBaseAdmin


class AdminTest(TestCase):

    def setUp(self):
        factory = RequestFactory()
        self.request = factory.get('/')

        self.site = AdminSite()
        self.page_admin = OnlineBaseAdmin(OnlineBaseModel, self.site)

    def test_onlinebaseadmin_publish_selected(self):
        obj = OnlineBaseModel.objects.create(
            is_online=False,
        )

        self.assertFalse(obj.is_online)

        self.page_admin.publish_selected(self.request, OnlineBaseModel.objects.all())

        obj = OnlineBaseModel.objects.get(pk=obj.pk)
        self.assertTrue(obj.is_online)

    def test_onlinebaseadmin_unpublish_selected(self):
        obj = OnlineBaseModel.objects.create(
            is_online=True,
        )

        self.assertTrue(obj.is_online)

        self.page_admin.unpublish_selected(self.request, OnlineBaseModel.objects.all())

        obj = OnlineBaseModel.objects.get(pk=obj.pk)
        self.assertFalse(obj.is_online)
