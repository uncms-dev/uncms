'''Template tags used for processing HTML.'''

from django import template
from django.template.defaultfilters import stringfilter

from uncms.templatetags._common import html

register = template.Library()


register.filter(stringfilter(html))
