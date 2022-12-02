# pylint:disable=duplicate-code
import base64
import random
import sys

import pytest
from bs4 import BeautifulSoup
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.views.main import IS_POPUP_VAR
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.test import LiveServerTestCase, RequestFactory, TransactionTestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.timezone import now

from tests.factories import UserFactory
from tests.media.factories import (
    EmptyFileFactory,
    SampleJPEGFileFactory,
    SamplePNGFileFactory,
)
from tests.mocks import MockSuperUser
from uncms.media.admin import FileAdmin
from uncms.media.forms import mime_check
from uncms.media.models import File, Label


class BrokenFile:

    """
    A special class designed to raise an IOError the second time it's `file`
    method is called. Used to test sorl.
    """

    name_requested = False

    def __getattr__(self, name):
        if name == 'file':
            if not self.name_requested:
                self.name_requested = True
                return self.obj.file
            return self.obj.file.file
        return getattr(self.obj, name)

    def __init__(self, *args, **kwargs):
        self.obj = File.objects.create(**kwargs)


class TestFileAdminBase(TransactionTestCase):

    def setUp(self):
        self.site = AdminSite()
        self.file_admin = FileAdmin(File, self.site)

        File.objects.all().delete()

        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.request.user = MockSuperUser()

        # An invalid JPEG
        self.name_1 = '{}-{}.jpg'.format(
            now().strftime('%Y-%m-%d_%H-%M-%S'),
            random.randint(0, sys.maxsize)
        )

        self.obj_1 = File.objects.create(
            title="Foo",
            file=SimpleUploadedFile(self.name_1, b"data", content_type="image/jpeg")
        )

        # A valid GIF.
        self.name_2 = '{}-{}.gif'.format(
            now().strftime('%Y-%m-%d_%H-%M-%S'),
            random.randint(0, sys.maxsize)
        )

        base64_string = b'R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='

        self.obj_2 = File.objects.create(
            title="Foo 2",
            file=SimpleUploadedFile(self.name_2, base64.b64decode(base64_string), content_type="image/gif")
        )

        # For mime_check: an image whose contents match the given extension
        self.file_1 = SimpleUploadedFile(self.name_2, base64.b64decode(base64_string), content_type="image/gif")
        # ...and one whose contents do not...
        self.file_2 = SimpleUploadedFile(self.name_2, base64.b64decode(base64_string), content_type="image/jpeg")
        # ...and one we should never check (we only care about images)
        self.file_3 = SimpleUploadedFile(self.name_2, base64.b64decode(base64_string), content_type="text/html")

        self.label = Label.objects.create(
            name="Foo"
        )

    def tearDown(self):
        self.obj_1.file.delete(False)
        self.obj_1.delete()

        # self.obj_2.file.delete(False)
        # self.obj_2.delete()

    def test_fileadminbase_to_field_allowed(self):
        self.assertTrue(self.file_admin.to_field_allowed(self.request, 'id'))
        self.assertFalse(self.file_admin.to_field_allowed(self.request, 'foo'))

    def test_fileadminbase_add_label_action(self):
        self.assertEqual(self.obj_1.labels.count(), 0)

        self.file_admin.add_label_action(self.request, File.objects.all(), self.label)

        self.assertEqual(self.obj_1.labels.count(), 1)

    def test_fileadminbase_remove_label_action(self):
        self.assertEqual(self.obj_1.labels.count(), 0)

        self.obj_1.labels.add(self.label)

        self.assertEqual(self.obj_1.labels.count(), 1)

        self.file_admin.remove_label_action(self.request, File.objects.all(), self.label)

        self.assertEqual(self.obj_1.labels.count(), 0)

    def test_fileadminbase_get_actions(self):
        actions = self.file_admin.get_actions(self.request)
        self.assertEqual(len(actions), 3)

        self.request = self.factory.get('/?{}'.format(IS_POPUP_VAR))
        self.request.user = MockSuperUser()
        actions = self.file_admin.get_actions(self.request)
        self.assertEqual(len(actions), 0)

    def test_fileadminbase_get_size(self):
        # Why this has to use a unicode space, I don't know..
        self.assertEqual(self.file_admin.get_size(self.obj_1), '4\xa0bytes')

        obj = File.objects.create(
            title="Foo",
            file='media/not/a/real.file'
        )

        self.assertEqual(self.file_admin.get_size(obj), '0 bytes')

    def test_fileadminbase_get_preview(self):
        # We can't do an `assertEqual` here as the generated src URL is dynamic.
        preview = self.file_admin.get_preview(self.obj_2)

        self.assertIn(
            '<img class="uncms-thumbnail" uncms:permalink="/r/{}-{}/"'.format(
                ContentType.objects.get_for_model(File).pk,
                self.obj_2.pk
            ),
            preview,
        )

        self.assertIn(
            'width="200" height="200" alt="" title="Foo 2"/>',
            preview,
        )

        obj = BrokenFile(
            title="Foo",
            file='media/not/a/real.png'
        )

        preview = self.file_admin.get_preview(obj)

        assert preview.startswith('<img class="uncms-thumbnail"')

        obj = File.objects.create(
            title="Foo",
            file='media/not/a/real.file'
        )
        preview = self.file_admin.get_preview(obj)

        self.assertEqual(preview, '<img class="uncms-fallback-icon" uncms:permalink="/r/{}-{}/" src="/static/media/img/text-x-generic-template.png" width="56" height="66" alt="" title="Foo"/>'.format(
            ContentType.objects.get_for_model(File).pk,
            obj.pk
        ))

        obj.delete()

    def test_fileadminbase_response_add(self):
        # Allow the messages framework to work.
        setattr(self.request, 'session', 'session')
        messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', messages)
        self.request.user = MockSuperUser()

        response = self.file_admin.response_add(self.request, self.obj_1)
        self.assertEqual(response.status_code, 302)

        self.request = self.factory.get('/?_tinymce')
        self.request.user = MockSuperUser()
        setattr(self.request, 'session', 'session')
        messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', messages)
        self.request.user = MockSuperUser()
        self.request.pages = {}

        response = self.file_admin.response_add(self.request, self.obj_1)
        self.assertEqual(response.status_code, 200)

    def test_fileadminbase_changelist_view(self):
        self.request.user = MockSuperUser()
        view = self.file_admin.changelist_view(self.request)

        self.assertEqual(view.status_code, 200)
        self.assertEqual(view.template_name, 'admin/media/file/change_list.html')
        self.assertNotIn('foo', view.context_data)

        view = self.file_admin.changelist_view(self.request, extra_context={'foo': 'bar'})

        self.assertEqual(view.status_code, 200)
        self.assertEqual(view.template_name, 'admin/media/file/change_list.html')
        self.assertIn('foo', view.context_data)

    def test_fileadminbase_mime_check(self):
        self.assertEqual(mime_check(self.file_1), True)
        self.assertEqual(mime_check(self.file_2), False)
        self.assertEqual(mime_check(self.file_3), True)


