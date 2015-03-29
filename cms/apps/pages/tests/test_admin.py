from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.widgets import FilteredSelectMultiple, RelatedFieldWidgetWrapper
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from django.db import models
from django.http import Http404, HttpResponseRedirect
from django.http.request import QueryDict
from django.test import TestCase, RequestFactory

from ..admin import PageAdmin, PAGE_FROM_KEY, PAGE_FROM_SITEMAP_VALUE, PAGE_TYPE_PARAMETER
from ..models import get_registered_content, ContentBase, Page
from .... import externals

import os
import sys
import warnings
warnings.simplefilter('ignore', DeprecationWarning)


# Test models
class PageContent(ContentBase):
    pass


class PageContentWithFields(ContentBase):
    description = models.TextField(
        blank=True,
    )

    inline_model = models.ManyToManyField(
        'InlineModelNoPage',
        blank=True,
    )


class InlineModel(models.Model):
    page = models.ForeignKey(Page)


class InlineModelNoPage(models.Model):
    pass


# Test model admins
class InlineModelNoPageInline(admin.StackedInline):
    model = InlineModelNoPage


class InlineModelInline(admin.StackedInline):
    model = InlineModel


# Other test classes
class MockRequest(object):
    pass


class MockSuperUser(object):
    pk = 1

    def has_perm(self, perm):
        return True


def get_inline_instances_1_4_x(self, request):
    inline_instances = []
    for inline_class in self.inlines:
        inline = inline_class(self.model, self.admin_site)
        inline.max_num = 0
        inline_instances.append(inline)

    return inline_instances


