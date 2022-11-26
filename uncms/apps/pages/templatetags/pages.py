'''Template tags used to render pages.'''
import jinja2
from django import template
from django.urls import reverse
from django.utils.html import escape
from django_jinja import library

from uncms.apps.pages.models import Page
from uncms.conf import defaults
from uncms.models import SearchMetaBase
from uncms.utils import canonicalise_url

register = template.Library()


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
        section_entry['here'] = context['pages'].current == section_entry['page']
        entries = [section_entry] + list(entries)

    return entries


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
        'pages': [sitemap_entry(Page.objects.get_homepage())]
    }


@library.global_function
@library.render_with(defaults.NAVIGATION_TEMPLATE)
@jinja2.pass_context
def render_navigation(context, pages, section=None, class_prefix=None, **templates):
    '''
    Renders a navigation list for the given pages.

    The pages should all be a subclass of PageBase, and possess a get_absolute_url() method.

    You can also specify an alias for the navigation, at which point it will be set in the
    context rather than rendered.
    '''
    return {
        'navigation': _navigation_entries(context, pages, section),
        'prefix': class_prefix or defaults.NAVIGATION_CLASS_PREFIX,
        'item_template': templates.get('item_template', defaults.NAVIGATION_ITEM_TEMPLATE),
        'submenu_template': templates.get('submenu_template', defaults.NAVIGATION_SUBMENU_TEMPLATE),
        'submenu_item_template': templates.get('submenu_item_template', defaults.NAVIGATION_SUBMENU_ITEM_TEMPLATE),
    }


# Page linking.
@library.global_function
def get_page_url(page, view_func=None, *args, **kwargs):  # pylint:disable=keyword-arg-before-vararg
    '''Renders the URL of the given view func in the given page.'''
    url = None
    if isinstance(page, int):
        try:
            page = Page.objects.get(pk=page)
        except Page.DoesNotExist:
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
@library.global_function
@jinja2.pass_context
def get_meta_description(context, description=None):
    '''
    Renders the content of the meta description tag for the current page::

        {{ get_meta_description() }}

    You can override the meta description by setting a context variable called
    'meta_description'::

        {% with meta_description = 'foo' %}
            {{ get_meta_description() }}
        {% endwith %}

    You can also provide the meta description as an argument to this tag::

        {{ get_meta_description('foo') %}

    '''
    if description is None:
        description = context.get('meta_description')

    if description is None:
        request = context['request']
        page = request.pages.current

        if page:
            description = page.meta_description

    return escape(description or '')


@library.global_function
@jinja2.pass_context
def get_meta_robots(context, index=None, follow=None, archive=None):
    '''
    Renders the content of the meta robots tag for the current page::

        {{ get_meta_robots() }}

    You can override the meta robots by setting boolean context variables called
    'robots_index', 'robots_archive' and 'robots_follow'::

        {% with robots_follow = 1 %}
            {% get_meta_robots() %}
        {% endwith %}

    You can also provide the meta robots as three boolean arguments to this
    tag in the order 'index', 'follow' and 'archive'::

        {% get_meta_robots(1, 1, 1) %}
    '''
    # Override with context variables.
    if index is None:
        index = context.get('robots_index')
    if follow is None:
        follow = context.get('robots_follow')
    if archive is None:
        archive = context.get('robots_archive')

    # Try to get the values from the current page.
    page = context['pages'].current

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
    return escape(robots)


@library.global_function
@jinja2.pass_context
def get_canonical_url(context):
    '''
    Returns the canonical URL of the current page, normalised for the correct
    protocol, path and PREPEND_WWW setting.
    '''
    url = canonicalise_url(context['request'].path)
    return escape(url)


@library.global_function
@jinja2.pass_context
def get_og_title(context, title=None):
    if not title:
        obj = context.get('object', None)

        if obj:
            title = getattr(obj, 'og_title', None) or getattr(obj, 'title', None)

    if not title:
        title = context.get('og_title')

    if not title or title == '':
        request = context['request']
        page = request.pages.current

        if page:
            title = page.og_title

        if not title:
            title = context.get('title') or (page and page.title) or (page and page.browser_title)

    return escape(title or '')


@library.global_function
@jinja2.pass_context
def get_og_description(context, description=None):
    if not description:
        description = context.get('og_description')

    if not description:
        request = context['request']
        page = request.pages.current

        if page:
            description = page.og_description

    return escape(description or '')


@library.global_function
@jinja2.pass_context
def get_og_image(context, image=None):
    image_obj = None

    if not image:
        image_obj = context.get('og_image')

    if not image and not image_obj:
        obj = context.get('object')

        if obj:
            field = getattr(obj, 'image', None) or getattr(obj, 'photo', None) or getattr(obj, 'logo', None)

            image_obj = field if field else None

    if not image_obj:
        request = context['request']
        page = request.pages.current

        if page:
            image_obj = page.og_image

    if image_obj:
        return canonicalise_url(image_obj.get_absolute_url())

    if image:
        return canonicalise_url(image.get_absolute_url())

    return None


