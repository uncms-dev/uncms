def render_image(img, **kwargs):
    return img.render_multi_format(**kwargs)


MEDIA_GLOBALS = {
    'render_image': render_image,
}
