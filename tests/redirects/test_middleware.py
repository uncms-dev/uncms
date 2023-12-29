import pytest
from django.test import modify_settings

from uncms.redirects.models import Redirect
from uncms.testhelpers.factories import UserFactory


@modify_settings(
    MIDDLEWARE={
        "append": ["uncms.redirects.middleware.RedirectFallbackMiddleware"],
    }
)
@pytest.mark.django_db
def test_redirect_fallback_middleware_works(client):
    # Make sure that a redirect will kick in for a non-404.
    client.force_login(UserFactory(superuser=True))
    Redirect.objects.create(old_path="/admin/", new_path="/wat/")
    response = client.get("/admin/")
    assert response.status_code == 200

    url = "/example/"
    # sanity check
    response = client.get(url)
    assert response.status_code == 404

    redirect = Redirect.objects.create(old_path="/example/", new_path="/sample/")
    response = client.get(url)
    assert response.status_code == 301
    assert response["Location"] == "/sample/"

    # Test the "append forward slash" branch.
    response = client.get(url[:-1])
    assert response.status_code == 301
    assert response["Location"] == "/sample/"

    # Test the "remove forward slash" branch.
    redirect.old_path = "/example"
    redirect.save()

    response = client.get(url)
    assert response.status_code == 301
    assert response["Location"] == "/sample/"

    # we know this works, but check the "fall back to original response"
    # branch
    response = client.get("/wobble/")
    assert response.status_code == 404
