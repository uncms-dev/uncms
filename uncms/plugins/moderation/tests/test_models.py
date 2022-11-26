from django.test import TestCase

from uncms.apps.testing_models.models import ModerationModel
from uncms.models import publication_manager


class TestModerationModels(TestCase):

    def setUp(self):
        ModerationModel.objects.create(status=1)
        ModerationModel.objects.create(status=2)
        ModerationModel.objects.create(status=3)

    def test_moderation_manager_select_published(self):
        with publication_manager.select_published(True):
            self.assertEqual(ModerationModel.objects.count(), 1)

        with publication_manager.select_published(False):
            self.assertEqual(ModerationModel.objects.count(), 3)
