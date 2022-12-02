# pylint:disable=attribute-defined-outside-init
import json
from urllib.parse import urlencode, urljoin, urlparse

import pytest
import reversion
from bs4 import BeautifulSoup
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.widgets import (
    FilteredSelectMultiple,
    RelatedFieldWidgetWrapper,
)
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.http.request import QueryDict
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.text import slugify
from reversion.models import Version
from watson import search

from tests.factories import UserFactory
from tests.mocks import MockSuperUser
from tests.testing_app.admin import InlineModelInline, InlineModelNoPageInline
from tests.testing_app.models import (
    EmptyTestPage,
    InlineModelNoPage,
    PageContent,
    PageContentWithFields,
)
from uncms.pages.admin import (
    PAGE_FROM_KEY,
    PAGE_FROM_SITEMAP_VALUE,
    PAGE_TYPE_PARAMETER,
    PageAdmin,
    PageContentTypeFilter,
)
from uncms.pages.models import Page, get_registered_content


class MockRequest:
    pass


class TestPageAdmin(TestCase):

    maxDiff = None

    def setUp(self):
        self.site = AdminSite()
        self.page_admin = PageAdmin(Page, self.site)

        with search.update_index():
            content_type = ContentType.objects.get_for_model(PageContent)

            self.homepage = Page.objects.create(
                title="Homepage",
                slug='homepage',
                content_type=content_type,
            )

            PageContent.objects.create(
                page=self.homepage,
            )

    def _build_request(self, page_type=None, method="GET"):
        request = MockRequest()
        request.user = MockSuperUser()
        request.pages = MockRequest()
        request.pages.homepage = self.homepage
        request.GET = QueryDict('', mutable=True)
        request.POST = QueryDict('', mutable=True)
        request.COOKIES = {}
        request.META = {
            'SCRIPT_NAME': ''
        }
        request.method = method
        request.path = '/'
        request.resolver_match = False
        request.session = {}
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        if page_type:
            request.GET['type'] = page_type

        return request

    def _make_page(self, title, content_type):
        ''' Little helper to create a page whose parent is the homepage. '''
        content_page = Page.objects.create(
            title=title,
            slug=slugify(title),
            parent=self.homepage,
            content_type=content_type,
        )

        content_type.model_class().objects.create(
            page=content_page,
        )

    def test_pageadmin_get_object(self):
        factory = RequestFactory()
        request = factory.get('/')
        self.assertEqual(self.page_admin.get_object(request, -1), None)

    def test_pageadmin_register_page_inline(self):
        self.page_admin._register_page_inline(InlineModelNoPage)

    def test_pageadmin_register_content_inline(self):
        self.assertListEqual(self.page_admin.content_inlines, [])

        self.page_admin.register_content_inline(PageContent, InlineModelInline)

        self.assertListEqual(self.page_admin.content_inlines, [(PageContent, InlineModelInline), ])

    def test_pageadmin_get_inline_instances(self):
        request = self._build_request(
            page_type=ContentType.objects.get_for_model(PageContent).pk
        )

        self.assertListEqual(self.page_admin.get_inline_instances(request), [])
        self.assertListEqual(self.page_admin.get_inline_instances(request, obj=self.homepage), [])
        self.page_admin.register_content_inline(PageContent, InlineModelInline)
        self.assertEqual(len(self.page_admin.get_inline_instances(request, obj=self.homepage)), 1)

    def test_pageadmin_get_revision_instances(self):
        request = self._build_request(
            page_type=ContentType.objects.get_for_model(PageContent).pk
        )

        instances = self.page_admin.get_revision_instances(request, self.homepage)
        self.assertListEqual(instances, [self.homepage, self.homepage.content])

        # Register a content type which doesn't have a `page` attribute to
        # trigger the exception in `get_revision_instances`.
        self.page_admin.register_content_inline(PageContent, InlineModelNoPageInline)

        instances = self.page_admin.get_revision_instances(request, self.homepage)
        self.assertListEqual(instances, [self.homepage, self.homepage.content])

    def test_pageadmin_get_revision_form_data(self):
        request = self._build_request(
            page_type=ContentType.objects.get_for_model(PageContent).pk
        )

        # Create an initial revision.
        with reversion.create_revision():
            self.homepage.content.save()

        versions = Version.objects.get_for_object(self.homepage.content)

        data = self.page_admin.get_revision_form_data(request, self.homepage, versions[0])
        self.assertDictEqual(data, {'page_id': self.homepage.pk})

    def test_pageadmin_get_page_content_cls(self):
        request = self._build_request(
            page_type=ContentType.objects.get_for_model(PageContent).pk
        )

        request2 = self._build_request()

        self.assertEqual(self.page_admin.get_page_content_cls(request), PageContent)

        with self.assertRaises(Http404):
            self.page_admin.get_page_content_cls(request2)

        self.assertEqual(self.page_admin.get_page_content_cls(request2, self.homepage), PageContent)

    def test_pageadmin_get_fieldsets(self):
        request = self._build_request(
            page_type=ContentType.objects.get_for_model(PageContent).pk
        )
        request2 = self._build_request(
            page_type=ContentType.objects.get_for_model(PageContentWithFields).pk
        )

        with search.update_index():
            content_type = ContentType.objects.get_for_model(PageContentWithFields)

            self.content_page = Page.objects.create(
                title="Content page",
                slug='content_page',
                parent=self.homepage,
                content_type=content_type,
            )

            PageContentWithFields.objects.create(
                page=self.content_page,
            )

        pagecontent_fields = [
            (None, {
                'fields': ('title', 'slug', 'parent')
            }),
            ('Publication', {
                'fields': ('publication_date', 'expiry_date', 'is_online'),
                'classes': ('collapse',)
            }),
            ('Navigation', {
                'fields': ('short_title', 'in_navigation', "hide_from_anonymous",),
                'classes': ('collapse',)
            }),
            ("Security", {
                "fields": ("requires_authentication",),
                "classes": ("collapse",)
            }),
            ('SEO', {
                'fields': ('browser_title', 'meta_description', 'sitemap_priority', 'sitemap_changefreq', 'robots_index', 'robots_follow', 'robots_archive'),
                'classes': ('collapse',)
            }),
            ("Open Graph", {
                "fields": ("og_title", "og_description", "og_image"),
                "classes": ("collapse",)
            }),
            ("Twitter card", {
                "fields": ("twitter_card", "twitter_title", "twitter_description", "twitter_image"),
                "classes": ("collapse",)
            }),
        ]

        pagecontentwithfields_fields = [
            (None, {
                'fields': ('title', 'slug', 'parent')
            }),
            ('Page content', {
                'fields': ['description', 'inline_model']
            }),
            ('Publication', {
                'fields': ('publication_date', 'expiry_date', 'is_online'),
                'classes': ('collapse',)
            }),
            ('Navigation', {
                'fields': ('short_title', 'in_navigation', "hide_from_anonymous",),
                'classes': ('collapse',)
            }),
            ("Security", {
                "classes": ("collapse",),
                "fields": ("requires_authentication",),
            }),
            ('SEO', {
                'fields': ('browser_title', 'meta_description', 'sitemap_priority', 'sitemap_changefreq', 'robots_index', 'robots_follow', 'robots_archive'),
                'classes': ('collapse',)
            }),
            ("Open Graph", {
                "fields": ("og_title", "og_description", "og_image"),
                "classes": ("collapse",)
            }),
            ("Twitter card", {
                "fields": ("twitter_card", "twitter_title", "twitter_description", "twitter_image"),
                "classes": ("collapse",)
            }),
        ]

        self.assertEqual(self.page_admin.get_fieldsets(request), pagecontent_fields)
        self.assertEqual(self.page_admin.get_fieldsets(request2), pagecontentwithfields_fields)

    def test_pageadmin_get_all_children(self):
        self.assertListEqual(self.page_admin.get_all_children(self.homepage), [])

        # Add a child page.
        with search.update_index():
            content_type = ContentType.objects.get_for_model(PageContentWithFields)

            self.content_page = Page.objects.create(
                title="Content page",
                slug='content_page',
                parent=self.homepage,
                content_type=content_type,
            )

            PageContentWithFields.objects.create(
                page=self.content_page,
            )

        # The `children` attribute is cached as long as we use the original
        # reference, so get the Page again.
        self.homepage = Page.objects.get(slug='homepage')
        self.assertListEqual(self.page_admin.get_all_children(self.homepage), [self.content_page])

    def test_pageadmin_get_breadcrumbs(self):
        self.assertListEqual(self.page_admin.get_breadcrumbs(self.homepage), [self.homepage])

    def test_pageadmin_get_form(self):
        request = self._build_request(
            page_type=ContentType.objects.get_for_model(PageContent).pk
        )

        form = self.page_admin.get_form(request)

        keys = [
            'title', 'slug', 'parent', 'publication_date', 'expiry_date',
            'is_online', 'short_title', 'in_navigation', 'hide_from_anonymous',
            'requires_authentication',
            'browser_title', 'meta_description',
            'sitemap_priority', 'sitemap_changefreq', 'robots_index',
            'robots_follow', 'robots_archive', 'og_title', 'og_description',
            'og_image',

            'twitter_card', 'twitter_title', 'twitter_description', 'twitter_image'
        ]

        self.assertListEqual(list(form.base_fields.keys()), keys)

        request = self._build_request()

        # Test a page with a content model with fields.
        with search.update_index():
            content_type = ContentType.objects.get_for_model(PageContentWithFields)

            self.content_page = Page.objects.create(
                title="Content page",
                slug='content_page',
                parent=self.homepage,
                content_type=content_type,
            )

            PageContentWithFields.objects.create(
                page=self.content_page,
            )

        form = self.page_admin.get_form(request, obj=self.content_page)

        keys = ['title', 'slug', 'parent', 'description', 'inline_model',
                'publication_date', 'expiry_date',
                'is_online', 'short_title', 'in_navigation',
                'hide_from_anonymous',
                'requires_authentication',
                'browser_title', 'meta_description',
                'sitemap_priority', 'sitemap_changefreq', 'robots_index',
                'robots_follow', 'robots_archive', 'og_title', 'og_description',
                'og_image', 'twitter_card', 'twitter_title',
                'twitter_description', 'twitter_image']
        self.assertListEqual(list(form.base_fields.keys()), keys)

        self.assertIsInstance(form.base_fields['inline_model'].widget, RelatedFieldWidgetWrapper)

        setattr(PageContentWithFields, 'filter_horizontal', ['inline_model'])
        form = self.page_admin.get_form(request, obj=self.content_page)
        self.assertIsInstance(form.base_fields['inline_model'].widget, FilteredSelectMultiple)

        # No homepage.
        self.assertEqual(form.base_fields['parent'].choices, [(self.homepage.pk, 'Homepage')])

        request.pages.homepage = None
        form = self.page_admin.get_form(request, obj=self.content_page)

        self.assertListEqual(form.base_fields['parent'].choices, [('', '---------')])

        # Trigger the `content_cls.DoesNotExist` exception.
        content_cls = self.page_admin.get_page_content_cls(request, self.content_page)

        class Obj:

            def __getattr__(self, name):
                return getattr(self.page, name)

            @property
            def content(self):
                raise content_cls.DoesNotExist

            def __init__(self, page, *args, **kwargs):
                self.page = page

        obj = Obj(self.content_page)
        self.page_admin.get_form(request, obj=obj)

    def test_pageadmin_save_model(self):
        # NOTE: This page type is different to the one used by the homepage.
        # This is intentional to test certain conditional routes in the method.
        request = self._build_request(
            page_type=ContentType.objects.get_for_model(PageContentWithFields).pk
        )

        form = self.page_admin.get_form(request)(data={
            'title': 'Homepage',
            'slug': 'homepage',
            'description': 'Foo'
        })
        form.is_valid()

        self.assertEqual(self.homepage.content_type_id, ContentType.objects.get_for_model(PageContent).pk)

        with self.assertRaises(AttributeError):
            self.homepage.content.description  # pylint:disable=pointless-statement

        # Save the model
        self.page_admin.save_model(request, self.homepage, form, True)

        self.assertEqual(self.homepage.content_type_id, ContentType.objects.get_for_model(PageContentWithFields).pk)
        self.assertEqual(self.homepage.content.description, 'Foo')

        self.page_admin.save_model(request, self.homepage, form, False)
        self.assertEqual(self.homepage.content_type_id, ContentType.objects.get_for_model(PageContentWithFields).pk)
        self.assertEqual(self.homepage.content.description, 'Foo')

    def test_pageadmin_has_add_content_permissions(self):
        request = self._build_request()
        self.assertTrue(self.page_admin.has_add_content_permission(request, Page))

    def test_pageadmin_has_add_permission(self):
        request = self._build_request()
        self.assertTrue(self.page_admin.has_add_permission(request))

        request.user.has_perm = lambda x: False
        self.assertFalse(self.page_admin.has_add_permission(request))

        request.user.has_perm = lambda x: True
        self.page_admin.has_add_content_permission = lambda x, y: False
        self.assertFalse(self.page_admin.has_add_permission(request))

    def test_pageadmin_has_change_permission(self):
        request = self._build_request()
        self.assertTrue(self.page_admin.has_change_permission(request))

        self.assertTrue(self.page_admin.has_change_permission(request, obj=self.homepage))

        request.user.has_perm = lambda x: False
        self.assertFalse(self.page_admin.has_change_permission(request))

    def test_pageadmin_has_delete_permission(self):
        request = self._build_request()
        self.assertTrue(self.page_admin.has_delete_permission(request))

        self.assertTrue(self.page_admin.has_delete_permission(request, obj=self.homepage))

        request.user.has_perm = lambda x: False
        self.assertFalse(self.page_admin.has_delete_permission(request))

    def test_pageadmin_patch_response_location(self):
        request = self._build_request()
        response = HttpResponseRedirect('/')
        patched_response = self.page_admin.patch_response_location(request, response)
        self.assertEqual(patched_response['Location'], '/')

        request.GET[PAGE_FROM_KEY] = '1'
        patched_response = self.page_admin.patch_response_location(request, response)
        self.assertEqual(patched_response['Location'], '/?from=1')

        response = Http404()
        patched_response = self.page_admin.patch_response_location(request, response)
        self.assertEqual(patched_response, response)

    def test_pageadmin_changelist_view(self):
        request = self._build_request()
        response = self.page_admin.changelist_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['title'], 'Select page to change')

        request.GET[PAGE_FROM_KEY] = '1'
        response = self.page_admin.changelist_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/?e=1')

        request.GET[PAGE_FROM_KEY] = PAGE_FROM_SITEMAP_VALUE
        response = self.page_admin.changelist_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/admin/')

    def test_pageadmin_change_view(self):

        request = self._build_request()
        response = self.page_admin.change_view(request, str(self.homepage.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['title'], 'Change page')

        response = self.page_admin.change_view(request, str(self.homepage.pk))

    def test_pageadmin_revision_view(self):
        request = self._build_request()

        # Create an initial revision.
        with reversion.create_revision():
            self.homepage.content.save()

        versions = Version.objects.get_for_object(self.homepage.content)

        response = self.page_admin.revision_view(request, str(self.homepage.pk), (versions[0].pk))
        self.assertEqual(response.status_code, 200)

    def test_pageadmin_add_view(self):  # pragma: no cover
        request = self._build_request()
        response = self.page_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        models = get_registered_content()
        for content in get_registered_content():
            if content != PageContent:
                content._meta.abstract = True

        response = self.page_admin.add_view(request)
        self.assertEqual(response.status_code, 302)

        for model in models:
            model._meta.abstract = False

        request.GET[PAGE_TYPE_PARAMETER] = ContentType.objects.get_for_model(PageContent).pk
        response = self.page_admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        request.user.has_perm = lambda x: False
        request.GET[PAGE_TYPE_PARAMETER] = ContentType.objects.get_for_model(PageContent).pk

        with self.assertRaises(PermissionDenied):
            response = self.page_admin.add_view(request)

    def test_pageadmin_response_add(self):
        factory = RequestFactory()
        request = factory.get('/')

        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        request.user = MockSuperUser()

        response = self.page_admin.response_add(request, self.homepage)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/admin/pages/page/')

    def test_pageadmin_response_change(self):
        factory = RequestFactory()
        request = factory.get('/')

        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        request.user = MockSuperUser()

        response = self.page_admin.response_change(request, self.homepage)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/admin/pages/page/')

    def test_pageadmin_delete_view(self):
        factory = RequestFactory()
        request = factory.get('/')

        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        request.user = MockSuperUser()

        response = self.page_admin.delete_view(request, str(self.homepage.pk))
        self.assertEqual(response.status_code, 200)

    def test_pageadmin_sitemap_json_view(self):
        # pylint:disable=fixme
        # FIXME: This is a bit of a silly test. Why is it comparing against a
        # giant half-kilobyte blob of hard-coded JSON? Can we do a more
        # meaningful test here?
        request = self._build_request()
        response = self.page_admin.sitemap_json_view(request)

        sitemap = '{"createHomepageUrl": "/admin/pages/page/add/?from=sitemap", "addUrl": "/admin/pages/page/add/?from=sitemap&parent=__id__", "canAdd": true, "changeUrl": "/admin/pages/page/__id__/change/?from=sitemap", "entries": [{"isOnline": true, "canDelete": true, "title": "Homepage", "canChange": true, "id": ' + str(self.homepage.pk) + ', "moveUrl": "/admin/pages/page/move-page/' + str(self.homepage.pk) + '/", "children": []}], "deleteUrl": "/admin/pages/page/__id__/delete/?from=sitemap"}'

        self.assertDictEqual(json.loads(response.content.decode()), json.loads(sitemap))
        self.assertEqual(response['Content-Type'], "application/json")

        # Add a child page.
        with search.update_index():
            content_type = ContentType.objects.get_for_model(PageContentWithFields)

            self.content_page = Page.objects.create(
                title="Content page",
                slug='content_page',
                parent=self.homepage,
                content_type=content_type,
            )

            PageContentWithFields.objects.create(
                page=self.content_page,
            )

        request.pages.homepage = Page.objects.get(slug='homepage')
        response = self.page_admin.sitemap_json_view(request)
        sitemap = '{"createHomepageUrl": "/admin/pages/page/add/?from=sitemap", "addUrl": "/admin/pages/page/add/?from=sitemap&parent=__id__", "canAdd": true, "changeUrl": "/admin/pages/page/__id__/change/?from=sitemap", "entries": [{"isOnline": true, "canDelete": true, "title": "Homepage", "canChange": true, "id": ' + str(self.homepage.pk) + ', "moveUrl": "/admin/pages/page/move-page/' + str(self.homepage.pk) + '/", "children": [{"isOnline": true, "canDelete": true, "title": "Content page", "canChange": true, "id": ' + str(self.content_page.pk) + ', "moveUrl": "/admin/pages/page/move-page/' + str(self.content_page.pk) + '/", "children": []}]}], "deleteUrl": "/admin/pages/page/__id__/delete/?from=sitemap"}'
        self.assertDictEqual(json.loads(response.content.decode()), json.loads(sitemap))
        self.assertEqual(response['Content-Type'], "application/json")

        request.pages.homepage = None
        response = self.page_admin.sitemap_json_view(request)
        sitemap = '{"createHomepageUrl": "/admin/pages/page/add/?from=sitemap", "addUrl": "/admin/pages/page/add/?from=sitemap&parent=__id__", "canAdd": true, "changeUrl": "/admin/pages/page/__id__/change/?from=sitemap", "entries": [], "deleteUrl": "/admin/pages/page/__id__/delete/?from=sitemap"}'
        self.assertDictEqual(json.loads(response.content.decode()), json.loads(sitemap))
        self.assertEqual(response['Content-Type'], "application/json")

    def test_pageadmin_move_page_view(self):
        request = self._build_request()
        request.POST['direction'] = 'up'
        response = self.page_admin.move_page_view(request, self.homepage.pk)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.content, b"Page could not be moved, as nothing to swap with.")

        request.POST['direction'] = 'down'
        response = self.page_admin.move_page_view(request, self.homepage.pk)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.content, b"Page could not be moved, as nothing to swap with.")

        request.POST['direction'] = 'foo'

        # Add some child pages.
        with search.update_index():
            content_type = ContentType.objects.get_for_model(PageContent)

            content_page_1 = Page.objects.create(
                title="Foo",
                slug='foo',
                parent=self.homepage,
                content_type=content_type,
            )

            PageContent.objects.create(
                page=content_page_1,
            )

            content_page_2 = Page.objects.create(
                title="Bar",
                slug='bar',
                parent=self.homepage,
                content_type=content_type,
            )

            PageContent.objects.create(
                page=content_page_2,
            )

        self.homepage = Page.objects.get(pk=self.homepage.pk)
        content_page_1 = Page.objects.get(pk=content_page_1.pk)
        content_page_2 = Page.objects.get(pk=content_page_2.pk)

        self.assertEqual(self.homepage.left, 1)
        self.assertEqual(self.homepage.right, 6)
        self.assertEqual(content_page_1.left, 2)
        self.assertEqual(content_page_1.right, 3)
        self.assertEqual(content_page_2.left, 4)
        self.assertEqual(content_page_2.right, 5)

        # Move the page
        request.POST['direction'] = 'down'
        response = self.page_admin.move_page_view(request, content_page_1.pk)

        self.homepage = Page.objects.get(pk=self.homepage.pk)
        content_page_1 = Page.objects.get(pk=content_page_1.pk)
        content_page_2 = Page.objects.get(pk=content_page_2.pk)

        self.assertEqual(self.homepage.left, 1)
        self.assertEqual(self.homepage.right, 6)
        self.assertEqual(content_page_1.left, 4)
        self.assertEqual(content_page_1.right, 5)
        self.assertEqual(content_page_2.left, 2)
        self.assertEqual(content_page_2.right, 3)

        self.assertEqual(response.status_code, 302)

        request.user.has_perm = lambda x: False
        response = self.page_admin.move_page_view(request, self.homepage.pk)
        self.assertEqual(response.status_code, 403)

    def test_pagecontenttypefilter_queryset(self):
        # Ensures that the queryset returned by filtering is correct.
        request = self._build_request()

        # Add some pages with different content types.
        with search.update_index():
            content_type = ContentType.objects.get_for_model(PageContent)
            content_type_2 = ContentType.objects.get_for_model(PageContentWithFields)

            self._make_page('Food', content_type)
            self._make_page('Barred', content_type)
            self._make_page('Bazooka', content_type_2)

        # Test with no filters. Should be the same as Page.objects.all().
        filterer = PageContentTypeFilter(request, {}, Page, self.page_admin)
        queryset = filterer.queryset(request, Page.objects.all())
        self.assertEqual(queryset.count(), Page.objects.all().count())

        # Test with a content type filter. It should return a subset of the
        # pages.
        content_type_id = ContentType.objects.get_for_model(PageContent).id
        parameters = {'page_type': content_type_id}
        filterer = PageContentTypeFilter(request, parameters, Page, self.page_admin)
        queryset = filterer.queryset(request, Page.objects.all())
        self.assertEqual(
            queryset.count(),
            Page.objects.filter(
                content_type_id=content_type_id
            ).count()
        )
        # The above will not be sufficient - we need to ensure that it is not
        # the same as the unfiltered queryset, not merely that the filtered
        # length is correct.
        self.assertNotEqual(queryset.count(), Page.objects.all().count())

    def test_pagecontenttypefilter_lookups(self):
        # Add some pages with different content types.
        with search.update_index():
            content_type = ContentType.objects.get_for_model(PageContent)
            content_type_2 = ContentType.objects.get_for_model(PageContentWithFields)

            self._make_page('John', content_type)
            self._make_page('Paul', content_type)
            self._make_page('Ringo', content_type_2)
        request = self._build_request()
        filterer = PageContentTypeFilter(request, {}, Page, self.page_admin)
        lookups = filterer.lookups(request, Page.objects.all())
        # Make sure that something has been returned...
        self.assertTrue(len(lookups) > 0)

        # ...and that they are of the correct content type.
        self.assertTrue(len(lookups) == len(get_registered_content()))

        # Ensure that the lookup names have been ordered.
        lookup_names = [lookup[1] for lookup in lookups]
        self.assertEqual(lookup_names, sorted(lookup_names))


