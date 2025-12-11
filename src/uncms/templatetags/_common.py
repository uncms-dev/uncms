"""Template tags used for processing HTML."""

from typing import Any

from django.conf import settings
from django.contrib import admin
from django.db import connection
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from uncms.conf import defaults
from uncms.html import process_html


def html(text):
    """
    Runs the given HTML through UNCMS['HTML_OUTPUT_FORMATTERS'] and then
    UNCMS['HTML_CLEANERS'].
    """
    if not text:
        return ""
    text = process_html(text)
    return mark_safe(text)


def get_pagination_context(request, page_obj, pagination_key=None):
    """
    Gets page context necessary to render the given paginator object.
    """
    return {
        "page_obj": page_obj,
        "page_range": page_obj.paginator.page_range[:10],
        "paginator": page_obj.paginator,
        "pagination_key": pagination_key
        or getattr(page_obj, "_pagination_key", "page"),
        # necessary for pagination_url to work
        "request": request,
        # Will be changed later on.
        "show_query_count": False,
    }


def get_edit_bar_context(context: dict[str, Any]) -> dict[str, Any] | None:
    """
    Given a template `context`, returns the things necessary for rendering the
    edit bar.
    """
    request = context["request"]

    # Don't show to non-admins.
    if not request.user.is_staff or not request.user.is_active:
        return None

    # If "object" is in the context, we'll get the edit page for that.
    # Otherwise, if we have a page in our context, show the one for the
    obj = context.get("object", request.pages.current)
    new_context = {
        "admin_index_url": reverse("admin:index"),
        "admin_logout_url": reverse("admin:logout"),
        "site_name": defaults.SITE_NAME,
        # Note that here and elsewhere in this function we do the translations
        # of text here. That permits the Django and Jinja2 versions of the
        # templates to be byte-for-byte identical, which eases maintenance.
        "admin_link_text": _("Admin"),
        "log_out_text": _("Log out"),
        "hide_bar_text": _("Hide bar"),
        "request": request,
        "csrf_token": context.get("csrf_token"),
    }
    if obj:
        if modeladmin := admin.site._registry.get(obj.__class__):
            new_context["verbose_model_name"] = obj._meta.verbose_name
            verbose_model_name = obj._meta.verbose_name
            model_name = obj._meta.model_name
            app_label = obj._meta.app_label

            if modeladmin.has_change_permission(request, obj=obj):
                # Black will make this look worse
                # fmt:off
                new_context.update({
                    "admin_change_url": reverse(f"admin:{app_label}_{model_name}_change", args=[obj.pk]),
                    "admin_change_text": _("Edit %(model_name)s" % {"model_name": verbose_model_name})
                })
                # fmt:on

            if modeladmin.has_add_permission(request):
                # fmt:off
                new_context.update({
                    "admin_add_url": reverse(f"admin:{app_label}_{model_name}_add"),
                    "admin_add_text": _("Add %(model_name)s" % {"model_name": verbose_model_name})
                })
                # fmt:on

    # Only show the query count in local development (the only time when DEBUG
    # should ever be on).
    if settings.DEBUG:
        new_context["show_query_count"] = True
        new_context["query_count"] = len(connection.queries)
        new_context["query_count_text"] = _(
            "%(query_count)s queries" % {"query_count": len(connection.queries)}
        )
    return new_context
