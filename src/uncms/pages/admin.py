"""
The UnCMS pages admin app.

This mostly takes care of patching the fields from content models into the
page form, including registering inlines. It also gives you a totally
different page for "add a page", which gives you a list of page types with
their icons.
"""
import itertools
from functools import cmp_to_key
from urllib.parse import parse_qs, urlencode

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.options import IS_POPUP_VAR
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_permission_codename
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.db.models import F
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import capfirst
from django.urls import path, reverse
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from watson.search import search_context_manager

from uncms.admin import PageBaseAdmin
from uncms.conf import defaults
from uncms.pages.models import Page, PageSearchAdapter, get_registered_content

# Used to track references to and from the JS sitemap.
PAGE_FROM_KEY = "from"
PAGE_FROM_SITEMAP_VALUE = "sitemap"


# The GET parameter used to indicate content type on page creation.
PAGE_TYPE_PARAMETER = "type"


class PageContentTypeFilter(admin.SimpleListFilter):
    """Enables filtering of pages by their content type."""

    title = _("page type")

    parameter_name = "page_type"

    def lookups(self, request, model_admin):
        lookups = []
        content_types = ContentType.objects.get_for_models(*get_registered_content())
        for key, value in content_types.items():
            lookups.append((value.id, capfirst(key._meta.verbose_name)))
        lookups.sort(key=lambda item: item[1])
        return lookups

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(content_type_id=int(self.value()))
        return queryset


