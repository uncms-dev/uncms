# Configuring UnCMS

Configuration of UnCMS in your Django settings is done with a single dictionary `UNCMS`.
The following settings should all be expressed as keys in the dictionary.
None of these keys are required,
and if you omit any of the keys from your configuration the defaults will be used.

For example this configuration dictionary will only override the `ONLINE_DEFAULT` setting,
and use the default settings for everything else:

```
UNCMS = {
    'ONLINE_DEFAULT': False,
}
```

## `BLEACH_OPTIONS`

* Type: dictionary (Bleach `clean` keyword arguments)
* Default: too large to put here; see `cms/conf.py`

HTML from the default [HTML editor](html-editor.md) should be sanitised for bad tags (such as `<script>`) and bad attributes (such as `onload`) before being displayed to users of your site.
By default, this is passed through [Bleach](https://github.com/mozilla/bleach).
UnCMS has a long list of built-in default allowed tags and attributes that should be safe.
You may want to allow or disallow other tags and attributes.
If you do, use this configuration setting.

This option corresponds directly to keyword arguments accepted by the [`bleach.clean`](https://bleach.readthedocs.io/en/latest/clean.html) function.

## `HTML_CLEANERS`

* Type: list of strings (dotted names of cleaner functions)
* Default: `['cms.html.clean_html']`

This is a list of functions that will clean the output in the `html` template filter.
The default is to run it through a function that cleans it with Bleach's `clean` function.
See `BLEACH_OPTIONS` above.

This should be a list of functions, as dotted string paths, which accept a single argument and return the cleaned HTML as a string.
This list is _not_ additive to the defaults;
if you wish to retain the default HTML cleaning while adding your own cleaner functions,
you must include `'cms.html.clean_html'` in this list.

## `HTML_OUTPUT_FORMATTERS`

* Type: list of strings (dotted names of HTML output formatting functions)
* Default: `['cms.html.format_html']`

`HTML_OUTPUT_FORMATTERS` is a list of functions, as dotted string paths, which will clean the HTML when output on your site with the `html` template filter.
This is intended for_post-processing_, not for sanitisation;
for the latter, see the `HTML_CLEANERS` option.

By default, it will run `'cms.html.format_html'`, which expands permalinks and rewrites images.
This list is _not_ additive to the defaults;
if you wish to retain the default HTML processing while adding your own output formatters,
you must include `'cms.html.format_html'` in this list.

## `MEDIA_FILE_MODEL`

* Type: string (dotted name of Django model)
* Default: `'media.File'`

UnCMS's default `SearchMetaBase` (and consequently `Page`) model has fields for images, for OpenGraph and Twitter cards.
By default, it will be assumed that you have the UnCMS [media app](media-app.md) installed.
You may want to bring your own media app, or to copy the UnCMS one into your own project with changes and a different name.
If you do, you may override `MEDIA_FILE_MODEL` with this setting.

Your custom model must implement a `file` attribute, which is a Django `FileField`,
an `is_image()` method to determine if it is an image,
and `width` and `height` attributes returning the width and height of the file as integers (if it is an image).

Note that this may not play nicely with using `HtmlField`.

## `MEDIA_LIST_GRID_VIEW`

* Type: boolean
* Default: `True`

The list of files in the [media app](media-app.md) has some extra CSS to style the list as a grid,
rather than as a table.
This looks much better for something that is not informationally-dense,
but it may not play well with non-standard admin skins.
Set this to `False` if it looks weird in your admin, or if you prefer a standard table list view.

## `ONLINE_DEFAULT`

* Type: boolean
* Default: `True`

This controls whether a new `Page` (and anything else that inherits from OnlineBase) will have `is_online` set to True by default when creating new objects in the admin.
Set it to `False` to make new pages be offline by default.

## `PATH_SIGNING_SECRET`

* Type: string
* Default: value of `settings.SECRET_KEY`

UnCMS uses signed URLs to, e.g., generate preview links for offline pages,
so that unauthenticated users can view them if they are given a special URL.
Usually, this is generated and validated using a hash of the path and `settings.SECRET_KEY`.
However, it is not uncommon to rotate `settings.SECRET_KEY` to protect data that is truly secret.
This might not be necessary with signed paths.

If you are using `SECRET_KEY` rotation, then you may want to override `PATH_SIGNING_SECRET` with a fixed value.

## `PUBLICATION_MIDDLEWARE_EXCLUDE_URLS`

* Type: list of regular expressions
* Default: `['^/admin/']`

THe publication middleware will automagically exclude any objects from any querysets whose model is a subclass of `OnlineBase` and whose `is_online` field is set to `False`.
Of course, you probably don't want to do that for _every_ request.
The most obvious is that you will want to be able to view offline pages in your site's administrative area.
You may want to change this setting if your admin lives at any location other than "/admin/".

## `WYSIWYG_OPTIONS`

* Type: dictionary
* Default: too large to put here; see `cms/conf.py`

These are options for the optional [HTML editor](html-editor.md).
These map directly onto TinyMCE options.
A full set of options is available in the [TinyMCE documentation](https://www.tiny.cloud/docs-4x/configure/integration-and-setup/).
