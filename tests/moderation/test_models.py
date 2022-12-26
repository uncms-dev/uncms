import pytest

from tests.testing_app.models import ModerationModel
from uncms.models import publication_manager


@pytest.mark.django_db
def test_moderation_manager_select_published():
    ModerationModel.objects.create(status=1)
    ModerationModel.objects.create(status=2)
    ModerationModel.objects.create(status=3)

    with publication_manager.select_published(True):
        assert ModerationModel.objects.count() == 1

    with publication_manager.select_published(False):
        assert ModerationModel.objects.count() == 3
