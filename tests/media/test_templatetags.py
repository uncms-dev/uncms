import pytest
from bs4 import BeautifulSoup
from sorl.thumbnail.images import ImageFile

from tests.media.factories import MinimalGIFFileFactory, SamplePNGFileFactory
from uncms.media.templatetags.media import render_image, thumbnail


@pytest.mark.django_db
def test_thumbnail():
    file = MinimalGIFFileFactory()
    thumb = thumbnail(file.file, '100')
    assert isinstance(thumb, ImageFile)


@pytest.mark.django_db
def test_render_image(client):
    # Deeper tests will be in File.render_multi_format - just do a basic test
    # to ensure it's outputting something that looks like HTML with a
    # non-broken image
    file = SamplePNGFileFactory()
    html = render_image(file, width=600, height=400)
    soup = BeautifulSoup(html, 'html.parser')

    url = soup.find('source')['srcset'].split()[0]
    response = client.get(url)
    assert response.status_code == 302

    response = client.get(response['Location'])
    assert response.status_code == 200
