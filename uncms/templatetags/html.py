'''Template tags used for processing HTML.'''

from django.template.defaultfilters import stringfilter

from uncms.templatetags._common import html

stringfilter(html)
