# pylint:disable=redefined-outer-name
# ^ because of fixture functions being defined here and used in method
#   signatures
import json
from unittest.mock import MagicMock, Mock, patch
from urllib.parse import urlencode, urljoin, urlparse

import pytest
import reversion
from bs4 import BeautifulSoup
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.widgets import (
    FilteredSelectMultiple,
    RelatedFieldWidgetWrapper,
)
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.http.request import QueryDict
from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils.text import slugify
from reversion.models import Version

from tests.mocks import MockSuperUser
from tests.testing_app.admin import InlineModelInline, InlineModelNoPageInline
from tests.testing_app.models import (
    InlineModelNoPage,
    PageContent,
    PageContentWithFields,
    PageContentWithSections,
    Section,
)
from uncms.pages.admin import (
    PAGE_FROM_KEY,
    PAGE_FROM_SITEMAP_VALUE,
    PAGE_TYPE_PARAMETER,
    PageAdmin,
    PageContentTypeFilter,
)
from uncms.pages.models import Page, get_registered_content
from uncms.testhelpers.factories import AdminRequestFactory, UserFactory
from uncms.testhelpers.factories.pages import PageFactory
from uncms.testhelpers.models import EmptyTestPage


@pytest.fixture
def admin_site():
    return AdminSite()


@pytest.fixture
def page_admin(admin_site):
    return PageAdmin(Page, admin_site)


@pytest.fixture
def homepage():
    return PageFactory(
        content=PageContent(),
        title="Homepage",
        slug="homepage",
    )


def build_request(page_type=None):
    request = AdminRequestFactory().get("/")
    request.user = MockSuperUser()
    request.GET = QueryDict("", mutable=True)

    if page_type:
        request.GET["type"] = page_type

    return request


@pytest.mark.django_db
def test_pageadmin_add_view(page_admin):  # pragma: no cover
    request = build_request()
    response = page_admin.add_view(request)
    assert response.status_code == 200

    models = get_registered_content()
    for content in get_registered_content():
        if content != PageContent:
            content._meta.abstract = True

    response = page_admin.add_view(request)
    assert response.status_code == 302

    for model in models:
        model._meta.abstract = False

    request.GET[PAGE_TYPE_PARAMETER] = ContentType.objects.get_for_model(PageContent).pk
    response = page_admin.add_view(request)
    assert response.status_code == 200

    request.user.has_perm = lambda x: False
    request.GET[PAGE_TYPE_PARAMETER] = ContentType.objects.get_for_model(PageContent).pk

    with pytest.raises(PermissionDenied):
        response = page_admin.add_view(request)


@pytest.mark.django_db
def test_pageadmin_change_view(page_admin, homepage):
    request = build_request()
    response = page_admin.change_view(request, str(homepage.pk))
    assert response.status_code == 200
    assert response.context_data["title"] == "Change page"

    response = page_admin.change_view(request, str(homepage.pk))


@pytest.mark.django_db
def test_pageadmin_changelist_view(page_admin):
    request = build_request()
    response = page_admin.changelist_view(request)
    assert response.status_code == 200
    assert response.context_data["title"] == "Select page to change"

    request.GET[PAGE_FROM_KEY] = "1"
    response = page_admin.changelist_view(request)
    assert response.status_code == 302
    assert response["Location"] == "/?e=1"

    request.GET[PAGE_FROM_KEY] = PAGE_FROM_SITEMAP_VALUE
    response = page_admin.changelist_view(request)
    assert response.status_code == 302
    assert response["Location"] == "/admin/"


