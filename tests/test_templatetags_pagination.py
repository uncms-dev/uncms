from unittest.mock import MagicMock

import pytest
from django.http import Http404
from django.test import RequestFactory

from uncms.templatetags.uncms_pagination import (
    paginate,
    pagination,
    pagination_url,
)


def test_paginate():
    rf = RequestFactory()
    paginate_response = paginate({'request': rf.get('/')}, [])
    assert repr(paginate_response) == '<Page 1 of 1>'

    with pytest.raises(Http404):
        paginate({'request': rf.get('/?page=2')}, [])


def test_pagination():
    request = RequestFactory().get('/')
    obj = MagicMock(
        has_other_pages=lambda: False,
        paginator=MagicMock(
            page_range=[],
        ),
    )
    pagination({'request': request}, obj)


def test_pagination_url():
    rf = RequestFactory()
    for request in [rf.get('/'), rf.get('/?page=9001')]:
        assert pagination_url({'request': request}, 1) == '/'
        assert pagination_url({'request': request}, 2) == '/?page=2'
