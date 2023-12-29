import jinja2
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

import uncms.pages.templatetags._common as pages_common
from uncms.conf import defaults


@jinja2.pass_context
def get_breadcrumbs(context, *, breadcrumb_list=None, auto_extend=True, extend_with=None):
    return pages_common.get_breadcrumbs_obj(
        context,
        breadcrumb_list=breadcrumb_list,
        auto_extend=auto_extend,
        extend_with=extend_with,
    )


@jinja2.pass_context
def render_breadcrumbs(context, breadcrumbs_obj=None, *, auto_extend=True, show_tail=None, class_prefix='breadcrumbs'):
    return mark_safe(render_to_string(
        defaults.BREADCRUMBS_TEMPLATE.format(extension='jinja2'),
        pages_common.get_breadcrumbs_context(
            context,
            breadcrumbs_obj=breadcrumbs_obj,
            auto_extend=auto_extend,
            show_tail=show_tail,
            class_prefix=class_prefix,
        ),
    ))


@jinja2.pass_context
def render_title(context):
    return render_to_string('pages/title.html', pages_common.render_title(context))


PAGES_GLOBALS = {
    key: jinja2.pass_context(getattr(pages_common, key))
    for key in [
        'get_canonical_url',
        'get_meta_description',
        'get_meta_robots',
        'get_og_title',
        'get_og_image',
        'get_og_description',
        'render_navigation',
    ]
}

PAGES_GLOBALS['get_breadcrumbs'] = get_breadcrumbs
PAGES_GLOBALS['render_breadcrumbs'] = render_breadcrumbs
PAGES_GLOBALS['render_title'] = render_title
PAGES_GLOBALS['get_page_url'] = pages_common.get_page_url
