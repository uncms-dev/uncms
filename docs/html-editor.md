# The HTML editor

UnCMS comes with a <abbr title="What You See Is What You Get">WYSIWYG</abbr> HTML editor that you can use on your models to provide rich-text editing in your admin using TinyMCE v4.
UnCMS does not use this internally (as it has no opinions about what your page content should look like),
but it's included with UnCMS because almost every website requires it.

Use `cms.models.HtmlField` to add HTML editing to your admin.
`HtmlField` is a subclass of `TextField` which overrides the widget with a TinyMCE text editor.
Other than the widget, it works just like a `TextField`:

```python
from cms.models import HtmlField
# ... other imports here ....


class Article(models.Model)
    content = HtmlField()
```

That's it!

When rendering the HTML on the front-end of your site, you probably want to filter your HTML through the `html` template filter.
This will expand permalinks and set alt text, attribution etc on the images in your WYSIWYG editor (if they were inserted through the media library plugin mentioned above).

```
{{ object.content|html }}
```

There may be circumstances in which you want to use the HTML editing widget, but not use `HtmlField` on your model.
In this unusual case, use `cms.fields.HtmlWidget` in your form class.

If you wish to add extra capabilities or options to your editor, you will want to look at the `WYSIWYG_OPTIONS` [configuration option](configuration.md).
