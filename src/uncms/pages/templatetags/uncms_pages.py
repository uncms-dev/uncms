from django import template
from django.urls import reverse

from uncms.conf import defaults
from uncms.pages import get_page_model
from uncms.pages.templatetags._common import (
    get_breadcrumbs_context,
    get_breadcrumbs_obj,
    get_canonical_url,
    get_meta_description,
    get_meta_robots,
    get_og_description,
    get_og_image,
    get_og_title,
    get_page_url,
    render_navigation,
)

register = template.Library()


@register.simple_tag(takes_context=True)
def admin_sitemap_entries(context):
    """
    admin_sitemap_entries returns the full page tree, bypassing
    any caching mechanisms, does not exclude entries that are not in the
    navigation, and adds `can_move` and `can_view` attributes. It is intended
    for cases where the tree might change over the course of a request, and
    only for admin users.

    You should use this tag for rendering a sitemap in the admin.
    """
    user = context["request"].user
    can_change = user.has_perm("pages.change_page")
    can_view = user.has_perm("pages.view_page") or can_change
    page_model = get_page_model()

    def sitemap_entry(page):
        return {
            "admin_url": reverse("admin:pages_page_change", args=[page.pk]),
            "can_move": can_change,
            "can_view": can_view,
            "children": [
                sitemap_entry(child_page) for child_page in page.get_children()
            ],
            "id": page.pk,
            "in_navigation": page.in_navigation,
            "is_homepage": page.parent_id is None,
            "is_online": page.is_online,
            "title": str(page),
        }

    try:
        # Note that we must not use request.pages here; that has all sorts of
        # optimisations in place which we do not want.
        homepage = page_model.objects.get_homepage()
    except page_model.DoesNotExist:
        pages = []
    else:
        pages = [sitemap_entry(homepage)]
    return {
        "pages": pages,
    }


@register.inclusion_tag(
    defaults.BREADCRUMBS_TEMPLATE.format(extension="html"), takes_context=True
)
def breadcrumbs(
    context,
    breadcrumbs_obj=None,
    *,
    auto_extend=True,
    show_tail=None,
    class_prefix="breadcrumbs",
):
    return get_breadcrumbs_context(
        context,
        breadcrumbs_obj,
        auto_extend=auto_extend,
        show_tail=show_tail,
        class_prefix=class_prefix,
    )


@register.simple_tag(takes_context=True)
def canonical_url(context):
    return get_canonical_url(context)


@register.simple_tag(takes_context=True)
def get_breadcrumbs(
    context, *, breadcrumb_list=None, auto_extend=True, extend_with=None
):
    return get_breadcrumbs_obj(
        context,
        breadcrumb_list=breadcrumb_list,
        auto_extend=auto_extend,
        extend_with=extend_with,
    )


@register.simple_tag(takes_context=True)
def meta_description(context):
    return get_meta_description(context)


@register.simple_tag(takes_context=True)
def meta_robots(context, index=None, follow=None, archive=None):
    return get_meta_robots(context, index=index, follow=follow, archive=archive)


@register.inclusion_tag("pages/navigation/navigation.html", takes_context=True)
def navigation(context, pages, section=None, class_prefix=None, **templates):
    return render_navigation(
        context, pages, section=section, class_prefix=class_prefix, **templates
    )


@register.simple_tag(takes_context=True)
def og_description(context):
    return get_og_description(context)


@register.simple_tag(takes_context=True)
def og_image(context):
    return get_og_image(context)


@register.simple_tag(takes_context=True)
def og_title(context):
    return get_og_title(context)


@register.simple_tag
def page_url(
    page, view_func=None, *args, **kwargs
):  # pylint:disable=keyword-arg-before-vararg
    return get_page_url(page, view_func=view_func, *args, **kwargs)


@register.inclusion_tag("pages/title.html", takes_context=True)
def title(context, browser_title=None):
    """
    Renders the title of the current page:

        {% title %}

    You can override the title by setting a context variable called 'title':

        {% with "foo" as title %}
            {% title %}
        {% endwith %}

    You can also provide the title as an argument to this tag::

        {% title "foo" %}

    """
    request = context["request"]
    page = request.pages.current
    return {
        "title": (
            browser_title
            or context.get("title")
            or (page and page.browser_title)
            or (page and page.title)
            or ""
        ),
    }
