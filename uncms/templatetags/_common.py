'''Template tags used for processing HTML.'''

from django.utils.safestring import mark_safe

from uncms.html import process_html


def html(text):
    '''
    Processes HTML text.

    The text is checked for permalinks embedded in <a> tags, expanding the
    permalinks to their referenced URL. Images containing a permalink source
    are checked for size and thumbnailed as appropriate.
    '''
    if not text:
        return ''
    text = process_html(text)
    return mark_safe(text)


def get_pagination_context(request, page_obj, pagination_key=None):
    """
    Gets page context necessary to render the given paginator object.
    """
    return {
        'page_obj': page_obj,
        'page_range': page_obj.paginator.page_range[:10],
        'paginator': page_obj.paginator,
        'pagination_key': pagination_key or getattr(page_obj, '_pagination_key', 'page'),
        # necessary for pagination_url to work
        'request': request,
    }
