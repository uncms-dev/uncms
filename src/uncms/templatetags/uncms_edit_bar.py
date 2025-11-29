from django import template
from django.template.loader import render_to_string

from uncms.templatetags._common import get_edit_bar_context

register = template.Library()


@register.simple_tag(takes_context=True)
def edit_bar(context):
    new_context = get_edit_bar_context(context)
    if new_context is None:
        return ""
    return render_to_string("edit-bar/edit_bar.html", new_context)
