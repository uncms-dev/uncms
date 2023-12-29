import pytest
from bs4 import BeautifulSoup

from uncms.jinja2_environment.media import render_image
from uncms.media.templatetags.uncms_images import image
from uncms.testhelpers.factories.media import SamplePNGFileFactory


@pytest.mark.django_db
# test both Jinja2 and vanilla Django
@pytest.mark.parametrize("test_func", [image, render_image])
def test_image(client, test_func):
    # Deeper tests will be in File.render_multi_format - just do a basic test
    # to ensure it's outputting something that looks like HTML with a
    # non-broken image
    file = SamplePNGFileFactory()
    html = test_func(file, width=600, height=400)
    soup = BeautifulSoup(html, "html.parser")

    url = soup.find("source")["srcset"].split()[0]
    response = client.get(url)
    assert response.status_code == 302

    response = client.get(response["Location"])
    assert response.status_code == 200
