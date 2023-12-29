"""
Template tags used to render pages.

The body of the code is broken out into this "common" file because we support
Jinja2. Both Jinja2 and Django template functions & filters shall be thin
wrappers around these.
"""
from django.utils.html import escape

from uncms.conf import defaults
from uncms.media.models import File
from uncms.pages import get_page_model
from uncms.pages.types import Breadcrumbs
from uncms.utils import canonicalise_url


# Navigation.
def _navigation_entries(context, pages, section=None, json_safe=False):
    request = context['request']
    # Compile the entries.

    def page_entry(page):
        # Do nothing if the page is to be hidden from not logged in users
        if page.hide_from_anonymous and not request.user.is_authenticated:
            return None

        url = page.get_absolute_url()
        entry = {
            'url': url,
            'title': str(page),
            'here': request.path.startswith(url),
            'current': page == request.pages.current,
            'children': [
                page_entry(x) for x in page.navigation
                if page is not request.pages.homepage
            ],
        }

        if not json_safe:
            entry['page'] = page

        return entry

    # All the applicable nav items
    entries = [page_entry(x) for x in pages if page_entry(x) is not None]

    # Add the section.
    if section:
        section_entry = page_entry(section)
        section_entry['here'] = context['request'].pages.current == section_entry['page']
        entries = [section_entry] + list(entries)

    return entries


def render_navigation(context, pages, section=None, class_prefix=None, **templates):
    """
    Renders a navigation list for the given pages.
    """
    return {
        'navigation': _navigation_entries(context, pages, section),
        'prefix': class_prefix or defaults.NAVIGATION_CLASS_PREFIX,
        'item_template': templates.get('item_template', defaults.NAVIGATION_ITEM_TEMPLATE),
        'submenu_template': templates.get('submenu_template', defaults.NAVIGATION_SUBMENU_TEMPLATE),
        'submenu_item_template': templates.get('submenu_item_template', defaults.NAVIGATION_SUBMENU_ITEM_TEMPLATE),
    }


def get_breadcrumbs_obj(context, *, breadcrumb_list=None, auto_extend=True, extend_with=None):
    if breadcrumb_list is None:
        items = context['request'].pages.breadcrumbs
    else:
        items = breadcrumb_list

    if auto_extend and 'object' in context:
        obj_extension = context['object']
    else:
        obj_extension = []

    return Breadcrumbs.from_objects(items, obj_extension, extend_with or [])


def get_breadcrumbs_context(context, breadcrumbs_obj=None, *, auto_extend=True, show_tail=None, class_prefix=None):
    if not breadcrumbs_obj:
        breadcrumbs_obj = get_breadcrumbs_obj(context, auto_extend=auto_extend)

    if show_tail is None:
        show_tail = defaults.BREADCRUMBS_SHOW_TAIL

    items = breadcrumbs_obj.items

    # Never show a completely empty breadcrumb trail, if we have a home page.
    if not show_tail:
        items = items[:-1]

    if class_prefix is None:
        class_prefix = defaults.BREADCRUMBS_CLASS_PREFIX

    return {
        'count': len(items),
        'breadcrumbs': items,
        'show_tail': show_tail,
        'class_prefix': class_prefix,
    }


def get_page_url(page, view_func=None, *args, **kwargs):  # pylint:disable=keyword-arg-before-vararg
    """
    Returns the URL of the given view func in the given page.
    """
    url = None
    page_model = get_page_model()

    if isinstance(page, int):
        try:
            page = page_model.objects.get(pk=page)
        except page_model.DoesNotExist:
            url = '#'
            page = None
    if page is None:
        url = '#'
    else:
        # Get the page URL.
        if view_func is None:
            url = page.get_absolute_url()
        else:
            url = page.reverse(view_func, args, kwargs)
    # Return the value, or set as a context variable as appropriate.
    return escape(url)


# Page widgets.
def get_meta_description(context):
    """
    Renders the content of the meta description tag for the current page.
    """
    if context.get('meta_description'):
        return context['meta_description']

    page = context['request'].pages.current
    if page and page.meta_description:
        return page.meta_description

    return ''


def get_meta_robots(context, index=None, follow=None, archive=None):
    """
    Returns the content of the meta robots tag for the current page::
    """

    # Override with context variables. These will be set by any detail view
    # which inherits from SearchMetaDetailMixin.
    if index is None:
        index = context.get('robots_index')
    if follow is None:
        follow = context.get('robots_follow')
    if archive is None:
        archive = context.get('robots_archive')

    # Try to get the values from the current page.
    page = context['request'].pages.current

    if page:
        if index is None:
            index = page.robots_index
        if follow is None:
            follow = page.robots_follow
        if archive is None:
            archive = page.robots_archive

    # Final override, set to True.
    if index is None:
        index = True
    if follow is None:
        follow = True
    if archive is None:
        archive = True

    # Generate the meta content.
    robots = ', '.join((
        index and 'INDEX' or 'NOINDEX',
        follow and 'FOLLOW' or 'NOFOLLOW',
        archive and 'ARCHIVE' or 'NOARCHIVE',
    ))
    return robots


def get_canonical_url(context):
    '''
    Returns the canonical URL of the current page, normalised for the correct
    protocol, path and PREPEND_WWW setting.
    '''
    return canonicalise_url(context['request'].path)


def get_og_title(context):
    # Always prefer a title override from the context.
    if context.get('og_title'):
        return context['og_title']

    # See if the current object has either an og_title or title attribute,
    # in that order.
    obj = context.get('object', None)
    if obj:
        for field_name in ['og_title', 'title']:
            title = getattr(obj, field_name, None)
            if title:
                return title

    request = context['request']
    page = request.pages.current

    if page:
        return page.og_title or page.browser_title or page.title

    return context.get('title', '')


def get_og_description(context, description=None):
    if not description:
        description = context.get('og_description')

    if not description:
        request = context['request']
        page = request.pages.current

        if page:
            description = page.og_description

    return escape(description or '')


def get_og_image(context):
    """
    Returns an OpenGraph image URL guessed from the current template context.
    """
    # See if it is in the context, most likely placed there by
    # SearchMetaDetailMixin.
    if context.get('og_image'):
        return canonicalise_url(context['og_image'].get_absolute_url())

    # Has there been an 'og_image_url' placed in the context? Prefer that.
    # That allows views to place a fallback for when administrators have not
    # explicitly specified one.
    if context.get('og_image_url'):
        return canonicalise_url(context['og_image_url'])

    obj = context.get('object')

    if obj:
        for field_name in ['image', 'photo']:
            field = getattr(obj, field_name, None)

            # Only return this if it is an UnCMS `File` - we don't want to
            # guess much more than this.
            if isinstance(field, File):
                return canonicalise_url(field.get_absolute_url())

    page = context['request'].pages.current

    if page and page.og_image:
        return canonicalise_url(page.og_image.get_absolute_url())

    if defaults.OPENGRAPH_FALLBACK_IMAGE:
        return canonicalise_url(defaults.OPENGRAPH_FALLBACK_IMAGE)

    return ''


def render_title(context, browser_title=None):
    '''
    Renders the title of the current page::

        {% title %}

    You can override the title by setting a context variable called 'title'::

        {% with "foo" as title %}
            {% title %}
        {% endwith %}

    You can also provide the title as an argument to this tag::

        {% title "foo" %}

    '''
    request = context['request']
    page = request.pages.current
    homepage = request.pages.homepage
    # Render the title template.
    return {
        'title': browser_title or context.get('title') or (page and page.browser_title) or (page and page.title) or '',
        'site_title': (homepage and homepage.browser_title) or (homepage and homepage.title) or '',
    }
