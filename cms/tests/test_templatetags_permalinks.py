from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, TestCase

from cms.templatetags.permalinks import get_permalink_absolute, permalink
from cms.apps.testing_models.models import PermalinksModel


class PermalinkTest(TestCase):

    def setUp(self):
        self.obj = PermalinksModel.objects.create()
        factory = RequestFactory()
        self.request = factory.get('/')

    def test_permalink(self):

        self.assertEqual(permalink(self.obj), '/r/{}-{}/'.format(
            ContentType.objects.get_for_model(PermalinksModel).pk,
            self.obj.pk
        ))

    def test_get_permalink_absolute(self):
        context = {
            'request': self.request
        }

        self.assertEqual(
            get_permalink_absolute(context, self.obj),
            'http://testserver/r/{}-{}/'.format(
                ContentType.objects.get_for_model(PermalinksModel).pk,
                self.obj.pk
            )
        )
