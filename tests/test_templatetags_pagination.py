from django.http import Http404
from django.test import RequestFactory, TestCase

from uncms.templatetags.uncms_pagination import (
    paginate,
    pagination,
    pagination_url,
)


class Object:
    paginator = None


class PaginationTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/')

    def test_paginate(self):
        paginate_response = paginate({'request': self.request}, [])
        self.assertEqual(repr(paginate_response), '<Page 1 of 1>')

        with self.assertRaises(Http404):
            self.request = self.factory.get('/?page=2')
            paginate({'request': self.request}, [])

    def test_pagination(self):
        # pylint:disable=attribute-defined-outside-init
        obj = Object()
        obj.has_other_pages = lambda: False
        pagination({'request': self.request}, obj)

    def test_pagination_url(self):
        for request in [self.factory.get('/'), self.factory.get('/?page=9001')]:
            self.assertEqual(pagination_url({'request': request}, 1), '/')
            self.assertEqual(pagination_url({'request': request}, 2), '/?page=2')
