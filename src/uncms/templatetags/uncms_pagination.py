'''Template tags for rendering pagination.'''
import jinja2
from django import template
from django.core.paginator import InvalidPage, Paginator
from django.http import Http404
from django.utils.html import escape

from uncms.templatetags._common import get_pagination_context

register = template.Library()


@jinja2.pass_context
def paginate(context, queryset, per_page=10, key='page'):
    '''Returns a paginator object for the given queryset.'''
    request = context['request']

    # Parse the page number.
    try:
        page_number = int(request.GET[key])
    except (KeyError, TypeError, ValueError):
        page_number = 1
    # Create the paginator.
    try:
        page = Paginator(queryset, per_page).page(page_number)
    except InvalidPage as exc:
        raise Http404('There are no items on page {}.'.format(page_number)) from exc
    page._pagination_key = key

    return page


@register.inclusion_tag('pagination/pagination.html', takes_context=True)
def pagination(context, page_obj, pagination_key=None):
    '''Renders pagination for the given paginator object.'''
    return get_pagination_context(context['request'], page_obj, pagination_key=pagination_key)


@register.simple_tag(takes_context=True)
def pagination_url(context, page_number):
    '''Returns a URL for the given page number.'''
    request = context['request']
    url = request.path
    params = request.GET.copy()
    if str(page_number) != '1':
        params[context.get('pagination_key', 'page')] = page_number
    else:
        params.pop(context.get('pagination_key', 'page'), None)
    if params:
        url += '?{}'.format(params.urlencode())
    return escape(url)
