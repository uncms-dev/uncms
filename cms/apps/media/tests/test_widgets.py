import pytest
from bs4 import BeautifulSoup
from django.contrib import admin

from cms.apps.media.tests.factories import (
    EmptyFileFactory,
    SamplePNGFileFactory,
)
from cms.apps.media.widgets import ImageThumbnailWidget
from cms.apps.testing_models.models import ImageFieldModel


@pytest.mark.django_db
def test_raw_id_widget_rendering(client):
    def get_img(html):
        soup = BeautifulSoup(html, features='html.parser')
        return soup.find('img')

    image = SamplePNGFileFactory()
    empty_file = EmptyFileFactory()
    widget = ImageThumbnailWidget(rel=ImageFieldModel._meta.get_field('image').remote_field, admin_site=admin.site)

    # No value or a broken file should not render a thumbnail.
    assert not get_img(widget.render(name='image', value=None))
    assert not get_img(widget.render(name='image', value=empty_file.pk))

    # But a real image should! Let's make sure it renders and is an actual
    # image.
    image = get_img(widget.render(name='image', value=image.pk))
    assert image
    assert client.get(image['src']).status_code == 200
