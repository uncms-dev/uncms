from django.contrib.admin.sites import AdminSite
from django.test import TestCase
from django.urls import reverse

from tests.testing_app.models import (
    UsageContentBaseModel,
    UsageContentBaseModelInline,
    UsageModelOne,
    UsageModelOneInline,
    UsageModelTwo,
)
from uncms.admin import get_related_objects_admin_urls
from uncms.testhelpers.factories.media import MinimalGIFFileFactory
from uncms.testhelpers.factories.pages import PageFactory


class TestFileUsedOn(TestCase):
    maxDiff = 2000

    def clear_image_references(self, instances):
        # Clear out the old images from the previous test to esnure
        # that they do not interfere.
        for instance in instances:
            if hasattr(instance, "image"):
                instance.image = None
                instance.save()

    def setUp(self):
        self.site = AdminSite(name="test_admin")

        self.test_file = MinimalGIFFileFactory()

        self.other_test_file = MinimalGIFFileFactory()

        self.test_model_1a = UsageModelOne.objects.create(
            image=self.test_file,
        )

        self.test_model_1b = UsageModelOne.objects.create(
            image=self.test_file,
        )

        self.test_model_1a_other = UsageModelOne.objects.create(
            image=self.other_test_file
        )

        self.test_model_2a_other = UsageModelTwo.objects.create(
            image=self.other_test_file
        )

        self.test_model_2a = UsageModelTwo.objects.create(
            image=self.test_file,
        )

        # We will define these ourselves later
        self.test_page_model = None
        self.test_content_base_inline = None
        self.test_content_base = None

    def tearDown(self):
        self.test_file.file.delete(False)
        self.other_test_file.file.delete(False)
        self.test_file.delete()
        self.other_test_file.delete()

        self.test_model_1a.delete()
        self.test_model_1b.delete()
        self.test_model_2a.delete()

        if self.test_content_base_inline:
            self.test_content_base_inline.delete()
            self.test_page_model.delete()

    def test_get_related_objects_admin_urls_from_models_with_image(self):
        # We have an instance of File (eg: self.test_file)
        # We have a Model with an ImageRefField (eg: self.test_model_1a)
        # We need to check that we can get the expected related objects when passing the file reference to get_related_objects_admin_urls()
        expected_outcome = [
            {
                "title": str(obj),
                "model_name": obj._meta.verbose_name,
                "admin_url": reverse(
                    f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
                    args=[obj.pk],
                ),
            }
            for obj in [self.test_model_1a, self.test_model_1b, self.test_model_2a]
        ]

        self.assertEqual(
            get_related_objects_admin_urls(self.test_file), expected_outcome
        )

    def test_get_related_objects_admin_urls_from_models_with_other_image(self):
        expected_outcome = [
            {
                "title": str(obj),
                "model_name": obj._meta.verbose_name,
                "admin_url": reverse(
                    f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
                    args=[obj.pk],
                ),
            }
            for obj in [self.test_model_1a_other, self.test_model_2a_other]
        ]

        self.assertEqual(
            get_related_objects_admin_urls(self.other_test_file), expected_outcome
        )

    def test_get_related_objects_admin_urls_from_contentbase_with_image(self):
        self.test_page_model = PageFactory(
            content=UsageContentBaseModel(
                image=self.test_file,
            ),
        )

        self.clear_image_references(
            [self.test_model_1a, self.test_model_1b, self.test_model_2a]
        )

        expected_outcome = [
            {
                "title": str(self.test_page_model.content),
                "model_name": self.test_page_model.content._meta.verbose_name,
                "admin_url": reverse(
                    f"admin:{self.test_page_model._meta.app_label}_{self.test_page_model._meta.model_name}_change",
                    args=[self.test_page_model.pk],
                ),
            },
        ]

        self.assertEqual(
            get_related_objects_admin_urls(self.test_file), expected_outcome
        )

    def test_get_related_objects_from_contentbase_inline_with_image(self):
        self.test_page_model = PageFactory(
            content=UsageContentBaseModel(),
        )

        self.test_content_base_inline = UsageContentBaseModelInline.objects.create(
            page=self.test_page_model,
            image=self.test_file,
        )

        self.clear_image_references(
            [self.test_model_1a, self.test_model_1b, self.test_model_2a]
        )

        expected_outcome = [
            {
                "title": str(self.test_content_base_inline),
                "model_name": self.test_content_base_inline._meta.verbose_name,
                "admin_url": reverse(
                    f"admin:{self.test_page_model._meta.app_label}_{self.test_page_model._meta.model_name}_change",
                    args=[self.test_page_model.pk],
                ),
            }
        ]

        self.assertEqual(
            get_related_objects_admin_urls(self.test_file), expected_outcome
        )

    def test_get_related_objects_admin_urls_from_model_inline_with_image(self):
        self.test_page_model = PageFactory(
            content=UsageContentBaseModel(),
        )

        test_model_1a_inline = UsageModelOneInline.objects.create(
            parent=self.test_model_1a, image=self.test_file
        )

        self.clear_image_references(
            [self.test_model_1a, self.test_model_1b, self.test_model_2a]
        )

        expected_outcome = [
            {
                "title": str(test_model_1a_inline),
                "model_name": test_model_1a_inline._meta.verbose_name,
                "admin_url": reverse(
                    f"admin:{self.test_model_1a._meta.app_label}_{self.test_model_1a._meta.model_name}_change",
                    args=[self.test_model_1a.pk],
                ),
            },
        ]

        self.assertEqual(
            get_related_objects_admin_urls(self.test_file), expected_outcome
        )
