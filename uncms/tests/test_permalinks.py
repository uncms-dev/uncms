from django import urls
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from uncms.apps.testing_models.models import PermalinksModel
from uncms.permalinks import PermalinkError, expand, resolve


class PermalinksTest(TestCase):

    def test_resolve(self):
        obj = PermalinksModel.objects.create()

        url = resolve('/r/{}-{}/'.format(
            ContentType.objects.get_for_model(PermalinksModel).pk,
            obj.pk
        ))

        self.assertEqual(url, obj)

        with self.assertRaises(PermalinkError):
            # A valid URL, but not a permalink.
            resolve('/admin/')

        original_urlconf = urls.get_urlconf()
        with self.assertRaises(PermalinkError):
            urls.set_urlconf('uncms.tests.urls')
            resolve('/r/')

        urls.set_urlconf(original_urlconf)

    def test_expand(self):
        obj = PermalinksModel.objects.create()

        self.assertEqual(obj.__str__(), 'Foo')

        url = expand('/r/{}-{}/'.format(
            ContentType.objects.get_for_model(PermalinksModel).pk,
            obj.pk
        ))

        self.assertEqual(url, '/foo/')
