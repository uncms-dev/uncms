from django import template

register = template.Library()


@register.simple_tag
def image(img, **kwargs):
    return img.render_multi_format(**kwargs)