@library.global_function
@jinja2.pass_context
def get_twitter_card(context, card=None):
    choices = dict(SearchMetaBase._meta.get_field('twitter_card').choices)

    # Load from context if exists
    if not card:
        card = context.get('twitter_card')

    # If we are still None, look at page content
    if not card:
        # Get current page from request
        request = context['request']
        current_page = request.pages.current
        homepage = request.pages.homepage

        # Use either the current page twitter card, or the homepage twitter card
        if current_page:
            card = current_page.twitter_card

        if not card and homepage:
            card = homepage.twitter_card

    if card or card == 0:
        card = str(choices[card]).lower()

    return escape(card or str(choices[0]).lower())


@library.global_function
@jinja2.pass_context
def get_twitter_title(context, title=None):
    # Load from context if exists
    if not title:
        title = context.get('twitter_title')

    # Check the object if we still have nothing
    if not title:
        obj = context.get('object', None)

        if obj:
            title = getattr(obj, 'twitter_title', None) or getattr(obj, 'title', None)

    # If we are still None, look at page content
    if not title:
        # Get current page from request
        request = context['request']
        current_page = request.pages.current
        homepage = request.pages.homepage

        # Use either the current page twitter title, or the homepage twitter title
        if current_page:
            title = current_page.twitter_title

        if not title and homepage:
            title = homepage.twitter_title

        # If everything fails, fallback to OG tag title
        if not title:
            title = get_og_title(context)

    # Return title, or an empty string if nothing is working
    return escape(title or '')


@library.global_function
@jinja2.pass_context
def get_twitter_description(context, description=None):
    # Load from context if exists
    if not description:
        description = context.get('twitter_description')

    # If we are still None, look at page content
    if not description:
        # Get current page from request
        request = context['request']
        current_page = request.pages.current
        homepage = request.pages.homepage

        # Use either the current page twitter description, or the homepage twitter description
        if current_page:
            description = current_page.twitter_description

        if not description and homepage:
            description = homepage.twitter_description

        # If everything fails, fallback to OG tag title
        if not description:
            description = get_og_description(context)

    # Return description, or an empty string if nothing is working
    return escape(description or '')


@library.global_function
@jinja2.pass_context
def get_twitter_image(context, image=None):
    '''
    Returns an appropriate Twitter image for the current page, falling back
    to the Open Graph image if it is set.
    '''
    image_obj = None

    # Load from context if exists
    if not image:
        image = context.get('twitter_image')

    # Check the object if we still have nothing
    if not image:
        obj = context.get('object')

        if obj:
            field = getattr(obj, 'image', None) or getattr(obj, 'photo', None) or getattr(obj, 'logo', None)

            image_obj = field if field else None

    # Get current page from request
    request = context['request']

    # If we are still None, look at page content
    if not image and not image_obj:
        current_page = request.pages.current
        homepage = request.pages.homepage

        # Use either the current page twitter image, or the homepage twitter image
        if current_page:
            image = current_page.twitter_image

        if not image and homepage:
            image = homepage.twitter_image

        # If everything fails, fallback to OG tag title
        if not image:
            return get_og_image(context)

    # If its a file object, load the URL manually
    if image_obj:
        return canonicalise_url(image_obj.get_absolute_url())

    if image:
        return canonicalise_url(image.get_absolute_url())

    # Return image, or an empty string if nothing is working
    return None


@library.global_function
@library.render_with('pages/title.html')
@jinja2.pass_context
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


@library.global_function
@library.render_with('pages/breadcrumbs.html')
@jinja2.pass_context
def render_breadcrumbs(context, page=None, extended=False):
    '''
    Renders the breadcrumbs trail for the current page::

        {% breadcrumbs %}

    To override and extend the breadcrumb trail within page applications, add
    the 'extended' flag to the tag and add your own breadcrumbs underneath::

        {% breadcrumbs extended=1 %}

    '''
    request = context['request']
    # Render the tag.
    page = page or request.pages.current
    if page:
        breadcrumb_list = [{
            'short_title': breadcrumb.short_title or breadcrumb.title,
            'title': breadcrumb.title,
            'url': breadcrumb.get_absolute_url(),
            'last': False,
            'page': breadcrumb,
        } for breadcrumb in request.pages.breadcrumbs]
    else:
        breadcrumb_list = []
    if not extended:
        breadcrumb_list[-1]['last'] = True
    # Render the breadcrumbs.
    return {
        'breadcrumbs': breadcrumb_list,
    }
