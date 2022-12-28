"""HTML processing routines."""
import bleach
from bs4 import BeautifulSoup
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.utils.module_loading import import_string

from uncms.conf import defaults


def clean_html(html):
    return bleach.clean(html, **defaults.BLEACH_OPTIONS)


def clean_all(html):
    for cleaner in defaults.HTML_CLEANERS:
        cleaner_func = import_string(cleaner)
        html = cleaner_func(html)

    return html


def format_html(text):
    """
    Expands image references inserted by the HTML editor, and adds in their
    alt attributes.
    """

    # An old form of permalink used on existing installations was '/r/NN-YY/',
    # where NN was the content type ID of media.File. We can be compatible
    # with that.
    media_model = apps.get_model(defaults.MEDIA_FILE_MODEL)
    media_model_id = ContentType.objects.get_for_model(media_model).id
    old_prefix = f'/r/{media_model_id}-'

    # Prefix for UnCMS-era temporary URLs. Create an unsaved instance of
    # a media file so we can get its preview URL.
    new_prefix = media_model(id=0).get_temporary_url()
    new_prefix = new_prefix[:new_prefix.index('0')]

    soup = BeautifulSoup(text, 'html.parser')

    for image in soup.find_all('img'):
        if not image.get('src'):
            continue

        image_id = None

        for prefix in old_prefix, new_prefix:
            if image['src'].startswith(prefix):
                image_id = image['src'][len(prefix):].rstrip('/')
                break

        if not image_id:
            continue

        # Don't throw an exception if the given image does not exist.
        try:
            obj = media_model.objects.get(pk=image_id)
        except (media_model.DoesNotExist, ValueError):
            continue

        new_image = BeautifulSoup(obj.render_multi_format(
            width=defaults.HTML_IMAGE_WIDTH,
            # Copy over alt text if it is present. If it is an explicit empty
            # string, obey it - if it is not present it will be None, which
            # render_multi_format treats as "replace with alt text from the
            # File model".
            alt_text=image.get('alt_text'),
            extra_styles=image.get('style'),
            # Copy over "class" - note BS4 returns an array for element['class']
            extra_classes=' '.join(image.get('class', [])),
            # Copy over all attributes except "style" and "class" (those are
            # handled above)
            extra_attributes={
                key: value
                for key, value in image.attrs.items()
                if key not in ['class', 'style', 'src']
            },
        ), 'html.parser')
        image.replace_with(new_image)

    return str(soup)


def format_all(html):
    for formatter in defaults.HTML_OUTPUT_FORMATTERS:
        formatter_func = import_string(formatter)
        html = formatter_func(html)

    return html


def process_html(html):
    return format_all(clean_all(html))
