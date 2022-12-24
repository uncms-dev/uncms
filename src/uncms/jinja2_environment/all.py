from django.template import defaultfilters
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment

from uncms.jinja2_environment.base import BASE_FILTERS
from uncms.jinja2_environment.pages import PAGES_GLOBALS


def environment(**options):
    env = Environment(**options)
    env.globals.update(PAGES_GLOBALS)
    env.filters.update(BASE_FILTERS)
    return env


def sensible_defaults(**options):
    env = environment(**options)
    env.globals.update({
        'static': static,
        'url': lambda viewname, *args, **kwargs: reverse(viewname, args=args, kwargs=kwargs),
    })

    for django_filter in [
        'date',
        'filesizeformat',
        'floatformat',
        'linebreaks',
        'linebreaksbr',
        'time',
        'urlize',
    ]:
        env.filters[django_filter] = getattr(defaultfilters, django_filter)
    return env