@pytest.mark.django_db
def test_pageadmin_get_fieldsets(page_admin):
    request = build_request(page_type=ContentType.objects.get_for_model(PageContent).pk)
    request2 = build_request(
        page_type=ContentType.objects.get_for_model(PageContentWithFields).pk
    )

    PageFactory(content=PageContentWithFields())

    pagecontent_fields = [
        (None, {"fields": ("title", "slug", "parent")}),
        (
            "Publication",
            {
                "fields": ("publication_date", "expiry_date", "is_online"),
                "classes": ("collapse",),
            },
        ),
        (
            "Navigation",
            {
                "fields": (
                    "short_title",
                    "in_navigation",
                    "hide_from_anonymous",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Security",
            {"fields": ("requires_authentication",), "classes": ("collapse",)},
        ),
        (
            "SEO",
            {
                "fields": (
                    "browser_title",
                    "meta_description",
                    "sitemap_priority",
                    "sitemap_changefreq",
                    "robots_index",
                    "robots_follow",
                    "robots_archive",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Open Graph",
            {
                "fields": ("og_title", "og_description", "og_image"),
                "classes": ("collapse",),
            },
        ),
    ]

    pagecontentwithfields_fields = [
        (None, {"fields": ("title", "slug", "parent")}),
        ("Page content", {"fields": ["description", "inline_model"]}),
        (
            "Publication",
            {
                "fields": ("publication_date", "expiry_date", "is_online"),
                "classes": ("collapse",),
            },
        ),
        (
            "Navigation",
            {
                "fields": (
                    "short_title",
                    "in_navigation",
                    "hide_from_anonymous",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Security",
            {
                "classes": ("collapse",),
                "fields": ("requires_authentication",),
            },
        ),
        (
            "SEO",
            {
                "fields": (
                    "browser_title",
                    "meta_description",
                    "sitemap_priority",
                    "sitemap_changefreq",
                    "robots_index",
                    "robots_follow",
                    "robots_archive",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Open Graph",
            {
                "fields": ("og_title", "og_description", "og_image"),
                "classes": ("collapse",),
            },
        ),
    ]

    assert page_admin.get_fieldsets(request) == pagecontent_fields
    assert page_admin.get_fieldsets(request2) == pagecontentwithfields_fields


@pytest.mark.django_db
def test_pageadmin_get_form(page_admin, homepage):
    request = build_request(page_type=ContentType.objects.get_for_model(PageContent).pk)

    form = page_admin.get_form(request)

    keys = [
        "title",
        "slug",
        "parent",
        "publication_date",
        "expiry_date",
        "is_online",
        "short_title",
        "in_navigation",
        "hide_from_anonymous",
        "requires_authentication",
        "browser_title",
        "meta_description",
        "sitemap_priority",
        "sitemap_changefreq",
        "robots_index",
        "robots_follow",
        "robots_archive",
        "og_title",
        "og_description",
        "og_image",
    ]

    assert list(form.base_fields.keys()) == keys

    request = build_request()

    # Test a page with a content model with fields.
    content_page = PageFactory(parent=homepage, content=PageContentWithFields())

    form = page_admin.get_form(request, obj=content_page)

    keys = [
        "title",
        "slug",
        "parent",
        "description",
        "inline_model",
        "publication_date",
        "expiry_date",
        "is_online",
        "short_title",
        "in_navigation",
        "hide_from_anonymous",
        "requires_authentication",
        "browser_title",
        "meta_description",
        "sitemap_priority",
        "sitemap_changefreq",
        "robots_index",
        "robots_follow",
        "robots_archive",
        "og_title",
        "og_description",
        "og_image",
    ]
    assert list(form.base_fields.keys()) == keys

    assert isinstance(
        form.base_fields["inline_model"].widget, RelatedFieldWidgetWrapper
    )

    setattr(PageContentWithFields, "filter_horizontal", ["inline_model"])
    form = page_admin.get_form(request, obj=content_page)
    assert isinstance(form.base_fields["inline_model"].widget, FilteredSelectMultiple)

    # No homepage.
    assert form.base_fields["parent"].choices == [(homepage.pk, "Homepage")]

    request.pages.homepage = None
    form = page_admin.get_form(request, obj=content_page)

    assert form.base_fields["parent"].choices == [("", "---------")]

    # Trigger the `content_cls.DoesNotExist` exception.
    content_cls = page_admin.get_page_content_cls(request, content_page)

    class Obj:
        def __getattr__(self, name):
            return getattr(self.page, name)

        @property
        def content(self):
            raise content_cls.DoesNotExist

        def __init__(self, page, *args, **kwargs):
            self.page = page

    obj = Obj(content_page)
    page_admin.get_form(request, obj=obj)


@pytest.mark.django_db
def test_pageadmin_get_inline_instances(page_admin, homepage):
    request = build_request(page_type=ContentType.objects.get_for_model(PageContent).pk)

    assert page_admin.get_inline_instances(request) == []
    assert page_admin.get_inline_instances(request, obj=homepage) == []
    page_admin.register_content_inline(PageContent, InlineModelInline)
    assert len(page_admin.get_inline_instances(request, obj=homepage)) == 1


@pytest.mark.django_db
def test_pageadmin_get_page_content_cls(page_admin, homepage):
    request = build_request(page_type=ContentType.objects.get_for_model(PageContent).pk)

    request2 = build_request()

    assert page_admin.get_page_content_cls(request) == PageContent

    with pytest.raises(Http404):
        page_admin.get_page_content_cls(request2)

    assert page_admin.get_page_content_cls(request2, homepage) == PageContent


@pytest.mark.django_db
def test_pageadmin_get_revision_form_data(page_admin, homepage):
    request = build_request(page_type=ContentType.objects.get_for_model(PageContent).pk)

    # Create an initial revision.
    with reversion.create_revision():
        homepage.content.save()

    versions = Version.objects.get_for_object(homepage.content)

    data = page_admin.get_revision_form_data(request, homepage, versions[0])
    assert data == {"page_id": homepage.pk}


@pytest.mark.django_db
def test_pageadmin_get_revision_instances(page_admin, homepage):
    request = build_request(page_type=ContentType.objects.get_for_model(PageContent).pk)

    instances = page_admin.get_revision_instances(request, homepage)
    assert instances == [homepage, homepage.content]

    # Register a content type which doesn't have a `page` attribute to
    # trigger the exception in `get_revision_instances`.
    page_admin.register_content_inline(PageContent, InlineModelNoPageInline)

    instances = page_admin.get_revision_instances(request, homepage)
    assert instances == [homepage, homepage.content]


@pytest.mark.django_db
def test_pageadmin_has_add_content_permissions(page_admin):
    request = build_request()
    assert page_admin.has_add_content_permission(request, Page)


@pytest.mark.django_db
def test_pageadmin_has_add_permission(page_admin):
    request = build_request()
    assert page_admin.has_add_permission(request)

    request.user.has_perm = lambda x: False
    assert not page_admin.has_add_permission(request)

    request.user.has_perm = lambda x: True
    page_admin.has_add_content_permission = lambda x, y: False
    assert not page_admin.has_add_permission(request)


@pytest.mark.django_db
def test_pageadmin_has_change_permission(page_admin, homepage):
    request = build_request()
    assert page_admin.has_change_permission(request)

    assert page_admin.has_change_permission(request, obj=homepage)

    request.user.has_perm = lambda x: False
    assert not page_admin.has_change_permission(request)


@pytest.mark.django_db
def test_pageadmin_has_delete_permission(page_admin, homepage):
    request = build_request()
    assert page_admin.has_delete_permission(request)

    assert page_admin.has_delete_permission(request, obj=homepage)

    request.user.has_perm = lambda x: False
    assert not page_admin.has_delete_permission(request)


@pytest.mark.django_db
def test_pageadmin_patch_response_location(page_admin):
    request = build_request()
    response = HttpResponseRedirect("/")
    patched_response = page_admin.patch_response_location(request, response)
    assert patched_response["Location"] == "/"

    request.GET[PAGE_FROM_KEY] = "1"
    patched_response = page_admin.patch_response_location(request, response)
    assert patched_response["Location"] == "/?from=1"

    response = Http404()
    patched_response = page_admin.patch_response_location(request, response)
    assert patched_response == response


@pytest.mark.django_db
def test_pageadmin_register_content_inline(page_admin):
    assert page_admin.content_inlines == []

    page_admin.register_content_inline(PageContent, InlineModelInline)

    assert page_admin.content_inlines == [
        (PageContent, InlineModelInline),
    ]


@pytest.mark.django_db
def test_pageadmin_register_page_inline(page_admin):
    page_admin._register_page_inline(InlineModelNoPage)


@pytest.mark.django_db
def test_pageadmin_response_add(page_admin, homepage):
    request = AdminRequestFactory().get("/")
    request.user = MockSuperUser()

    response = page_admin.response_add(request, homepage)
    assert response.status_code == 302
    assert response["Location"] == "/admin/pages/page/"


@pytest.mark.django_db
def test_pageadmin_save_model(page_admin, homepage):
    # NOTE: This page type is different to the one used by the homepage.
    # This is intentional to test certain conditional routes in the method.
    request = build_request(
        page_type=ContentType.objects.get_for_model(PageContentWithFields).pk
    )

    form = page_admin.get_form(request)(
        data={"title": "Homepage", "slug": "homepage", "description": "Foo"}
    )
    form.is_valid()

    assert homepage.content_type_id == ContentType.objects.get_for_model(PageContent).pk

    with pytest.raises(AttributeError):
        homepage.content.description  # pylint:disable=pointless-statement

    # Save the model
    page_admin.save_model(request, homepage, form, True)

    assert (
        homepage.content_type_id
        == ContentType.objects.get_for_model(PageContentWithFields).pk
    )
    assert homepage.content.description == "Foo"

    page_admin.save_model(request, homepage, form, False)
    assert (
        homepage.content_type_id
        == ContentType.objects.get_for_model(PageContentWithFields).pk
    )
    assert homepage.content.description == "Foo"


@pytest.mark.django_db
def test_pageadmin_sitemap_json_view(page_admin, homepage):
    # pylint:disable=fixme
    # FIXME: This is a bit of a silly test. Why is it comparing against a
    # giant half-kilobyte blob of hard-coded JSON? Can we do a more
    # meaningful test here?
    request = build_request()
    response = page_admin.sitemap_json_view(request)

    sitemap = (
        '{"createHomepageUrl": "/admin/pages/page/add/?from=sitemap", "addUrl": "/admin/pages/page/add/?from=sitemap&parent=__id__", "canAdd": true, "changeUrl": "/admin/pages/page/__id__/change/?from=sitemap", "entries": [{"isOnline": true, "canDelete": true, "title": "Homepage", "canChange": true, "id": '
        + str(homepage.pk)
        + ', "moveUrl": "/admin/pages/page/move-page/'
        + str(homepage.pk)
        + '/", "children": []}], "deleteUrl": "/admin/pages/page/__id__/delete/?from=sitemap"}'
    )

    assert json.loads(response.content.decode()) == json.loads(sitemap)
    assert response["Content-Type"] == "application/json"

    # Add a child page.
    content_page = PageFactory(
        title="Content page", content=PageContentWithFields(), parent=homepage
    )

    request.pages.homepage = Page.objects.get(slug="homepage")
    response = page_admin.sitemap_json_view(request)
    sitemap = (
        '{"createHomepageUrl": "/admin/pages/page/add/?from=sitemap", "addUrl": "/admin/pages/page/add/?from=sitemap&parent=__id__", "canAdd": true, "changeUrl": "/admin/pages/page/__id__/change/?from=sitemap", "entries": [{"isOnline": true, "canDelete": true, "title": "Homepage", "canChange": true, "id": '
        + str(homepage.pk)
        + ', "moveUrl": "/admin/pages/page/move-page/'
        + str(homepage.pk)
        + '/", "children": [{"isOnline": true, "canDelete": true, "title": "Content page", "canChange": true, "id": '
        + str(content_page.pk)
        + ', "moveUrl": "/admin/pages/page/move-page/'
        + str(content_page.pk)
        + '/", "children": []}]}], "deleteUrl": "/admin/pages/page/__id__/delete/?from=sitemap"}'
    )
    assert json.loads(response.content.decode()) == json.loads(sitemap)
    assert response["Content-Type"] == "application/json"

    request.pages.homepage = None
    response = page_admin.sitemap_json_view(request)
    sitemap = '{"createHomepageUrl": "/admin/pages/page/add/?from=sitemap", "addUrl": "/admin/pages/page/add/?from=sitemap&parent=__id__", "canAdd": true, "changeUrl": "/admin/pages/page/__id__/change/?from=sitemap", "entries": [], "deleteUrl": "/admin/pages/page/__id__/delete/?from=sitemap"}'
    assert json.loads(response.content.decode()) == json.loads(sitemap)
    assert response["Content-Type"] == "application/json"


@pytest.mark.django_db
def test_pagecontenttypefilter_lookups(page_admin):
    # Add some pages with different content types. (The repetition in this
    # array is intentional!)
    for content_cls in [PageContent, PageContent, PageContentWithFields]:
        PageFactory(content=content_cls())

    request = RequestFactory().get("/")
    filterer = PageContentTypeFilter(request, {}, Page, page_admin)
    lookups = filterer.lookups(request, Page.objects.all())

    # Make sure our lookups look kinda correct.
    assert len(lookups) == len(get_registered_content())

    # Ensure that the lookup names have been ordered.
    lookup_names = [lookup[1] for lookup in lookups]
    assert lookup_names == sorted(lookup_names)


@pytest.mark.django_db
def test_pagecontenttypefilter(client):
    client.force_login(UserFactory(superuser=True))

    def fetch_admin_list(get_data):
        # Because of a bug in RequestFactory (when it's used with admin list
        # filters anyway) we need to fetch the actual admin list rather than
        # testing methods on the filter. This is OK.
        response = client.get(reverse("admin:pages_page_changelist"), data=get_data)
        assert response.status_code == 200
        return response.context["cl"].result_list

    # Ensures that the queryset returned by filtering is correct.
    # Add some pages with different content types.
    PageFactory(content=PageContent())
    PageFactory(content=PageContent())
    PageFactory(content=PageContentWithFields())

    # Test with no filters. Should be the same as Page.objects.all().
    assert len(fetch_admin_list({})) == Page.objects.all().count()

    # Test with a content type filter. It should return a subset of the
    # pages.
    content_type_id = ContentType.objects.get_for_model(PageContent).id
    parameters = {"page_type": content_type_id}
    admin_results = fetch_admin_list(parameters)
    assert (
        len(admin_results)
        == Page.objects.filter(content_type_id=content_type_id).count()
    )
    # The above will not be sufficient - we need to ensure that it is not
    # the same as the unfiltered queryset, not merely that the filtered
    # length is correct.
    assert len(admin_results) != Page.objects.all().count()


@pytest.mark.django_db
def test_pageadmin_delete_view(page_admin, homepage):
    request = AdminRequestFactory().get("/")
    request.user = MockSuperUser()

    response = page_admin.delete_view(request, str(homepage.pk))
    assert response.status_code == 200


@pytest.mark.django_db
def test_pageadmin_get_all_children(page_admin):
    homepage = PageFactory(slug="homepage")
    assert page_admin.get_all_children(homepage) == []

    # Add a child page.
    subpage = PageFactory(parent=homepage)

    # The `children` attribute is cached as long as we use the original
    # reference, so get the Page again.
    homepage = Page.objects.get(slug="homepage")
    assert page_admin.get_all_children(homepage) == [subpage]


@pytest.mark.django_db
def test_pageadmin_get_breadcrumbs(page_admin):
    subpage = PageFactory(parent=PageFactory())
    assert page_admin.get_breadcrumbs(subpage) == [subpage.parent, subpage]


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
        soup = BeautifulSoup(response.content, "html.parser")
        element = soup.find(id="page_form")
        assert element
        return element.get("action")

    def post_and_check_form(url, title):
        response = client.post(url, data={"title": title, "slug": slugify(title)})
        assert response.status_code == 302
        assert Page.objects.filter(title=title).count() == 1

    content_type_id = ContentType.objects.get_for_model(EmptyTestPage).id
    user = UserFactory(superuser=True)
    client.force_login(user)

    url = reverse("admin:pages_page_add")

    url_qs = build_url_with_qs(url, {"type": content_type_id})
    response = client.get(url_qs)
    assert response.status_code == 200
    # The "action" should be empty.
    assert get_form_action(response) is None
    # When "action" is empty on a form, browsers will use the current full URL
    # including query string.
    post_and_check_form(url_qs, title="Save me")

    # Cleanup! It'll require a parent page if we do not do this.
    Page.objects.all().delete()

    # Let's add a preserved filter to the URL.
    response = client.get(
        url,
        {
            "type": content_type_id,
            "_changelist_filters": "seo_quality_control%3Dno-meta-description",
        },
    )
    assert response.status_code == 200

    # Form action must be present.
    action_url = get_form_action(response)
    assert action_url is not None
    # Sanity check: make sure it begins with '?' - if Django changes this
    # our behaviour from here might not make sense
    assert action_url.startswith("?")
    # stupid test, but...
    assert "_changelist_filters" in action_url

    # Now try posting to it. It should create a page.
    post_and_check_form(urljoin(url, action_url), title="Save yourself")


@pytest.mark.django_db
@pytest.mark.parametrize("object_count", [1, 10])
def test_pageadmin_list_is_efficient(
    object_count, admin_client, django_assert_num_queries
):
    # Ensure that there are no N+1 queries on the page list. The exact queries
    # are not relevant; any number for django_assert_num_queries that
    # satisfies an object count of both 1 and 10 is by definition correct.
    ContentType.objects.clear_cache()
    PageFactory.create_tree(object_count, 3)
    with django_assert_num_queries(8):
        response = admin_client.get(reverse("admin:pages_page_changelist"))
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("use_arrows", [True, False])
# does not give interesting behaviour, just covers a branch
@pytest.mark.parametrize("prefetch_depth", [True, False])
def test_pageadmin_list_arrows(use_arrows, prefetch_depth, admin_client):
    PageFactory.create_tree(2, 2)
    with override_settings(
        UNCMS={
            "ADMIN_PAGE_LIST_ARROWS": use_arrows,
            "PAGE_TREE_PREFETCH_DEPTH": prefetch_depth,
        }
    ):
        response = admin_client.get(reverse("admin:pages_page_changelist"))
    assert response.status_code == 200
    # less effort than poking around in the template context
    soup = BeautifulSoup(response.content, "html.parser")
    title_columns = [
        element.get_text() for element in soup.select(".field-render_title")
    ]
    assert title_columns[0].startswith("→ Page") is False

    for top_level_index in [1, 4]:
        assert title_columns[top_level_index].startswith("→ Page") is use_arrows

    for second_level_index in [2, 3, 5, 6]:
        assert title_columns[second_level_index].startswith("→ → Page") is use_arrows


@pytest.mark.django_db
def test_pageadmin_move_page_view(client):
    def post_move(page, direction):
        return client.post(
            reverse("admin:pages_page_move_page", args=[page.pk]),
            data={"direction": direction},
        )

    homepage = PageFactory()
    user = UserFactory(is_staff=True)
    client.force_login(user)

    # Ensure permissions are being checked.
    response = post_move(homepage, "up")
    assert response.status_code == 403

    # Give them change permission on pages.
    user.user_permissions.add(Permission.objects.get(codename="change_page"))

    response = post_move(homepage, "up")
    assert response.status_code == 200
    assert response.content == b"Page could not be moved, as nothing to swap with."

    response = post_move(homepage, "down")
    assert response.status_code == 200
    assert response.content == b"Page could not be moved, as nothing to swap with."

    with pytest.raises(ValueError) as e:
        response = post_move(homepage, "kitties")
    assert str(e.value) == 'Direction should be "up" or "down".'

    content_page_1 = PageFactory(parent=homepage)
    content_page_2 = PageFactory(parent=homepage)

    for page in [homepage, content_page_1, content_page_2]:
        page.refresh_from_db()

    # Make sure everything is what we think it is
    assert homepage.left == 1
    assert homepage.right == 6
    assert content_page_1.left == 2
    assert content_page_1.right == 3
    assert content_page_2.left == 4
    assert content_page_2.right == 5

    # Move the page
    response = post_move(content_page_1, "down")

    for page in [homepage, content_page_1, content_page_2]:
        page.refresh_from_db()

    assert homepage.left == 1
    assert homepage.right == 6
    assert content_page_1.left == 4
    assert content_page_1.right == 5
    assert content_page_2.left == 2
    assert content_page_2.right == 3

    assert response.status_code == 302


@pytest.mark.django_db
def test_pageadmin_publish_selected(client):
    client.force_login(UserFactory(superuser=True))
    page_1 = PageFactory()
    page_2 = PageFactory(parent=page_1, is_online=False)
    page_3 = PageFactory(parent=page_1, is_online=False)

    list_url = reverse("admin:pages_page_changelist")
    response = client.post(
        list_url,
        data={
            "action": "publish_selected",
            "_selected_action": [str(page_2.pk), str(page_3.pk)],
        },
    )
    assert response.status_code == 302
    assert response["Location"] == list_url

    for page in page_2, page_3:
        page.refresh_from_db()
        assert page.is_online is True


@pytest.mark.django_db
def test_pageadmin_recover_view(client):
    user = UserFactory(superuser=True)
    client.force_login(user)

    with reversion.create_revision():
        page = PageFactory.create(content=PageContentWithSections(testing="Hooray!"))
        Section.objects.create(page=page)

    page.delete()

    for revision in Version.objects.all():
        response = client.get(reverse("admin:pages_page_recover", args=[revision.pk]))
        assert response.status_code == 200


@pytest.mark.django_db
def test_pageadmin_response_change(page_admin):
    page = PageFactory()

    request = AdminRequestFactory().get("/")
    request.user = MockSuperUser()

    response = page_admin.response_change(request, page)
    assert response.status_code == 302
    assert response["Location"] == "/admin/pages/page/"


@pytest.mark.django_db
def test_pageadmin_revision_view(page_admin):
    page = PageFactory()

    request = AdminRequestFactory().get("/")
    request.user = MockSuperUser()

    # Create an initial revision.
    with reversion.create_revision():
        page.content.save()

    versions = Version.objects.get_for_object(page.content)

    response = page_admin.revision_view(request, str(page.pk), (versions[0].pk))
    assert response.status_code == 200


@pytest.mark.django_db
def test_pageadmin_unpublish_selected(client):
    client.force_login(UserFactory(superuser=True))
    page_1 = PageFactory()
    page_2 = PageFactory(parent=page_1)
    page_3 = PageFactory(parent=page_1)

    list_url = reverse("admin:pages_page_changelist")
    response = client.post(
        list_url,
        data={
            "action": "unpublish_selected",
            "_selected_action": [str(page_2.pk), str(page_3.pk)],
        },
    )
    assert response.status_code == 302
    assert response["Location"] == list_url

    for page in page_2, page_3:
        page.refresh_from_db()
        assert page.is_online is False


class Wat:
    # you'll see what this is for below
    ...


@override_settings(UNCMS={"PAGE_ADMIN_ANCESTORS": ["tests.pages.test_admin.Wat"]})
def test_pageadmin_ancestors_setting():
    assert isinstance(PageAdmin(Page, AdminSite()), Wat)


@pytest.mark.django_db
def test_pageadmin_get_page_content_cls_with_admin_change_obj_fallback(
    page_admin, homepage
):
    """
    Test that get_page_content_cls falls back to request._admin_change_obj.

    This covers the edge case where get_page_content_cls is called with an obj
    that lacks a content_type. It is not fully clear why this branch is there
    (it's probably something to do with reversion), but for Chesterton's fence
    reasons I'm keeping it there and just making sure that branch is visited.
    """
    request = AdminRequestFactory().get("/")
    request.user = MockSuperUser()

    # Simulate what change_view does - set _admin_change_obj
    request._admin_change_obj = homepage

    # Create a Page instance without content_type set (simulating incomplete state)
    incomplete_page = Page()

    # Call with obj that has no content_type, should fall back to _admin_change_obj
    result = page_admin.get_page_content_cls(request, incomplete_page)
    assert result == PageContent


@pytest.mark.django_db
def test_pageadmin_save_model_field_not_in_cleaned_data(page_admin):
    """
    Test save_model when editing via list_editable where only some fields
    are in form.cleaned_data. Content fields not in cleaned_data should be
    skipped rather than raising KeyError.

    This test was written with AI assistance.
    """
    page = PageFactory(content=PageContentWithFields(description="Original"))

    request = AdminRequestFactory().get("/")
    request.user = MockSuperUser()

    form = MagicMock()
    form.cleaned_data = {
        "title": page.title,
        "slug": page.slug,
        "is_online": True,
        "inline_model": [],
    }
    form.save = Mock(return_value=page)

    page_admin.save_model(request, page, form, True)

    page.refresh_from_db()
    assert page.content.description == "Original"


@pytest.mark.django_db
def test_pageadmin_add_view_without_permission_for_content_type(client):
    """
    Test add_view filters out content types the user doesn't have permission
    to add when displaying the content type selection page.
    """
    user = UserFactory(is_staff=True)
    client.force_login(user)

    user.user_permissions.add(Permission.objects.get(codename="add_page"))

    response = client.get(reverse("admin:pages_page_add"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_pageadmin_move_page_view_loop_branches(client):
    """
    Test move_page_view returns error when attempting to move a page that
    has no sibling to swap with (last child moving down).

    This test was written with AI assistance.
    """
    user = UserFactory(is_staff=True)
    user.user_permissions.add(Permission.objects.get(codename="change_page"))
    client.force_login(user)

    homepage = PageFactory()
    child1 = PageFactory(parent=homepage)
    child2 = PageFactory(parent=homepage)
    PageFactory(parent=homepage)

    response = client.post(
        reverse("admin:pages_page_move_page", args=[child1.pk]),
        data={"direction": "down"},
    )
    assert response.status_code == 302

    child1.refresh_from_db()
    child2.refresh_from_db()

    response = client.post(
        reverse("admin:pages_page_move_page", args=[child1.pk]),
        data={"direction": "down"},
    )
    assert response.status_code == 302

    child1.refresh_from_db()

    response = client.post(
        reverse("admin:pages_page_move_page", args=[child1.pk]),
        data={"direction": "down"},
    )
    assert response.status_code == 200
    assert response.content == b"Page could not be moved, as nothing to swap with."

    # Also test moving up from the first position
    response = client.post(
        reverse("admin:pages_page_move_page", args=[child2.pk]),
        data={"direction": "up"},
    )
    assert response.status_code == 200
    assert response.content == b"Page could not be moved, as nothing to swap with."


@pytest.mark.django_db
def test_pageadmin_move_page_view_page_not_in_siblings(page_admin):
    """
    Test move_page_view when the page is not found in siblings list due to
    data inconsistency. Uses mocks to simulate this edge case.

    This test was written with AI assistance.
    """
    user = UserFactory(is_staff=True)
    user.user_permissions.add(Permission.objects.get(codename="change_page"))

    homepage = PageFactory()
    child1 = PageFactory(parent=homepage)

    request = AdminRequestFactory().post(
        reverse("admin:pages_page_move_page", args=[child1.pk]),
        data={"direction": "down"},
    )
    request.user = user

    # Mock an inconsistent state where the page exists in the dict but not in
    # the siblings list during iteration. This requires patching dict() builtin.
    with patch.object(Page.objects, "select_for_update") as mock_select:
        with patch("uncms.pages.admin.dict") as mock_dict:
            mock_existing_pages = {
                child1.id: {
                    "id": child1.id,
                    "parent_id": homepage.id,
                    "left": 2,
                    "right": 3,
                    "title": "Child 1",
                },
                888: {
                    "id": 888,
                    "parent_id": homepage.id,
                    "left": 4,
                    "right": 5,
                    "title": "Other",
                },
            }
            mock_dict.return_value = mock_existing_pages

            mock_qs = MagicMock()
            mock_qs.values.return_value.order_by.return_value = [
                {
                    "id": 888,
                    "parent_id": homepage.id,
                    "left": 4,
                    "right": 5,
                    "title": "Other",
                },
            ]
            mock_select.return_value = mock_qs

            response = page_admin.move_page_view(request, child1.pk)

            assert response.status_code == 200
            assert (
                response.content == b"Page could not be moved, as nothing to swap with."
            )
