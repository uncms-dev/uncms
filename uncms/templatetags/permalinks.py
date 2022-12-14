'''Permalink generation template tags.'''
import jinja2
from django.utils.html import escape

from uncms import permalinks


def permalink(obj):
    '''Returns a permalink for the given object.'''
    return permalinks.create(obj)


@jinja2.pass_context
def get_permalink_absolute(context, model):
    request = context['request']

    return escape(request.build_absolute_uri(permalinks.create(model)))
