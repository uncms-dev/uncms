import pytest
from django.core.exceptions import ValidationError

from tests.testing_app.models import LinkFieldModel
from uncms.models.fields import (
    LinkResolutionError,
    link_validator,
    resolve_link,
)


def test_resolve_link():
    with pytest.raises(LinkResolutionError):
        resolve_link('')

    with pytest.raises(LinkResolutionError):
        resolve_link('http://[a')


def test_link_validator():
    with pytest.raises(ValidationError):
        link_validator('')

    with pytest.raises(ValidationError):
        link_validator('http://[a')

    link_validator('https://www.example.com')


@pytest.mark.django_db
def test_linkfield_get_xxx_resolved():
    obj = LinkFieldModel.objects.create(
        link='https://example.com'
    )

    assert obj.get_link_resolved() == 'https://example.com'

    obj = LinkFieldModel.objects.create(
        link='https://[a'
    )

    assert obj.get_link_resolved() == 'https://[a'
