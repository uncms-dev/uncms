import json

from django import forms
from django.contrib.staticfiles.storage import staticfiles_storage

from cms.conf import defaults
from cms.html import clean_all


class HtmlWidget(forms.Textarea):
    '''A textarea that is converted into a TinyMCE rich text editor.'''

    def get_media(self):
        js = [
            staticfiles_storage.url('cms/js/tinymce/tinymce.min.js'),
            staticfiles_storage.url('cms/js/wysiwyg.js'),
        ]

        css = {
            'screen': [staticfiles_storage.url('cms/css/tinymce-tweak.css')],
        }

        return forms.Media(js=js, css=css)

    media = property(
        get_media,
        doc='The media used by the widget.',
    )

    def render(self, name, value, attrs=None, renderer=None):
        # Add on the JS initializer.
        attrs = attrs or {}
        attrs['class'] = 'wysiwyg'
        attrs['required'] = False
        attrs['data-wysiwyg-settings'] = json.dumps(defaults.WYSIWYG_OPTIONS)
        value = clean_all(value or '')

        # Get the standard widget.
        return super().render(name, value, attrs)