class LiveServerTestFileAdminBase(LiveServerTestCase):

    def setUp(self):
        self.site = AdminSite()
        self.file_admin = FileAdmin(File, self.site)

        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.request.user = MockSuperUser

        # An invalid JPEG
        self.name_1 = '{}-{}.jpg'.format(
            now().strftime('%Y-%m-%d_%H-%M-%S'),
            random.randint(0, sys.maxsize)
        )

        self.obj_1 = File.objects.create(
            title="Foo",
            file=SimpleUploadedFile(self.name_1, b"data", content_type="image/jpeg")
        )

    def tearDown(self):
        self.obj_1.file.delete(False)
        self.obj_1.delete()

    def test_fileadminbase_remote_view(self):
        self.request.user = MockSuperUser()
        view = self.file_admin.remote_view(self.request, self.obj_1.pk)

        # 405: Method not allowed. We have to POST to this view.
        self.assertEqual(view.status_code, 405)

        self.request.method = 'POST'

        # No URL supplied.
        with self.assertRaises(Http404):
            view = self.file_admin.remote_view(self.request, self.obj_1.pk)

        # No permissions.
        self.request.user.has_perm = lambda x: False

        view = self.file_admin.remote_view(self.request, self.obj_1.pk)
        self.assertEqual(view.status_code, 403)

        self.request.user.has_perm = lambda x: True

        # Allow the messages framework to work.
        setattr(self.request, 'session', 'session')
        messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', messages)
        self.request.user = MockSuperUser()

        self.request.POST = {
            'url': self.live_server_url + '/static/media/img/text-x-generic.png'
        }
        view = self.file_admin.remote_view(self.request, self.obj_1.pk)

        self.assertEqual(view.content, b'{"status": "ok"}')
        self.assertEqual(view.status_code, 200)


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

    file = File.objects.create(
        title="Foo",
        file=SimpleUploadedFile('Sample', b"data", content_type='image/jpeg')
    )
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
    assert soup.find('form').get('action') is None

    response = client.get(reverse('admin:media_file_add'), {'_tinymce': '1'})
    assert response.status_code == 200
    soup = BeautifulSoup(response.content, 'html.parser')
    assert soup.find('form').get('action') == '?_tinymce=1'


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
