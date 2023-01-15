# pylint:disable=duplicate-code
import base64

import pytest
from bs4 import BeautifulSoup
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.views.main import IS_POPUP_VAR
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404
from django.test.utils import override_settings
from django.urls import reverse

from tests.factories import AdminRequestFactory, UserFactory
from tests.media.factories import (
    EmptyFileFactory,
    FileFactory,
    LabelFactory,
    MinimalGIFFileFactory,
    SampleJPEGFileFactory,
    SamplePNGFileFactory,
    data_file_path,
)
from tests.mocks import MockSuperUser
from uncms.media.admin import FileAdmin
from uncms.media.models import File


@pytest.mark.django_db
def test_fileadminbase_changelist_view():
    file_admin = FileAdmin(File, AdminSite())
    request = AdminRequestFactory().get('/')
    request.user = MockSuperUser()
    view = file_admin.changelist_view(request)

    assert view.status_code == 200
    assert view.template_name == 'admin/media/file/change_list.html'
    assert 'foo' not in view.context_data

    view = file_admin.changelist_view(request, extra_context={'foo': 'bar'})
    assert view.status_code == 200
    assert view.template_name == 'admin/media/file/change_list.html'
    assert 'foo' in view.context_data


@pytest.mark.django_db
def test_fileadmin_add_label_action():
    file_admin = FileAdmin(File, AdminSite())

    obj = EmptyFileFactory()
    label = LabelFactory()
    assert obj.labels.count() == 0

    file_admin.add_label_action(AdminRequestFactory().get('/'), File.objects.all(), label)
    assert obj.labels.count() == 1


@pytest.mark.django_db
def test_fileadmin_get_actions():
    site = AdminSite()
    rf = AdminRequestFactory()
    file_admin = FileAdmin(File, site)
    LabelFactory()

    request = rf.get('/')
    request.user = MockSuperUser()
    actions = file_admin.get_actions(request)
    assert len(actions) == 3

    request = rf.get('/?{}'.format(IS_POPUP_VAR))
    request.user = MockSuperUser()
    actions = file_admin.get_actions(request)
    assert len(actions) == 0


@pytest.mark.django_db
def test_fileadmin_get_preview():
    file_admin = FileAdmin(File, AdminSite())

    obj = SamplePNGFileFactory(title='Kittens')
    preview = file_admin.get_preview(obj)
    # We can't do an `assertEqual` here as the generated src URL is dynamic.
    assert preview.startswith(
        f'<img class="uncms-thumbnail" uncms:permalink="/library/redirect/{obj.pk}/"'
    )
    assert preview.endswith('width="200" height="112" alt="" title="Kittens"/>')

    obj = FileFactory(file='media/not/a/real.png')
    preview = file_admin.get_preview(obj)
    assert preview.startswith('<img class="uncms-thumbnail"')

    obj = FileFactory(title="Canary", file='media/not/a/real.file')
    preview = file_admin.get_preview(obj)
    assert preview == f'<img class="uncms-fallback-icon" uncms:permalink="/library/redirect/{obj.pk}/" src="/static/media/img/text-x-generic-template.png" width="56" height="66" alt="" title="Canary"/>'


@pytest.mark.django_db
def test_fileadmin_get_size():
    file_admin = FileAdmin(File, AdminSite())

    seven_bytes = FileFactory(file__data='abcdefg')
    assert file_admin.get_size(seven_bytes) == '7\xa0bytes'

    bad_file = FileFactory(file='media/not/a/real.file')
    assert file_admin.get_size(bad_file) == '0 bytes'


def test_fileadmin_remote_view(live_server):
    file_admin = FileAdmin(File, AdminSite())
    obj = EmptyFileFactory()

    request = AdminRequestFactory().get('/')
    request.user = MockSuperUser

    request.user = MockSuperUser()
    response = file_admin.remote_view(request, obj)
    # 405: Method not allowed. We have to POST to this view.
    assert response.status_code == 405

    request.method = 'POST'

    # No URL supplied.
    with pytest.raises(Http404):
        file_admin.remote_view(request, obj.pk)

    # No permissions.
    request.user.has_perm = lambda x: False

    response = file_admin.remote_view(request, obj.pk)
    assert response.status_code == 403

    request.user = MockSuperUser()
    request.POST = {
        'url': live_server.url + '/static/media/img/text-x-generic.png'
    }
    response = file_admin.remote_view(request, obj.pk)
    assert response.content == b'{"status": "ok"}'
    assert response.status_code == 200


@pytest.mark.django_db
def test_fileadmin_remove_label_action():
    file_admin = FileAdmin(File, AdminSite())

    label = LabelFactory()
    obj = EmptyFileFactory()
    assert obj.labels.count() == 0

    obj.labels.add(label)
    assert obj.labels.count() == 1

    file_admin.remove_label_action(AdminRequestFactory().get('/'), File.objects.all(), label)
    assert obj.labels.count() == 0


