from django.conf import settings
from django.utils.translation import gettext_lazy as _


class AppSettings:
    """
    AppSettings implements a way to get default settings for the application.
    Settings are accessible via attributes on an AppSettings instance.

    It will attempt to read any requested option from the `UNCMS`
    configuration dictionary, if that dictionary is present.

    If that option is not in the `UNCMS` dictionary, or `UNCMS` is not
    present, a sensible default will be returned.
    """
    default_settings = {
        'ADMIN_PAGE_LIST_ARROWS': True,
        # Options for HTML output filtering.
        'BLEACH_OPTIONS': {
            'tags': {
                'p', 'div', 'a', 'hr', 'span', 'blockquote',
                # Lists
                'ol', 'ul', 'li', 'dl', 'dt', 'dd',
                # Headings
                'h2', 'h3', 'h4', 'h5', 'h6',
                # Media
                'img', 'audio', 'picture', 'figure', 'figcaption', 'source', 'video',
                # Simple emphasis
                'i', 'em', 'strong', 'b', 'u',
                # obvs
                'br',
                # Code formats
                'code', 'pre',
                # super/subscripts
                'sup', 'sub',
                # a thing I needed once
                'abbr',
                # strikethrough and such
                'del', 'ins', 's',
                # external media
                'iframe',
                # Tables
                'table', 'thead', 'tbody', 'th', 'tr', 'td', 'tfoot', 'caption', 'colgroup', 'col',
            },
            'attributes': {
                '*': {
                    # blanket stuff that should almost always be OK - can
                    # style ever be dangerous?
                    'style', 'class', 'title',
                },
                'a': ['href'],
                'audio': ['src', 'controls', 'loop', 'muted'],
                'col': ['span'],
                'iframe': ['src', 'allowfullscreen', 'frameborder'],
                'img': ['src', 'loading', 'height', 'width', 'alt'],
                'ol': ['type'],
                'table': ['summary'],
                'td': ['rowspan', 'colspan'],
                'ul': ['type'],
                'video': ['controls', 'height', 'width'],
            },
        },
        'BREADCRUMBS_CLASS_PREFIX': 'breadcrumbs',
        'BREADCRUMBS_SHOW_TAIL': False,
        'BREADCRUMBS_TEMPLATE': 'pages/breadcrumbs.{extension}',
        'HTML_CLEANERS': ['uncms.html.clean_html'],
        'HTML_OUTPUT_FORMATTERS': ['uncms.html.format_html'],
        'HTML_IMAGE_WIDTH': 1280,
        'IMAGE_CLASS_PREFIX': 'image',
        'IMAGE_TEMPLATE': 'media/multi_format_image.html',
        'IMAGE_USE_WEBP': True,
        'MEDIA_FILE_MODEL': 'media.File',
        'MEDIA_LIST_GRID_VIEW': True,
        'MEDIA_UPLOAD_ALLOWED_EXTENSIONS': [],
        'MEDIA_UPLOAD_ALWAYS_ALLOW_IMAGES': True,
        'MEDIA_UPLOAD_PERMISSIONS_BYPASS': True,
        'MEDIA_URLS_NAMESPACE': 'media_library',
        'NAVIGATION_CLASS_PREFIX': 'navigation',
        'NAVIGATION_TEMPLATE': 'pages/navigation/navigation.html',
        'NAVIGATION_ITEM_TEMPLATE': 'pages/navigation/navigation_item.html',
        'NAVIGATION_SUBMENU_TEMPLATE': 'pages/navigation/navigation_submenu.html',
        'NAVIGATION_SUBMENU_ITEM_TEMPLATE': 'pages/navigation/navigation_submenu_item.html',
        'ONLINE_DEFAULT': True,
        'OPENGRAPH_FALLBACK_IMAGE': None,
        'PAGE_MODEL': 'pages.Page',
        'PAGE_TREE_PREFETCH_DEPTH': 2,
        'PATH_SIGNING_SECRET': settings.SECRET_KEY,
        'PUBLICATION_MIDDLEWARE_EXCLUDE_URLS': [r'^/admin/'],
        'REDIRECTS_CSV_IMPORT_ENABLED': True,
        'REGEX_REDIRECTS': False,
        'SITE_DOMAIN': None,
        'WYSIWYG_EXTRA_OPTIONS': {},
        'WYSIWYG_EXTRA_SCRIPTS': [],
        'WYSIWYG_EXTRA_STYLESHEETS': [],
        'WYSIWYG_OPTIONS': {
            'autogrow': False,
            'btns': [
                ['viewHTML'],
                ['structure'],
                ['strong', 'em', 'del', 'superscript', 'subscript'],
                ['imagelibrary', 'upload'],
                ['link'],
                ['unorderedList', 'orderedList'],
                ['table'],
                ['horizontalRule'],
                ['removeformat'],
                ['fullscreen'],
            ],
            'btnsDef': {
                # Trumbowyg's default "formatting" dropdown has the above plus
                # "h1". But we almost always don't want to allow h1, as that
                # is almost always provided by some element on the page. This
                # editor is not designed for editing the _entire_ page, only
                # some part of it, e.g. the body of an article.
                'structure': {
                    'title': _('Structure'),
                    'dropdown': ['p', 'blockquote', 'h2', 'h3', 'h4'],
                    'ico': 'p',
                },
            },
            'minimalLinks': True,
            'removeFormatPasted': True,
            'resetCss': True,
        },
    }

    def __getattr__(self, attname):
        conf_dict = getattr(settings, 'UNCMS', {})
        return conf_dict.get(attname, self.default_settings[attname])

    def get_wysiwyg_options(self):
        return {**self.WYSIWYG_OPTIONS, **self.WYSIWYG_EXTRA_OPTIONS}


defaults = AppSettings()
