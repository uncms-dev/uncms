# Rendering images

## Before you continue

You will want to add `THUMBNAIL_PRESERVE_FORMAT = True` to your Django settings.
By default, if you do not specify an output format, the Sorl thumbnail backend will generate a JPEG file,
regardless of your source format.

## Using `{% image %}`

To render images in your template, use the `{% image %}` template tag from the `uncms_images` library.
The simplest example is this:

```
{% load uncms_images %}
{% image some_file_object width=600 %}
```
It will render an image from your [media library](media-library.md) in multiple sizes for different devices using `srcset`,
and also in WebP format for browsers that support it.

You must specify an UnCMS File object as an argument, and at least one of these keyword arguments:

* `width`, an integer:
the width to thumbnail the image to.
* `height`, an integer:
the height to thumbnail the image to.
If you specify both `width` and `height`, the image will be cropped to the proper aspect ratio.

There are several additional options that you may want to use:

* `alt_text`, a string:
[textual description of the image](https://www.deque.com/blog/great-alt-text-introduction/) to display to screen readers.
This will default to the `alt_text` field of the `File`, or the empty string if that is not present.
If an explicit empty string (`''`) has been specified, it will be the empty string, and will not fall back to the `alt_text` for the image.
To improve the experience for screen readers, you should use an explicit empty string for images that are purely decorative.
* `webp`, boolean:
whether to output WebP versions of the image.
This is a Web-optimised format supported by almost all browsers and gives substantial size reductions over PNG and JPEG.
Defaults to `True`.
* `lazy`, boolean:
whether to use `loading="lazy"` on the rendered image.
You almost always want to use this option,
because it stops browsers loading off-screen images,
which is good for everyone's data plan.
Defaults to `True`.
* `aspect`, boolean:
whether to output an inline `style` with the appropriate `aspect-ratio` for this image.
You may want to specify `False` for this value if you have, e.g., an absolutely-positioned image designed to spread across the entire region of an element which will have a non-predictable aspect ratio
(such as a background image on an element).
You will also need to specify `False` if you are using a strict [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP) which forbids inline styles.
* `quality`, integer:
quality of the resized image.
This defaults to `None`, which will use Sorl's default settings for the image type
(which itself can be overridden by the `THUMBNAIL_QUALITY` Django setting).
* `colorspace`, string:
the colourspace to use for this image.
If you are displaying images in monochrome on your site,
you can obtain substantial image size reductions by specifying `GRAY` for this option,
rather than (e.g.) greyscaling them with CSS.
This defaults to `auto`, which will use the original colourspace for the image.
* `sizes`: the `sizes` attribute for the `<source>` tags. Defaults to `100vw`.

## How it works

First, depending on the width and/or height you have requested,
an initial thumbnail size is calculated, along with a generated signed URL containing thumbnailing parameters.
When visited, this URL thumbnails the image, and 302-redirects the user agent to the thumbnail's static file.

Secondly, for every value in the `UNCMS['IMAGE_WIDTHS']` values,
a URL is generated for each of the formats that will be output into a `<source>`,
using the same out-of-initial-request thumbnailing as above.

The trick here is that resizing images - which is usually a very expensive operation - is performed outside the initial request/response cycle.
Rendering images has _very little_ impact on time-to-first-byte performance of your page;
the cost of rendering the image tag is that of a few `reverse` calls and a template render.
This approach was directly inspired by the now-unmaintained [django-lazy-image](https://github.com/dan-gamble/django-lazy-image) package.

## Customising image rendering

Other than the many options for `{% image %}`,
you can customise image rendering either with CSS
(targeting sensible [BEM class names](https://getbem.com/naming/)),
or by overriding the default image rendering template.

### Customising with CSS

You may target the following selectors in CSS:

* `.image`: the opening `<picture>` tag
* `.image__image`: the `<img>` tag inside the above

For example, you may want to add a light grey background colour to all images,
as a placeholder indication for people on slow Internet connections who had not loaded it yet.
The following CSS will work fine:

```
.image {
  background-color: #eee;
}
```

If you are integrating UnCMS into an already-existing project,
it may be that the class name `image` is already taken.
Alternatively, you may just want to use a different class prefix for your own, because you are special.
If you do, you may override the `IMAGE_CLASS_PREFIX` option in the settings.

For example, the following will result in the selectors mentioned above being `.picture` and `.picture__image`.

```
UNCMS = {
    # your other options here...
    'IMAGE_CLASS_PREFIX': 'picture',
}
```

### Customising the template

The default template used to render images can be specified in the `IMAGE_TEMPLATE` [configuration option](configuration.md).
Instead of copying this template into your project and changing the bits you need to change,
you may want to change this configuration option,
and add a template of your own to your project which extends `media/multi_format_image.html`.
This template provides a huge number of blocks which you can override to add custom elements,
or classes and attributes to the ones which already exist.

* `before_picture_tag`: empty extension block before the opening `<picture>` tag
* `picture_tag_classes`: classes for the `<picture>` tag
* `extra_picture_tag_classes`: empty extension block for _extra_ picture tag classes
* `inside_picture_tag_top` empty extension block immediately after the opening `<picture>` tag
* `img_tag_classes`: all HTML classes for the `<img>` tag (defaults to `"image"`)
* `extra_img_tag_classes` empty extension block for adding _extra_ classes to the `<img>` tag
* `extra_img_tag_attributes`: empty extension block for adding extra attributes to the `<img>` tag
* `img_tag_lazy_attribute`: if lazy loading has been requested, the attribute `loading="lazy"` on the `<img>` tag, otherwise empty
* `img_tag_style_attribute`: the `style` attribute for the `img` tag, including the attribute name
* `inside_picture_tag_bottom`: empty extension block before the closing `<picture>` tag
* `after_picture_tag`: empty extension block after the closing `<picture>` tag

For example, you might not like (for whatever reason) the fact that images always request that browsers load them lazily by default,
and do not want to specify `lazy=False` every time you use `{% image %}`.
In this case, you would want an `UNCMS` configuration dictionary that looked like this:

```
UNCMS = {
    # your other options here...
    'IMAGE_TEMPLATE': 'media/never_lazy.html',
}
```

And in your `media/never_lazy.html`, you could have this:

```
{% extends 'media/multi_format_image.html' %}
{% block img_tag_lazy_attribute %}{% endblock %}
```

This will remove `loading="lazy"` regardless of the value specified for the `lazy` argument.
