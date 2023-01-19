import json

from django import forms
from django.urls import reverse

from uncms.conf import defaults
from uncms.html import clean_all


class HtmlWidget(forms.Textarea):
    """
    A textarea which is converted into a Trumbowyg rich text editor.
    """
    class Media:
        """
        Media for HtmlWidget.

        You may be thinking "this is an uncomfortably large number of files".
        As it happens, instinctively, I would agree. Yet, in the HTTP/2 world
        (and hopefully, all instances will be deployed that way) this is not
        an issue.
        """

        js = [
            # must be first - both trumbowyg and its upload plugin depend on
            # window.jquery being present
            'admin/js/vendor/jquery/jquery.js',
            'uncms/vendor/trumbowyg/trumbowyg.js',
            'uncms/js/trumbowyg-imagelibrary/trumbowyg.imagelibrary.js',
            'uncms/vendor/trumbowyg/plugins/upload/trumbowyg.upload.js',
            'uncms/vendor/trumbowyg/plugins/table/trumbowyg.table.js',
            'uncms/js/wysiwyg.js',
        ] +  defaults.WYSIWYG_EXTRA_SCRIPTS + [
            # Must be last, as this `noconflict`s jQuery and Trumbowyg thinks
            # it is always available as `window.jQuery`.
            'admin/js/jquery.init.js',
        ]

        css = {
            'screen': [
                'uncms/vendor/trumbowyg/ui/trumbowyg.css',
                'uncms/vendor/trumbowyg/plugins/table/ui/trumbowyg.table.css',
                'uncms/js/trumbowyg-imagelibrary/ui/trumbowyg.imagelibrary.css',
                'uncms/css/trumbowyg-tweak.css',
            ] + defaults.WYSIWYG_EXTRA_STYLESHEETS,
        }

    def render(self, name, value, attrs=None, renderer=None):
        # Add on the JS initializer.
        attrs = attrs or {}
        attrs['class'] = 'wysiwyg'
        attrs['required'] = False
        attrs['rows'] = 30
        attrs['data-wysiwyg-upload-url'] = reverse('admin:media_file_image_upload_api')
        attrs['data-wysiwyg-image-list-url'] = reverse('admin:media_file_image_list_api')
        attrs['data-wysiwyg-settings'] = json.dumps(defaults.get_wysiwyg_options())
        value = clean_all(value or '')

        # Get the standard widget.
        return super().render(name, value, attrs)
