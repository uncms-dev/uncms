from django import template
from django.urls import reverse

from uncms.pages import get_page_model

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
    user = context['request'].user
    can_change = user.has_perm('pages.change_page')
    can_view = user.has_perm('pages.view_page') or can_change

    def sitemap_entry(page):
        return {
            'admin_url': reverse('admin:pages_page_change', args=[page.pk]),
            'can_move': can_change,
            'can_view': can_view,
            'children': [sitemap_entry(child_page) for child_page in page.get_children()],
            'id': page.pk,
            'in_navigation': page.in_navigation,
            'is_homepage': page.parent_id is None,
            'is_online': page.is_online,
            'title': str(page),
        }

    return {
        # Note that we must not use request.pages here - we want to be able
        # to render the sitemap after it has changed.
        'pages': [sitemap_entry(get_page_model().objects.get_homepage())]
    }


@register.inclusion_tag('pages/title.html', takes_context=True)
def render_title(context, browser_title=None):
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
    request = context['request']
    page = request.pages.current
    return {
        'title': (
            browser_title or
            context.get('title') or
            (page and page.browser_title) or
            (page and page.title) or
            ''
        ),
    }
