import pytest
from bs4 import BeautifulSoup

from tests.media.factories import SamplePNGFileFactory
from uncms.media.templatetags.uncms_images import image


@pytest.mark.django_db
def test_image(client):
    # Deeper tests will be in File.render_multi_format - just do a basic test
    # to ensure it's outputting something that looks like HTML with a
    # non-broken image
    file = SamplePNGFileFactory()
    html = image(file, width=600, height=400)
    soup = BeautifulSoup(html, 'html.parser')

    url = soup.find('source')['srcset'].split()[0]
    response = client.get(url)
    assert response.status_code == 302

    response = client.get(response['Location'])
    assert response.status_code == 200
