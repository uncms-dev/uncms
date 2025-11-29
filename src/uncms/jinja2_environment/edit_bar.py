import jinja2
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from uncms.templatetags._common import get_edit_bar_context


@jinja2.pass_context
def render_edit_bar(context):
    new_context = get_edit_bar_context(context)
    if new_context is None:
        return ""
    return mark_safe(render_to_string("edit-bar/edit_bar.jinja2", new_context))


EDIT_BAR_GLOBALS = {
    "render_edit_bar": render_edit_bar,
}
