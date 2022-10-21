from django_jinja import library
from sorl.thumbnail import get_thumbnail


@library.global_function
def thumbnail(path, geometry, **options):
    """
    Jinja2 wrapper for sorl's thumbnail tag.
    """
    return get_thumbnail(path, geometry, **options)


@library.global_function
def render_image(image, **kwargs):
    return image.render_multi_format(**kwargs)
