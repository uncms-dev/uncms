'''Template tags used for processing HTML.'''

from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django_jinja import library

from uncms.html import process_html


@library.filter
@stringfilter
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
