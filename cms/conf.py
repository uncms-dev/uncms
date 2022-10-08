from django.conf import settings


class AppSettings:
    """
    AppSettings implements a way to get default settings for the application.
    Settings are accessible via attributes on an AppSettings instance.
    It will attempt to read the options from the UNCMS configuration
    dictionary if it is present, and if it is neither in UNCMS or UNCMS is not
    present, will return some sensible default.
    """
    default_settings = {
        'MEDIA_FILE_MODEL': 'media.File',
        'ONLINE_DEFAULT': True,
        'PATH_SIGNING_SECRET': settings.SECRET_KEY,
        'PUBLICATION_MIDDLEWARE_EXCLUDE_URLS': [r'^/admin/'],
        'WYSIWYG_OPTIONS': {
            'height': 500,
            'plugins': [
                'advlist autolink link image lists charmap hr anchor pagebreak',
                'wordcount visualblocks visualchars code fullscreen cmsimage hr',
            ],
            'toolbar1': 'code | cut copy pastetext | undo redo | bullist numlist | link unlink anchor cmsimage | blockquote',
            'menubar': False,
            'toolbar_items_size': 'small',
            'block_formats': 'Paragraph=p;Header 2=h2;Header 3=h3;Header 4=h4;Header 5=h5;Header 6=h6;',
            'convert_urls': False,
            'paste_as_text': True,
            'image_advtab': True,
        },
    }

    def __getattr__(self, attname):
        conf_dict = getattr(settings, 'UNCMS', {})
        return conf_dict.get(attname, self.default_settings[attname])


defaults = AppSettings()
