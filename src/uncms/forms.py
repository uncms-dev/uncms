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
        js = [
            # must be first - both trumbowyg and its upload plugin depend on
            # window.jquery being present
            'admin/js/vendor/jquery/jquery.js',
            'uncms/vendor/trumbowyg/trumbowyg.js',
            'uncms/vendor/trumbowyg/plugins/upload/trumbowyg.upload.js',
            'uncms/vendor/trumbowyg/plugins/table/trumbowyg.table.js',
            'uncms/js/wysiwyg.js',
            # Must be last, as this `noconflict`s jQuery
            'admin/js/jquery.init.js',
        ]

        css = {
            'screen': [
                'uncms/vendor/trumbowyg/ui/trumbowyg.css',
                'uncms/vendor/trumbowyg/plugins/table/ui/trumbowyg.table.css',
                'uncms/css/trumbowyg-tweak.css',
            ],
        }

    def render(self, name, value, attrs=None, renderer=None):
        # Add on the JS initializer.
        attrs = attrs or {}
        attrs['class'] = 'wysiwyg'
        attrs['required'] = False
        attrs['data-wysiwyg-upload-url'] = reverse('admin:media_file_image_upload')
        attrs['data-wysiwyg-settings'] = json.dumps(defaults.get_wysiwyg_options())
        value = clean_all(value or '')

        # Get the standard widget.
        return super().render(name, value, attrs)
