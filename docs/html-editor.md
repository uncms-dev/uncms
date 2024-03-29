# The HTML editor

UnCMS comes with a <abbr title="What You See Is What You Get">WYSIWYG</abbr> HTML editor that you can use on your models to provide rich-text editing in your admin, using [Trumbowyg](https://alex-d.github.io/Trumbowyg/).
UnCMS does not use this internally (because it has no opinions about what your page content should look like),
but it's included with UnCMS because almost every website requires it.

Use `uncms.models.HtmlField` to add HTML editing to your admin.
`HtmlField` is a subclass of `TextField` which overrides the widget with a Trumbowyg text editor.
The default text editor ships with a minimal set of useful plugins,
including one to upload files directly to your [media library](media-app.md) from within your editor,
and to choose from existing files in your library.

Other than the widget, it works just like a `TextField`:

```python
from uncms.models import HtmlField
# ... other imports here ....


class Article(models.Model)
    content = HtmlField()
```

That's it!

When rendering the HTML on the front-end of your site, you will want to filter your HTML through the `html` template filter.

```
{% load uncms_html %}
{{ object.content|html }}
```

This will expand image references and add alt text where it is missing to the images in your HTML editor.
It will also thumbnail images to the width specified in the [`HTML_IMAGE_WIDTH`](configuration.md?id=html_image_width) configuration option
(including generating optional WebP versions for browsers which support it).

Extra HTML output processors may be specified with [`HTML_OUTPUT_FORMATTERS`](configuration.md?id=html_output_formatters).

The `html` filter will also clean the HTML by filtering it through [nh3](https://github.com/messense/nh3), which will remove any nasties such as `<script>`.
You may wish to override which tags and attributes are allowed with the [`NH3_OPTIONS`](configuration.md?id=nh3_options) configuration option.
Alternatively, you may change the [`HTML_CLEANERS`](configuration.md?id=html_cleaners) option to add extra HTML sanitisers,
or to remove HTML sanitisation altogether.

There may be circumstances in which you want to use the HTML editing widget, but not use `HtmlField` on your model.
In this unusual case, use `uncms.fields.HtmlWidget` in your form class.

If you wish to add extra capabilities or options to your editor,
you will want to look at the `WYSIWYG_EXTRA_OPTIONS`, `WYSIWYG_EXTRA_SCRIPTS`, and `WYSIWYG_EXTRA_STYLESHEETS` [configuration options](configuration.md).