@pytest.mark.django_db
def test_pageadmin_get_preserved_filters(client):
    """
    Make sure that filters are being preserved. Testing get_preserved_filters
    in isolation is both effort and doesn't actually test whether this works.
    It is better to ensure that the form action does what we think it is
    doing, and we do that by actually posting with a client to the form action
    on the page.
    """
    def build_url_with_qs(url, qs):
        # we can client.get(url, data) but that doesn't ensure that the URL is
        # exactly the same as the one with a guessed form action, so this is
        # to ensure consistency
        parsed = urlparse(url)
        parsed = parsed._replace(query=urlencode(qs))
        return parsed.geturl()

    def get_form_action(response):
        soup = BeautifulSoup(response.content, 'html.parser')
        element = soup.find(id='page_form')
        assert element
        return element.get('action')

    def post_and_check_form(url, title):
        response = client.post(url, data={'title': title, 'slug': slugify(title)})
        assert response.status_code == 302
        assert Page.objects.filter(title=title).count() == 1

    content_type_id = ContentType.objects.get_for_model(EmptyTestPage).id
    user = UserFactory(superuser=True)
    client.force_login(user)

    url = reverse('admin:pages_page_add')

    url_qs = build_url_with_qs(url, {'type': content_type_id})
    response = client.get(url_qs)
    assert response.status_code == 200
    # The "action" should be empty.
    assert get_form_action(response) is None
    # When "action" is empty on a form, browsers will use the current full URL
    # including query string.
    post_and_check_form(url_qs, title='Save me')

    # Cleanup! It'll require a parent page if we do not do this.
    Page.objects.all().delete()

    # Let's add a preserved filter to the URL.
    response = client.get(url, {'type': content_type_id, '_changelist_filters': 'seo_quality_control%3Dno-meta-description'})
    assert response.status_code == 200

    # Form action must be present.
    action_url = get_form_action(response)
    assert action_url is not None
    # Sanity check: make sure it begins with '?' - if Django changes this
    # our behaviour from here might not make sense
    assert action_url.startswith('?')
    # stupid test, but...
    assert '_changelist_filters' in action_url

    # Now try posting to it. It should create a page.
    post_and_check_form(urljoin(url, action_url), title='Save yourself')