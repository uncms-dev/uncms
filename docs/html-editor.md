# The HTML editor

UnCMS comes with a <abbr title="What You See Is What You Get">WYSIWYG</abbr> HTML editor that you can use on your models to provide rich-text editing in your admin using TinyMCE v4.
UnCMS does not use this internally (as it has no opinions about what your page content should look like),
but it's included with UnCMS because almost every website requires it.

Use `uncms.models.HtmlField` to add HTML editing to your admin.
`HtmlField` is a subclass of `TextField` which overrides the widget with a TinyMCE text editor.
Other than the widget, it works just like a `TextField`:

```python
from uncms.models import HtmlField
# ... other imports here ....


class Article(models.Model)
    content = HtmlField()
```

That's it!

When rendering the HTML on the front-end of your site, you will want to filter your HTML through the `html` template filter.
This will expand image references and add alt text where it is missing to the images in your HTML editor.
Extra output processors may be specified with the [`HTML_OUTPUT_FORMATTERS`](configuration.md?id=html_output_formatters) configuration option.

It will also clean the HTML by filtering it through [Bleach](https://github.com/mozilla/bleach), which will remove any nasties such as `<script>`.
You may wish to override which tags and attributes are allowed with the [`BLEACH_OPTIONS`](configuration.md?id=bleach_options) configuration option.
Alternatively, you may use the [`HTML_CLEANERS`](configuration.md?id=html_cleaners) option to add extra HTML sanitisers,
or to remove HTML sanitisation altogether.

```
{{ object.content|html }}
```

There may be circumstances in which you want to use the HTML editing widget, but not use `HtmlField` on your model.
In this unusual case, use `uncms.fields.HtmlWidget` in your form class.

If you wish to add extra capabilities or options to your editor, you will want to look at the `WYSIWYG_OPTIONS` [configuration option](configuration.md).
