from sorl.thumbnail import get_thumbnail


def thumbnail(path, geometry, **options):
    """
    Jinja2 wrapper for sorl's thumbnail tag.
    """
    return get_thumbnail(path, geometry, **options)


def render_image(image, **kwargs):
    return image.render_multi_format(**kwargs)