class TestPageAdmin(TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.page_admin = PageAdmin(Page, self.site)

        with externals.watson.context_manager("update_index")():
            content_type = ContentType.objects.get_for_model(PageContent)

            self.homepage = Page.objects.create(
                title="Homepage",
                url_title='homepage',
                content_type=content_type,
            )

            PageContent.objects.create(
                page=self.homepage,
            )

    def _build_request(self, page_type=None):
        request = MockRequest()
        request.user = MockSuperUser()
        request.pages = MockRequest()
        request.pages.homepage = self.homepage
        request.GET = QueryDict('', mutable=True)
        request.POST = QueryDict('', mutable=True)
        request.COOKIES = {}
        request.META = {}
        request.method = 'GET'
        request.path = '/'
        request.resolver_match = False

        if page_type:
            request.GET['type'] = page_type

        return request

    def test_pageadmin_register_page_inline(self):
        self.page_admin._register_page_inline(InlineModelNoPage)

    def test_pageadmin_register_content_inline(self):
        self.assertListEqual(self.page_admin.content_inlines, [])

        self.page_admin.register_content_inline(PageContent, InlineModelInline)

        self.assertListEqual(self.page_admin.content_inlines, [(PageContent, InlineModelInline), ])

    def test_get_inline_instances_1_4_x(self):
        class Inlines(object):
            model = PageContent
            admin_site = self.page_admin

            def __init__(self, *args, **kwargs):
                self.inlines = kwargs.get('inlines', [])

        factory = RequestFactory()
        request = factory.get('/')

        self.assertListEqual(get_inline_instances_1_4_x(Inlines(), request), [])
        self.assertEqual(len(get_inline_instances_1_4_x(Inlines(inlines=[InlineModel]), request)), 1)

    def test_pageadmin_get_inline_instances(self):
        request = self._build_request(
            page_type=ContentType.objects.get_for_model(PageContent).pk
        )

        self.assertListEqual(self.page_admin.get_inline_instances(request), [])
        self.assertListEqual(self.page_admin.get_inline_instances(request, obj=self.homepage), [])
        self.page_admin.register_content_inline(PageContent, InlineModelInline)
        self.assertEqual(len(self.page_admin.get_inline_instances(request, obj=self.homepage)), 1)

        # Monkey patch the function back to Django 1.4.x style so we can trigger
        # the TypeError in `PageAdmin.get_inline_instances`.
        setattr(admin.ModelAdmin, 'get_inline_instances', get_inline_instances_1_4_x)

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
        with externals.reversion.create_revision():
            self.homepage.content.save()

        versions = externals.reversion.get_for_object(self.homepage.content)

        data = self.page_admin.get_revision_form_data(request, self.homepage, versions[0])
        self.assertDictEqual(data, {'page': self.homepage.pk})

    def test_pageadmin_get_page_content_cls(self):
        request = self._build_request(
            page_type=ContentType.objects.get_for_model(PageContent).pk
        )

        request2 = self._build_request()

        self.assertEqual(self.page_admin.get_page_content_cls(request), PageContent)

        with self.assertRaises(Http404):
            self.page_admin.get_page_content_cls(request2)

        self.assertEqual(self.page_admin.get_page_content_cls(request2, self.homepage), PageContent)

        with self.assertRaises(AttributeError):
            self.page_admin.get_page_content_cls(request2, self.homepage.content)

    def test_pageadmin_get_fieldsets(self):
        request = self._build_request(
            page_type=ContentType.objects.get_for_model(PageContent).pk
        )
        request2 = self._build_request(
            page_type=ContentType.objects.get_for_model(PageContentWithFields).pk
        )

        with externals.watson.context_manager("update_index")():
            content_type = ContentType.objects.get_for_model(PageContentWithFields)

            self.content_page = Page.objects.create(
                title="Content page",
                url_title='content_page',
                parent=self.homepage,
                content_type=content_type,
            )

            PageContentWithFields.objects.create(
                page=self.content_page,
            )

        pagecontent_fields = (
            (None, {
                'fields': ('title', 'url_title', 'parent')
            }),
            ('Publication', {
                'fields': ('publication_date', 'expiry_date', 'is_online'),
                'classes': ('collapse',)
            }),
            ('Navigation', {
                'fields': ('short_title', 'in_navigation'),
                'classes': ('collapse',)
            }),
            ('Search engine optimization', {
                'fields': ('browser_title', 'meta_keywords', 'meta_description', 'sitemap_priority', 'sitemap_changefreq', 'robots_index', 'robots_follow', 'robots_archive'),
                'classes': ('collapse',)
            })
        )

        pagecontentwithfields_fields = (
            (None, {
                'fields': ('title', 'url_title', 'parent')
            }),
            ('Page content', {
                'fields': ['description', 'inline_model']
            }),
            ('Publication', {
                'fields': ('publication_date', 'expiry_date', 'is_online'),
                'classes': ('collapse',)
            }),
            ('Navigation', {
                'fields': ('short_title', 'in_navigation'),
                'classes': ('collapse',)
            }),
            ('Search engine optimization', {
                'fields': ('browser_title', 'meta_keywords', 'meta_description', 'sitemap_priority', 'sitemap_changefreq', 'robots_index', 'robots_follow', 'robots_archive'),
                'classes': ('collapse',)
            })
        )

        self.assertEqual(self.page_admin.get_fieldsets(request), pagecontent_fields)
        self.assertEqual(self.page_admin.get_fieldsets(request2), pagecontentwithfields_fields)

    def test_pageadmin_get_all_children(self):
        self.assertListEqual(self.page_admin.get_all_children(self.homepage), [])

        # Add a child page.
        with externals.watson.context_manager("update_index")():
            content_type = ContentType.objects.get_for_model(PageContentWithFields)

            self.content_page = Page.objects.create(
                title="Content page",
                url_title='content_page',
                parent=self.homepage,
                content_type=content_type,
            )

            PageContentWithFields.objects.create(
                page=self.content_page,
            )

        # The `children` attribute is cached as long as we use the original
        # reference, so get the Page again.
        self.homepage = Page.objects.get(url_title='homepage')
        self.assertListEqual(self.page_admin.get_all_children(self.homepage), [self.content_page])

    def test_pageadmin_get_breadcrumbs(self):
        self.assertListEqual(self.page_admin.get_breadcrumbs(self.homepage), [self.homepage])

    def test_pageadmin_get_form(self):
        request = self._build_request(
            page_type=ContentType.objects.get_for_model(PageContent).pk
        )

        form = self.page_admin.get_form(request)

        keys = ['title', 'url_title', 'parent', 'publication_date',
                'expiry_date', 'is_online', 'short_title', 'in_navigation',
                'browser_title', 'meta_keywords', 'meta_description',
                'sitemap_priority', 'sitemap_changefreq', 'robots_index',
                'robots_follow', 'robots_archive']
        self.assertListEqual(form.base_fields.keys(), keys)

        request = self._build_request()

        # Test a page with a content model with fields.
        with externals.watson.context_manager("update_index")():
            content_type = ContentType.objects.get_for_model(PageContentWithFields)

            self.content_page = Page.objects.create(
                title="Content page",
                url_title='content_page',
                parent=self.homepage,
                content_type=content_type,
            )

            PageContentWithFields.objects.create(
                page=self.content_page,
            )

        form = self.page_admin.get_form(request, obj=self.content_page)

        keys = ['title', 'url_title', 'parent', 'description', 'inline_model',
                'publication_date', 'expiry_date', 'is_online', 'short_title',
                'in_navigation', 'browser_title', 'meta_keywords',
                'meta_description', 'sitemap_priority', 'sitemap_changefreq',
                'robots_index', 'robots_follow', 'robots_archive']
        self.assertListEqual(form.base_fields.keys(), keys)

        self.assertIsInstance(form.base_fields['inline_model'].widget, RelatedFieldWidgetWrapper)

        setattr(PageContentWithFields, 'filter_horizontal', ['inline_model'])
        form = self.page_admin.get_form(request, obj=self.content_page)
        self.assertIsInstance(form.base_fields['inline_model'].widget, FilteredSelectMultiple)

        # No homepage.
        self.assertEqual(form.base_fields['parent'].choices, [(self.homepage.pk, u'Homepage')])

        request.pages.homepage = None
        form = self.page_admin.get_form(request, obj=self.content_page)

        self.assertListEqual(form.base_fields['parent'].choices, [('', '---------')])

    def test_pageadmin_save_model(self):
        # NOTE: This page type is different to the one used by the homepage.
        # This is intentional to test certain conditional routes in the method.
        request = self._build_request(
            page_type=ContentType.objects.get_for_model(PageContentWithFields).pk
        )

        form = self.page_admin.get_form(request)(data={
            'title': 'Homepage',
            'url_title': 'homepage',
            'description': 'Foo'
        })
        form.is_valid()

        self.assertEqual(self.homepage.content_type_id, ContentType.objects.get_for_model(PageContent).pk)

        with self.assertRaises(AttributeError):
            self.homepage.content.description

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

    def test_pageadmin_revision_view(self):
        request = self._build_request()

        # Create an initial revision.
        with externals.reversion.create_revision():
            self.homepage.content.save()

        versions = externals.reversion.get_for_object(self.homepage.content)

        response = self.page_admin.revision_view(request, str(self.homepage.pk), (versions[0].pk))
        self.assertEqual(response.status_code, 200)

    def test_pageadmin_add_view(self):
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
        request = self._build_request()
        response = self.page_admin.sitemap_json_view(request)

        sitemap = '{"createHomepageUrl": "/admin/pages/page/add/?from=sitemap", "addUrl": "/admin/pages/page/add/?from=sitemap&parent=__id__", "canAdd": true, "changeUrl": "/admin/pages/page/__id__/?from=sitemap", "entries": [{"isOnline": true, "canDelete": true, "title": "Homepage", "canChange": true, "id": ' + str(self.homepage.pk) + ', "children": []}], "deleteUrl": "/admin/pages/page/__id__/delete/?from=sitemap", "moveUrl": "/admin/pages/page/move-page/"}'
        self.assertEqual(response.content, sitemap)
        self.assertEqual(response['Content-Type'], "application/json; charset=utf-8")

        # Add a child page.
        with externals.watson.context_manager("update_index")():
            content_type = ContentType.objects.get_for_model(PageContentWithFields)

            self.content_page = Page.objects.create(
                title="Content page",
                url_title='content_page',
                parent=self.homepage,
                content_type=content_type,
            )

            PageContentWithFields.objects.create(
                page=self.content_page,
            )

        request.pages.homepage = Page.objects.get(url_title='homepage')
        response = self.page_admin.sitemap_json_view(request)
        sitemap = '{"createHomepageUrl": "/admin/pages/page/add/?from=sitemap", "addUrl": "/admin/pages/page/add/?from=sitemap&parent=__id__", "canAdd": true, "changeUrl": "/admin/pages/page/__id__/?from=sitemap", "entries": [{"isOnline": true, "canDelete": true, "title": "Homepage", "canChange": true, "id": ' + str(self.homepage.pk) + ', "children": [{"isOnline": true, "canDelete": true, "title": "Content page", "canChange": true, "id": ' + str(self.content_page.pk) + ', "children": []}]}], "deleteUrl": "/admin/pages/page/__id__/delete/?from=sitemap", "moveUrl": "/admin/pages/page/move-page/"}'
        self.assertEqual(response.content, sitemap)
        self.assertEqual(response['Content-Type'], "application/json; charset=utf-8")

        request.pages.homepage = None
        response = self.page_admin.sitemap_json_view(request)
        sitemap = '{"createHomepageUrl": "/admin/pages/page/add/?from=sitemap", "addUrl": "/admin/pages/page/add/?from=sitemap&parent=__id__", "canAdd": true, "changeUrl": "/admin/pages/page/__id__/?from=sitemap", "entries": [], "deleteUrl": "/admin/pages/page/__id__/delete/?from=sitemap", "moveUrl": "/admin/pages/page/move-page/"}'
        self.assertEqual(response.content, sitemap)
        self.assertEqual(response['Content-Type'], "application/json; charset=utf-8")

    def test_pageadmin_move_page_view(self):
        request = self._build_request()
        request.POST['page'] = self.homepage.pk
        request.POST['direction'] = 'up'
        response = self.page_admin.move_page_view(request)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.content, "Page could not be moved, as nothing to swap with.")

        request.POST['direction'] = 'down'
        response = self.page_admin.move_page_view(request)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.content, "Page could not be moved, as nothing to swap with.")

        request.POST['direction'] = 'foo'

        stderr = sys.stderr
        with open(os.devnull, 'w') as f:
            sys.stderr = f

        try:
            with self.assertRaises(ValueError):
                self.page_admin.move_page_view(request)
        except ValueError:
            pass

        sys.stderr = stderr

        # Add some child pages.
        with externals.watson.context_manager("update_index")():
            content_type = ContentType.objects.get_for_model(PageContent)

            content_page_1 = Page.objects.create(
                title="Foo",
                url_title='foo',
                parent=self.homepage,
                content_type=content_type,
            )

            PageContent.objects.create(
                page=content_page_1,
            )

            content_page_2 = Page.objects.create(
                title="Bar",
                url_title='bar',
                parent=self.homepage,
                content_type=content_type,
            )

            PageContent.objects.create(
                page=content_page_2,
            )

        request.POST['page'] = content_page_1.pk
        request.POST['direction'] = 'down'
        response = self.page_admin.move_page_view(request)
        self.assertEqual(response.content, "Page #" + str(content_page_1.pk) + " was moved down.")
        self.assertEqual(response.status_code, 200)

        request.user.has_perm = lambda x: False
        response = self.page_admin.move_page_view(request)
        self.assertEqual(response.status_code, 403)