class PageAdmin(PageBaseAdmin):
    """Admin settings for Page models."""

    list_display = (
        "render_title",
        "render_content_type",
        "is_online",
    )
    list_display_links = ["render_title"]

    list_editable = ("is_online",)

    list_filter = PageBaseAdmin.list_filter + (PageContentTypeFilter,)

    new_fieldsets = [
        (
            None,
            {
                "fields": ("title", "slug", "parent"),
            },
        ),
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
                "fields": ("short_title", "in_navigation", "hide_from_anonymous"),
                "classes": ("collapse",),
            },
        ),
        (
            "Security",
            {"fields": ("requires_authentication",), "classes": ("collapse",)},
        ),
    ]

    new_fieldsets.extend(PageBaseAdmin.fieldsets)

    removed_fieldsets = [
        new_fieldsets.index(PageBaseAdmin.TITLE_FIELDS),
        new_fieldsets.index(PageBaseAdmin.PUBLICATION_FIELDS),
    ]

    fieldsets = []

    for k, v in enumerate(new_fieldsets):
        if k not in removed_fieldsets:
            fieldsets.append(v)

    search_adapter_cls = PageSearchAdapter

    def _register_page_inline(self, model):
        """Registers the given page inline with reversion."""
        self._reversion_autoregister(model, follow=["page"])

    def __new__(cls, *args, **kwargs):
        """
        This is bad code which should not exist. It dynamically composes
        PageAdmin based on ancestors in the PAGE_ADMIN_ANCESTORS configuration
        item. Friends don't let friends use __new__.

        This has been added because of one thing: adminsortable2. It insists
        that its sortable inlines can only be registered to some other
        ModelAdmin which inherits from SortableAdminBase. We're not going to make
        adminsortable2 a requirement of UnCMS just in case someone wants to
        use it in their projects. But we can add an extension point for people
        who want to use it.

        The other option would be to have a local PageAdmin in a project. But
        then `page_admin.register_content_inline` would not work anymore. This
        seems like the most "consumer" friendly way of implementing this.
        """
        composed = type(
            "PageAdmin",
            tuple(
                itertools.chain(
                    # Compose a class made of everything from the
                    # PAGE_ADMIN_ANCESTORS setting...
                    [
                        import_string(ancestor)
                        for ancestor in defaults.PAGE_ADMIN_ANCESTORS
                    ],
                    # ...with this class.
                    (cls,),
                ),
            ),
            {},
        )
        return super().__new__(composed)

    def __init__(self, *args, **kwargs):
        """Initialzies the PageAdmin."""
        super().__init__(*args, **kwargs)
        # Prepare to register some content inlines.
        self.content_inlines = []
        # Register all page inlines.
        for content_cls in get_registered_content():
            self._register_page_inline(content_cls)

    def register_content_inline(self, content_cls, inline_admin):
        """Registers an inline model with the page admin."""
        self.content_inlines.append((content_cls, inline_admin))
        self._register_page_inline(inline_admin.model)

    def get_inline_instances(self, request, obj=None):
        """Returns all the inline instances for this PageAdmin."""
        inline_instances = super().get_inline_instances(request, obj=obj)
        # Add on the relevant content inlines.
        obj = getattr(
            request, "_admin_change_obj", None
        )  # HACK: Retrieve the page from the change view.
        content_cls = self.get_page_content_cls(request, obj)
        for cls, inline in self.content_inlines:
            if cls == content_cls:
                inline_instances.append(inline(self.model, self.admin_site))
        # All done!
        return inline_instances

    # Reversion
    def get_revision_instances(self, request, obj):
        """Returns all the instances to be used in this object's revision."""
        instances = [obj]
        # Add the content object.
        instances.append(obj.content)
        # Add all the content inlines.
        for _ignore, inline in self.content_inlines:
            # pass
            try:
                instances.extend(inline.model._default_manager.filter(page=obj))
            except:  # pylint:disable=bare-except
                pass
        return instances

    @staticmethod
    def get_revision_form_data(request, obj, version):
        """
        Returns a dictionary of data to set in the admin form in order to revert
        to the given revision.
        """
        data = version.field_dict
        content_version = version.revision.version_set.all().get(
            content_type=obj.content_type_id,
            object_id=obj.pk,
        )
        data.update(content_version.field_dict)
        return data

    # Plugable content types.
    @staticmethod
    def get_page_content_cls(request, obj=None):
        """Retrieves the page content type slug."""
        if obj and not hasattr(request, "_admin_change_obj"):
            request._admin_change_obj = obj

        if PAGE_TYPE_PARAMETER in request.GET:
            return ContentType.objects.get_for_id(
                request.GET[PAGE_TYPE_PARAMETER]
            ).model_class()

        if obj and hasattr(obj, "content_type") and obj.content_type:
            return obj.content_type.model_class()

        if hasattr(request, "_admin_change_obj") and hasattr(
            request._admin_change_obj, "content_type"
        ):
            return request._admin_change_obj.content_type.model_class()

        raise Http404("You must specify a page content type.")

    def get_fieldsets(self, request, obj=None):
        """Generates the custom content fieldsets."""
        content_cls = self.get_page_content_cls(request, obj)
        content_fields = [
            field.name
            for field in content_cls._meta.fields + content_cls._meta.many_to_many
            if field.name != "page"
        ]

        fieldsets = super().get_fieldsets(request, obj)
        if content_fields:
            content_fieldsets = content_cls.fieldsets or [
                (
                    "Page content",
                    {
                        "fields": content_fields,
                    },
                ),
            ]
            fieldsets = list(fieldsets[0:1]) + content_fieldsets + list(fieldsets[1:])
        return fieldsets

    def get_all_children(self, page):
        """Returns all the children for a page."""
        children = []

        def do_get_all_children(page):
            for child in page.children:
                children.append(child)
                do_get_all_children(child)

        do_get_all_children(page)
        return children

    def get_breadcrumbs(self, page):
        """Returns all breadcrumbs for a page."""
        breadcrumbs = []
        while page:
            breadcrumbs.append(page)
            page = page.parent
        breadcrumbs.reverse()
        return breadcrumbs

    def get_form(self, request, obj=None, change=False, **kwargs):
        """Adds the template area fields to the form."""
        content_cls = self.get_page_content_cls(request, obj)
        form_attrs = {}
        for field in content_cls._meta.fields + content_cls._meta.many_to_many:
            if field.name == "page":
                continue
            form_field = self.formfield_for_dbfield(field, request=request)
            # HACK: add in the initial value. No other way to pass this on.
            if obj:
                try:
                    form_field.initial = getattr(obj.content, field.name, "")
                    if (
                        isinstance(field, models.ManyToManyField)
                        and not form_field.initial == ""
                    ):
                        form_field.initial = form_field.initial.all()
                except content_cls.DoesNotExist:
                    # This means that we're in a reversion recovery, or
                    # something weird has happened to the database.
                    pass

            if field.name in getattr(content_cls, "filter_horizontal", ()):
                form_field.widget = FilteredSelectMultiple(
                    field.verbose_name,
                    is_stacked=False,
                )
            # Store the field.
            form_attrs[field.name] = form_field
        ContentForm = type(
            "{}Form".format(self.__class__.__name__), (forms.ModelForm,), form_attrs
        )
        form_defaults = {"form": ContentForm}
        form_defaults.update(kwargs)

        self.prepopulated_fields = {
            "slug": ("title",),
        }
        self.fieldsets[0][1]["fields"] = ("title", "slug", "parent")

        PageForm = super().get_form(request, obj=obj, change=change, **form_defaults)

        # HACK: Need to limit parents field based on object. This should be
        # done in formfield_for_foreignkey, but that method does not know
        # about the object instance.
        if obj:
            invalid_parents = set(child.id for child in self.get_all_children(obj))
            invalid_parents.add(obj.id)
        else:
            invalid_parents = frozenset()
        homepage = request.pages.homepage

        if homepage:
            parent_choices = []
            for page in [homepage] + self.get_all_children(homepage):
                if page.id not in invalid_parents:
                    parent_choices.append(
                        (
                            page.id,
                            " \u203a ".join(
                                "{}".format(breadcrumb.title)
                                for breadcrumb in self.get_breadcrumbs(page)
                            ),
                        )
                    )
        else:
            parent_choices = []

        if not parent_choices:
            parent_choices = (("", "---------"),)

        PageForm.base_fields["parent"].choices = parent_choices

        # Return the completed form.
        return PageForm

    def get_queryset(self, request):
        # select_related parents of pages so that checking for the parent is
        # efficient. PAGE_TREE_PREFETCH_DEPTH is a hint of how deep our
        # navigation is going to be, so use that if it's present, otherwise
        # just use the parent and parent-of-parent.
        queryset = super().get_queryset(request).select_related("content_type")
        if defaults.ADMIN_PAGE_LIST_ARROWS:
            if defaults.PAGE_TREE_PREFETCH_DEPTH:
                queryset = queryset.select_related(
                    *[
                        "__".join(["parent"] * (defaults.PAGE_TREE_PREFETCH_DEPTH + 1))
                        for i in range(defaults.PAGE_TREE_PREFETCH_DEPTH)
                    ]
                )
            else:
                queryset = queryset.select_related("parent", "parent__parent")
        return queryset

    def save_model(self, request, obj, form, change):
        """Saves the model and adds its content fields."""
        content_cls = self.get_page_content_cls(request, obj)
        content_cls_type = ContentType.objects.get_for_model(content_cls)
        # Delete the old page content, if it's expired.
        if (
            change
            and ContentType.objects.get_for_id(obj.content_type_id) != content_cls_type
        ):
            obj.content.delete()
        # Create the page content.
        obj.content_type = content_cls_type
        if change:
            try:
                content_obj = content_cls_type.model_class().objects.get(page=obj)
            except content_cls.DoesNotExist:
                content_obj = (
                    content_cls()
                )  # This means that we're in a reversion recovery, or something weird has happened to the database.
        else:
            content_obj = content_cls()
        # Modify the page content.
        for field in content_obj._meta.fields:
            if field.name == "page":
                continue
            # This will not necessarily be in the form; if you change something
            # that is `list_editable` in the changelist, for example.
            if field.name in form.cleaned_data:
                setattr(content_obj, field.name, form.cleaned_data[field.name])

        # Save the model.
        super().save_model(request, obj, form, change)
        # Save the page content.
        content_obj.page = obj
        content_obj.save()

        # Now save m2m fields.
        for field in content_obj._meta.many_to_many:
            getattr(content_obj, field.name).set(form.cleaned_data[field.name])

        obj.content = content_obj

    # Permissions.
    @staticmethod
    def has_add_content_permission(request, model):
        """Checks whether the given user can edit the given content model."""
        opts = model._meta
        return request.user.has_perm(
            "{0}.{1}".format(opts.app_label, get_permission_codename("add", opts))
        )

    def has_add_permission(self, request):
        """Checks whether the user can edits pages and at least one content model."""
        if not super().has_add_permission(request):
            return False
        for content_model in get_registered_content():
            if self.has_add_content_permission(request, content_model):
                return True
        return False

    def has_change_permission(self, request, obj=None):
        """Checks whether the user can edit the page and associated content model."""
        if not super().has_change_permission(request, obj):
            return False
        if obj:
            content_model = ContentType.objects.get_for_id(
                obj.content_type_id
            ).model_class()
            content_opts = content_model._meta
            return request.user.has_perm(
                "{0}.{1}".format(
                    content_opts.app_label,
                    get_permission_codename("change", content_opts),
                )
            )
        return True

    def has_delete_permission(self, request, obj=None):
        """Checks whether the user can delete the page and associated content model."""
        if not super().has_delete_permission(request, obj):
            return False
        if obj:
            content_model = ContentType.objects.get_for_id(
                obj.content_type_id
            ).model_class()
            content_opts = content_model._meta
            return request.user.has_perm(
                "{0}.{1}".format(
                    content_opts.app_label,
                    get_permission_codename("delete", content_opts),
                )
            )
        return True

    # Custom views.
    def patch_response_location(self, request, response):
        """Perpetuates the 'from' key in all redirect responses."""
        if isinstance(response, HttpResponseRedirect):
            if PAGE_FROM_KEY in request.GET:
                response["Location"] += "?%s=%s" % (
                    PAGE_FROM_KEY,
                    request.GET[PAGE_FROM_KEY],
                )
        return response

    def changelist_view(self, request, extra_context=None):
        """Redirects to the sitemap, if appropriate."""
        if PAGE_FROM_KEY in request.GET:
            redirect_slug = request.GET[PAGE_FROM_KEY]
            if redirect_slug == PAGE_FROM_SITEMAP_VALUE:
                return redirect("admin:index")
        return super().changelist_view(request, extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Uses only the correct inlines for the page."""
        # HACK: Add the current page to the request to pass to the get_inline_instances() method.
        page = get_object_or_404(self.model, id=object_id)
        request._admin_change_obj = page

        extra_context = {}

        # Call the change view.
        return super().change_view(
            request, object_id, form_url=form_url, extra_context=extra_context
        )

    def revision_view(self, request, object_id, version_id, extra_context=None):
        """Load up the correct content inlines."""
        # HACK: Add the current page to the request to pass to the get_inline_instances() method.
        page = get_object_or_404(self.model, id=object_id)
        request._admin_change_obj = page
        # Call the change view.
        return super().revision_view(request, object_id, version_id, extra_context)

    def add_view(self, request, form_url="", extra_context=None):
        """Ensures that a valid content type is chosen."""
        if PAGE_TYPE_PARAMETER not in request.GET:
            # Generate the available content items.
            content_items = get_registered_content()

            def cmp_function(a, b):
                return (a.classifier > b.classifier) - (
                    a.classifier < b.classifier
                ) or (a._meta.verbose_name.lower() > b._meta.verbose_name.lower()) - (
                    a._meta.verbose_name.lower() < b._meta.verbose_name.lower()
                )

            content_items.sort(key=cmp_to_key(cmp_function))
            content_types = []
            for content_type in content_items:
                if self.has_add_content_permission(request, content_type):
                    # If we get this far, then we have permisison to add a page of this type.
                    get_params = request.GET.copy()
                    get_params[PAGE_TYPE_PARAMETER] = ContentType.objects.get_for_model(
                        content_type
                    ).id
                    query_string = get_params.urlencode()
                    content_url = request.path + "?" + query_string
                    content_type_context = {
                        "name": content_type._meta.verbose_name,
                        "icon": staticfiles_storage.url(content_type.icon),
                        "url": content_url,
                        "classifier": content_type.classifier,
                    }
                    content_types.append(content_type_context)
            # Shortcut for when there is a single content type.
            if len(content_types) == 1:
                return redirect(content_types[0]["url"])
            # Render the select page template.
            context = {
                **self.admin_site.each_context(request),
                "title": "Select page type",
                "content_types": content_types,
                "is_popup": request.GET.get(IS_POPUP_VAR, False),
                "opts": self.model._meta,
                "add": True,
                "has_view_permission": self.has_view_permission(request, obj=None),
            }

            return render(request, "admin/pages/page/select_page_type.html", context)

        if not self.has_add_content_permission(
            request,
            ContentType.objects.get_for_id(
                request.GET[PAGE_TYPE_PARAMETER]
            ).model_class(),
        ):
            raise PermissionDenied(
                "You are not allowed to add pages of that content type."
            )
        return super().add_view(request, form_url, extra_context)

    def get_preserved_filters(self, request):
        """
        This is fixes an issue wherein if there were preserved filters from
        the list view,the type of page being saved would not be passed to the
        form action of the change form.

        This mean that on posting, the admin would think the user was on
        the page type selection page and not trying to save the form.
        We just need to add the PAGE_TYPE_PARAMETER to the form action if
        there are preserved filters.

        For more info see: https://github.com/onespacemedia/osm-jet/issues/11
        """
        preserved_filters = super().get_preserved_filters(request)

        if preserved_filters and request.GET.get(PAGE_TYPE_PARAMETER):
            # it seems like get_preserved_filters really should be a dict,
            # not a query string smooshed together, but...
            filters_dict = parse_qs(preserved_filters)
            filters_dict[PAGE_TYPE_PARAMETER] = request.GET[PAGE_TYPE_PARAMETER]
            preserved_filters = urlencode(filters_dict)

        return preserved_filters

    def recover_view(self, request, version_id, extra_context=None):
        """
        Stop Watson from trying to index the page during recovery (a situation
        where PageInstance.content does not exist).

        From this unmerged PR: https://github.com/onespacemedia/cms/pull/195
        """
        search_context_manager.invalidate()
        return super().recover_view(request, version_id, extra_context=extra_context)

    @admin.display(description=_("Content type"), ordering="content_type__model")
    def render_content_type(self, obj):
        if not obj.content_type:
            # no-covered because this can only happen in really weird
            # situations
            return None  # pragma: no cover
        return capfirst(obj.content_type.model_class()._meta.verbose_name)

    @admin.display(description=_("Page"))
    def render_title(self, obj):
        """
        `render_title` renders arrows in the page title to indicate the depth
        and parent of the page.

        For example, if we have a home page, a top-level page called "Cats"
        with three children "Black" "Tabby" and "Calico", their titles will be
        displayed as:

        Home
        → Cats
        → → Black
        → → Tabby
        → → Calico
        """
        if not defaults.ADMIN_PAGE_LIST_ARROWS:
            return str(obj)

        canary = 0
        fmt = str(obj)
        parent = obj.parent
        while parent:
            fmt = f"→ {fmt}"
            parent = parent.parent
            canary += 1
            if canary > 20:
                # More than 20 level deep navigation probably implies a
                # problem and that our page tree is garbaged. In the legit
                # case, it means they don't have arrows shown for more than
                # 20 level deep pages. In the case where it has gotten
                # garbaged, we don't deprive them of the use of the admin to
                # fix it :)
                break  # pragma: no cover
        return fmt

    def response_add(self, request, obj, post_url_continue=None):
        """Redirects to the sitemap if appropriate."""
        response = super().response_add(request, obj, post_url_continue)
        return self.patch_response_location(request, response)

    def response_change(self, request, obj):
        """Redirects to the sitemap if appropriate."""
        response = super().response_change(request, obj)
        return self.patch_response_location(request, response)

    def delete_view(self, request, object_id, extra_context=None):
        """Redirects to the sitemap if appropriate."""
        response = super().delete_view(request, object_id, extra_context)
        return self.patch_response_location(request, response)

    def get_urls(self):
        """Adds in some custom admin URLs."""
        admin_view = self.admin_site.admin_view
        return [
            path(
                "sitemap.json",
                admin_view(self.sitemap_json_view),
                name="pages_page_sitemap_json",
            ),
            path(
                "move-page/<page_id>/",
                admin_view(self.move_page_view),
                name="pages_page_move_page",
            ),
        ] + super().get_urls()

    def sitemap_json_view(self, request):
        """Returns a JSON data structure describing the sitemap."""
        # Get the homepage.
        homepage = request.pages.homepage
        # Compile the initial data.
        data = {
            "canAdd": self.has_add_permission(request),
            "createHomepageUrl": reverse("admin:pages_page_add")
            + "?{0}={1}".format(PAGE_FROM_KEY, PAGE_FROM_SITEMAP_VALUE),
            "addUrl": reverse("admin:pages_page_add")
            + "?{0}={1}&parent=__id__".format(PAGE_FROM_KEY, PAGE_FROM_SITEMAP_VALUE),
            "changeUrl": reverse("admin:pages_page_change", args=("__id__",))
            + "?{0}={1}".format(PAGE_FROM_KEY, PAGE_FROM_SITEMAP_VALUE),
            "deleteUrl": reverse("admin:pages_page_delete", args=("__id__",))
            + "?{0}={1}".format(PAGE_FROM_KEY, PAGE_FROM_SITEMAP_VALUE),
        }
        # Add in the page data.
        if homepage:

            def sitemap_entry(page):
                children = []
                for child in page.children:
                    children.append(sitemap_entry(child))
                return {
                    "isOnline": page.is_online,
                    "id": page.id,
                    "title": str(page),
                    "children": children,
                    "canChange": self.has_change_permission(request, page),
                    "canDelete": self.has_delete_permission(request, page),
                    "moveUrl": reverse("admin:pages_page_move_page", args=[page.pk]),
                }

            data["entries"] = [sitemap_entry(homepage)]
        else:
            data["entries"] = []
        return JsonResponse(data)

    @transaction.atomic
    def move_page_view(self, request, page_id):
        """Moves a page up or down."""
        # Check that the user has permission to move pages.
        if not self.has_change_permission(request):
            return HttpResponseForbidden(
                "You do not have permission to move this page."
            )

        # Lock entire table.
        existing_pages_list = (
            Page.objects.select_for_update()
            .values("id", "parent_id", "left", "right", "title")
            .order_by("left")
        )
        existing_pages = dict((page["id"], page) for page in existing_pages_list)

        # Get the page.
        page = existing_pages[int(page_id)]
        parent_id = page["parent_id"]

        # Get all the siblings.
        siblings = [s for s in existing_pages_list if s["parent_id"] == parent_id]

        # Find the page to swap.
        direction = request.POST["direction"]

        if direction == "up":
            siblings.reverse()
        elif direction == "down":
            pass
        else:
            raise ValueError('Direction should be "up" or "down".')

        sibling_iter = iter(siblings)
        for sibling in sibling_iter:
            if sibling["id"] == page["id"]:
                break
        try:
            other_page = next(sibling_iter)
        except StopIteration:
            return HttpResponse("Page could not be moved, as nothing to swap with.")

        # Put the pages in order.
        first_page, second_page = sorted((page, other_page), key=lambda p: p["left"])

        # Excise the first page.
        Page.objects.filter(
            left__gte=first_page["left"], right__lte=first_page["right"]
        ).update(
            left=F("left") * -1,
            right=F("right") * -1,
        )

        # Move the other page.
        branch_width = first_page["right"] - first_page["left"] + 1
        Page.objects.filter(
            left__gte=second_page["left"], right__lte=second_page["right"]
        ).update(
            left=F("left") - branch_width,
            right=F("right") - branch_width,
        )

        # Put the page back in.
        second_branch_width = second_page["right"] - second_page["left"] + 1
        Page.objects.filter(
            left__lte=-first_page["left"], right__gte=-first_page["right"]
        ).update(
            left=(F("left") - second_branch_width) * -1,
            right=(F("right") - second_branch_width) * -1,
        )

        # if we've managed to POST, "next" should always be safe (if we've
        # managed to do a POST with an attacker-supplied URL we've got other
        # problems like CSRF protection not working)
        next_url = request.POST.get("next") or reverse("admin:index")
        messages.success(request, f"Page was moved {direction}")
        return redirect(next_url)

    @admin.display(description=_("Place selected %(verbose_name_plural)s online"))
    def publish_selected(self, request, queryset):
        """
        publish_selected (and also unpublish_selected) on this ModelAdmin are
        overrides of the OnlineBaseAdmin methods of the same name. This is
        because using `.update` as OnlineBaseAdmin does, does not go through
        the save method, and the save method does a bunch of things to ensure
        that the page tree is in a sane state.

        Instead, we do it the slow way of looping through each instance and
        calling save().
        """
        for obj in queryset:
            obj.is_online = True
            obj.save()

    @admin.display(description=_("Take selected %(verbose_name_plural)s offline"))
    def unpublish_selected(self, request, queryset):
        for obj in queryset:
            obj.is_online = False
            obj.save()


admin.site.register(Page, PageAdmin)
page_admin = admin.site._registry[Page]
