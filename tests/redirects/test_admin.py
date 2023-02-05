from io import BytesIO

import pytest
from bs4 import BeautifulSoup
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, override_settings
from django.urls import reverse

from tests.factories import UserFactory
from tests.media.factories import MINIMAL_GIF_DATA
from tests.redirects.helpers import generate_csv
from uncms.redirects.admin import RedirectAdmin
from uncms.redirects.forms import RedirectImportForm
from uncms.redirects.models import Redirect

IMPORT_PERMISSIONS = ['redirects.add_redirect', 'redirects.change_redirect']


@pytest.mark.django_db
def test_redirectadmin_change(admin_client):
    # "real" world test to make sure that the form isn't broken with and
    # without an object
    response = admin_client.get(reverse('admin:redirects_redirect_add'))
    assert response.status_code == 200

    redirect = Redirect.objects.create(old_path='/example/', new_path='/sample/')
    response = admin_client.get(reverse('admin:redirects_redirect_change', args=[redirect.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_redirectadmin_get_form(admin_client):
    # testing get_form directly is nonsense, because I actually care about
    # what the admin form is doing, so test that by poking around the context
    # data in the response
    response = admin_client.get(reverse('admin:redirects_redirect_add'))
    assert response.status_code == 200
    form = response.context_data['adminform'].form
    assert list(form.fields) == ['type', 'old_path', 'new_path']

    with override_settings(UNCMS={'REGEX_REDIRECTS': True}):
        response = admin_client.get(reverse('admin:redirects_redirect_add'))
    assert response.status_code == 200
    form = response.context_data['adminform'].form
    assert list(form.fields) == ['type', 'old_path', 'new_path', 'regular_expression', 'test_path']


@pytest.mark.django_db
def test_redirectadmin_list(admin_client):
    # basic check to make sure nothing is broken when no redirects are created
    response = admin_client.get(reverse('admin:redirects_redirect_changelist'))
    assert response.status_code == 200

    # Make sure it's not broken with existing objects, and check the
    # `list_display` is OK.
    for i in range(3):
        Redirect.objects.create(old_path=f'/example/{i}/', new_path='/sample/{i}/')
    response = admin_client.get(reverse('admin:redirects_redirect_changelist'))
    assert response.status_code == 200
    assert response.context_data['cl'].list_display == ['action_checkbox', 'old_path', 'new_path', 'type', 'test_redirect']

    # Make sure it changes when regular expression redirects are enabled (and
    # also make sure it's not throwing an exception)
    with override_settings(UNCMS={'REGEX_REDIRECTS': True}):
        response = admin_client.get(reverse('admin:redirects_redirect_changelist'))
    assert response.status_code == 200
    assert response.context_data['cl'].list_display == ['action_checkbox', 'old_path', 'new_path', 'regular_expression', 'type', 'test_redirect']


@pytest.mark.django_db
def test_redirectadmin_media(admin_client):
    # Ensure that our JS is loaded into the add form.
    response = admin_client.get(reverse('admin:redirects_redirect_add'))
    assert response.status_code == 200
    soup = BeautifulSoup(response.content, 'html.parser')

    scripts = [
        script['src'] for script in soup.find_all('script')
        if script.get('src', '').endswith('uncms/js/redirect-fields.js')
    ]
    assert len(scripts) == 1


@pytest.mark.django_db
def test_redirectadmin_test_redirect():
    def get_link(text):
        return BeautifulSoup(text, 'html.parser').find('a')['href']
    redirect_admin = RedirectAdmin(Redirect, AdminSite())

    obj = Redirect(old_path='/example/', new_path='/sample/')
    assert get_link(redirect_admin.test_redirect(obj)) == '/example/'

    obj = Redirect(old_path='/example/(.*)/', new_path=r'/sample/\1/', test_path='/example/wat/', regular_expression=True)
    assert get_link(redirect_admin.test_redirect(obj)) == '/example/wat/'


@pytest.mark.django_db
@pytest.mark.parametrize('user_permissions, expect_enabled', [
    ([], False),
    ([IMPORT_PERMISSIONS[0]], False),
    ([IMPORT_PERMISSIONS[1]], False),
    (IMPORT_PERMISSIONS, True),
])
def test_redirectadmin_is_import_enabled(user_permissions, expect_enabled):
    redirect_admin = RedirectAdmin(Redirect, AdminSite())

    request = RequestFactory().get('/')
    request.user = UserFactory(is_staff=True, permissions=user_permissions)
    assert redirect_admin.is_import_enabled(request) is expect_enabled

    with override_settings(UNCMS={'REDIRECTS_CSV_IMPORT_ENABLED': False}):
        assert redirect_admin.is_import_enabled(request) is False


@pytest.mark.django_db
def test_redirectadmin_import_csv_view(client):
    def submit_button_text(soup):
        button = soup.find('input', type='submit')
        return button['value']

    url = reverse('admin:redirects_redirect_import_csv')
    # paranoid sanity check
    response = client.get(url)
    assert response.status_code == 302
    assert response['Location'].startswith('/admin/login/')

    client.force_login(UserFactory(is_staff=True, permissions=IMPORT_PERMISSIONS))

    # Check the "is enabled" branch
    with override_settings(UNCMS={'REDIRECTS_CSV_IMPORT_ENABLED': False}):
        response = client.get(url)
        assert response.status_code == 404

    response = client.get(url)
    assert response.status_code == 200
    # just check that something looking like a file input is in the response
    soup = BeautifulSoup(response.content, 'html.parser')
    assert soup.find('input', type='file')
    assert submit_button_text(soup) == 'Check file'

    # Try posting some binary to cover a branch in RedirectImportForm and
    # cause the unusual case where validation fails.
    response = client.post(url, {'csv_file': BytesIO(MINIMAL_GIF_DATA)})
    assert response.status_code == 200
    assert 'probably a binary file' in response.context['form'].errors['csv_file'][0]
    assert response.context['form'].__class__ == RedirectImportForm
    assert submit_button_text(BeautifulSoup(response.content, 'html.parser')) == 'Check file'

    csv_file = generate_csv([
        ('From', 'To'),
        ('/example/', '/sample/'),
        ('/example2/', '/sample2/'),
    ])
    # Check the "show confirmation screen" branch.
    response = client.post(url, data={'csv_file': csv_file})
    assert response.status_code == 200
    soup = BeautifulSoup(response.content, 'html.parser')
    assert submit_button_text(soup) == 'Ignore errors and import'

    response = client.post(url, data={
        # Ensure we're posting exactly the data that is in the rendered form.
        # (This is borderline integration test.)
        'csv_data': soup.find('textarea', attrs={'name': 'csv_data'}).get_text(),
        'filename': soup.find('input', attrs={'name': 'filename'})['value'],
    })
    assert response.status_code == 302
    # Check it's redirecting somewhere meaningful
    assert client.get(response['location']).status_code == 200

    # Make sure that something has been created.
    assert list(Redirect.objects.values_list('old_path', 'new_path')) == [
        ('/example/', '/sample/'),
        ('/example2/', '/sample2/'),
    ]