@pytest.mark.django_db
def test_fileadmin_response_add():
    file_admin = FileAdmin(File, AdminSite())
    obj = EmptyFileFactory()

    for url, status_code in [('/', 302), ('/?_tinymce', 200)]:
        request = AdminRequestFactory().get(url)
        # Allow the messages framework to work.
        request.session = 'session'
        request._messages = FallbackStorage(request)
        request.user = MockSuperUser()
        request.pages = None

        response = file_admin.response_add(request, obj)
        assert response.status_code == status_code


@pytest.mark.django_db
def test_media_list_shows_stylesheet(client):
    """
    Ensure the stylesheet is correctly conditionally loaded on the media file
    list page depending on the MEDIA_LIST_GRID_VIEW setting.
    """
    client.force_login(UserFactory(superuser=True))

    for fancy_view in [True, False]:
        with override_settings(UNCMS={'MEDIA_LIST_GRID_VIEW': fancy_view}):
            response = client.get(reverse('admin:media_file_changelist'))
        assert response.status_code == 200
        soup = BeautifulSoup(response.content, 'html.parser')
        assert bool(soup.find('link', attrs={'rel': 'stylesheet', 'href': '/static/media/css/media-list.css'})) is fancy_view


@pytest.mark.django_db
def test_file_detail_conditionally_shows_fieldsets(client):
    def has_usage_fieldset(context):
        return any(fieldset[0] == 'Usage' for fieldset in context['adminform'].fieldsets)

    client.force_login(UserFactory(superuser=True))

    response = client.get(reverse('admin:media_file_add'))
    assert response.status_code == 200
    assert has_usage_fieldset(response.context_data) is False

    file = MinimalGIFFileFactory()
    response = client.get(reverse('admin:media_file_change', args=[file.pk]))
    assert response.status_code == 200
    assert has_usage_fieldset(response.context_data) is True


@pytest.mark.django_db
def test_file_detail_preserves_filters(client):
    # Ensure ?_tinymce query string parameter is preserved in the form action.
    client.force_login(UserFactory(superuser=True))
    response = client.get(reverse('admin:media_file_add'))
    assert response.status_code == 200
    soup = BeautifulSoup(response.content, 'html.parser')
    assert soup.find('form', attrs={'id': 'file_form'}).get('action') is None

    response = client.get(reverse('admin:media_file_add'), {'_tinymce': '1'})
    assert response.status_code == 200
    soup = BeautifulSoup(response.content, 'html.parser')
    assert soup.find('form', attrs={'id': 'file_form'}).get('action') == '?_tinymce=1'


@pytest.mark.django_db
def test_file_list_type_filter(client):
    def context_pks(context):
        return sorted([obj.pk for obj in context['cl'].result_list])

    client.force_login(UserFactory(superuser=True))

    sample_jpeg = SampleJPEGFileFactory()
    sample_png = SamplePNGFileFactory()
    sample_not_image = EmptyFileFactory()

    url = reverse('admin:media_file_changelist')

    response = client.get(url)
    assert response.status_code == 200
    assert context_pks(response.context_data) == sorted([sample_jpeg.pk, sample_png.pk, sample_not_image.pk])

    response = client.get(url, {'filetype': 'image'})
    assert response.status_code == 200
    assert context_pks(response.context_data) == sorted([sample_jpeg.pk, sample_png.pk])


@pytest.mark.django_db
def test_file_media_library_changelist_view(client):
    SamplePNGFileFactory()
    client.force_login(UserFactory(superuser=True))

    response = client.get(reverse('admin:media_file_wysiwyg_list'))
    assert response.status_code == 200
    assert response.headers['X-Frame-Options'] == 'SAMEORIGIN'
    assert response.context_data['is_media_library_iframe']

    soup = BeautifulSoup(response.content, 'html.parser')
    assert soup.find('script', id='tinymce-script')


@pytest.mark.django_db
def test_fileadmin_edit_view(client):
    obj = SamplePNGFileFactory()
    # check permissions
    user = UserFactory(is_staff=True)
    client.force_login(user)

    url = reverse('admin:media_file_edit', args=[obj.pk])

    response = client.get(url)
    assert response.status_code == 403

    # give it the right permission, try again
    user.user_permissions.add(Permission.objects.get(codename='change_file'))
    response = client.get(url)
    assert response.status_code == 200

    # Post 800x600 PNG data to the file. (We test other branches inside the
    # form in test_forms.py.)
    with open(data_file_path('800x600.png'), 'rb') as fd:
        changed_data = ''.join([';base64,', base64.b64encode(fd.read()).decode('utf-8')])

    response = client.post(url, data={'changed_image': changed_data})
    assert response.status_code == 302
    assert response['Location'] == reverse('admin:media_file_change', args=[obj.pk])

    response = client.get(response['Location'])
    assert response.status_code == 200

    # Ensure its data has actually changed - the original was 1920x1080.
    obj.refresh_from_db()
    assert obj.width == 800
    assert obj.height == 600


@pytest.mark.django_db
def test_media_get_form(client):
    # Test the get_form override - rather than testing the function directly,
    # which is silly, ensure that the form in the context has the attributes
    # we are expecting.
    user = UserFactory(superuser=True)
    client.force_login(user)
    response = client.get(reverse('admin:media_file_add'))
    assert response.status_code == 200
    assert response.context_data['adminform'].form.user == user
