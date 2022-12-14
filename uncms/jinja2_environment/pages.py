import jinja2
from django.template.loader import render_to_string

import uncms.pages.templatetags._common as pages_common


@jinja2.pass_context
def render_title(context):
    return render_to_string('pages/title.html', pages_common.render_title(context))


PAGES_GLOBALS = {
    key: getattr(pages_common, key)
    for key in [
        'get_canonical_url',
        'get_page_url',
        'get_meta_description',
        'get_meta_robots',
        'get_og_title',
        'get_og_image',
        'get_og_description',
        'get_twitter_card',
        'get_twitter_image',
        'get_twitter_description',
        'get_twitter_title',
        'render_navigation',
    ]
}

PAGES_GLOBALS['render_title'] = render_title
