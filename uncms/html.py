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

    soup = BeautifulSoup(text, 'html.parser')

    for image in soup.find_all('img'):
        if not image.get('src'):
            continue

        image_id = None

        if image['src'].startswith(old_prefix):
            image_id = image['src'][len(old_prefix):].rstrip('/')
        else:
            # Coverage is smoking something and cannot see that this line is
            # in fact covered - stick "assert 0" in here to see the test fail
            # :)
            continue  # pragma: no cover

        try:
            obj = media_model.objects.get(pk=image_id)
        except (media_model.DoesNotExist, ValueError):
            continue
        image['src'] = obj.get_absolute_url()
        if not image.get('alt'):
            image['alt'] = obj.alt_text or ''

    return str(soup)


def format_all(html):
    for formatter in defaults.HTML_OUTPUT_FORMATTERS:
        formatter_func = import_string(formatter)
        html = formatter_func(html)

    return html


def process_html(html):
    return format_all(clean_all(html))
