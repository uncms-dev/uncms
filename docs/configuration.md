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

## `ADMIN_PAGE_LIST_ARROWS`

* Type: boolean
* Default: `True`

By default, the admin page list will show arrows next to the page title to indicate the depth and parent of the current page.
For example, if you have a home page "Home", with a child called "Cats", and that child has children called "Black", "Tabby" and "Calico",
their titles will be displayed as:

```
Home
→ Cats
→ → Black
→ → Tabby
→ → Calico
```

While some efforts are made to ensure this is efficient
(`PAGE_TREE_PREFETCH_DEPTH` below is obeyed to chain `select_related` on the parents to ensure it happens in a single query),
with extremely deep and wide page trees you may find that this becomes inefficient.
If so, set this to `False`.

## `BLEACH_OPTIONS`

* Type: dictionary (Bleach `clean` keyword arguments)
* Default: too large to put here; see `uncms/conf.py`

HTML from the default [HTML editor](html-editor.md) should be sanitised for bad tags (such as `<script>`) and bad attributes (such as `onload`) before being displayed to users of your site.
By default, this is passed through [Bleach](https://github.com/mozilla/bleach).
UnCMS has a long list of built-in default allowed tags and attributes that should be safe.
You may want to allow or disallow other tags and attributes.
If you do, use this configuration setting.

This option corresponds directly to keyword arguments accepted by the [`bleach.clean`](https://bleach.readthedocs.io/en/latest/clean.html) function.

## `HTML_CLEANERS`

* Type: list of strings (dotted names of cleaner functions)
* Default: `['uncms.html.clean_html']`

This is a list of functions that will clean the output in the `html` template filter.
The default is to run it through a function that cleans it with Bleach's `clean` function.
See `BLEACH_OPTIONS` above.

This should be a list of functions, as dotted string paths, which accept a single argument and return the cleaned HTML as a string.
This list is _not_ additive to the defaults;
if you wish to retain the default HTML cleaning while adding your own cleaner functions,
you must include `'uncms.html.clean_html'` in this list.

## `HTML_IMAGE_WIDTH`

* Type: integer
* Default: 1280

When formatting HTML from the [HTML editor](html-editor.md),
the UnCMS `html` template filter will replace images with thumbnailed versions.
This is to save you from resizing them to a sensible size yourself before inserting them
(which encourages the sensible practice of always having high-resolution master versions in the library).
Images will be thumbnailed to a width specified by the `HTML_IMAGE_WIDTH` option.
You may adjust this value if you know you will need to display them at larger widths than this,
or if you know you will only be displaying it at sizes smaller than this.

## `HTML_OUTPUT_FORMATTERS`

* Type: list of strings (dotted names of HTML output formatting functions)
* Default: `['uncms.html.format_html']`

`HTML_OUTPUT_FORMATTERS` is a list of functions, as dotted string paths, which will clean the HTML when output on your site with the `html` template filter.
This is intended for_post-processing_, not for sanitisation;
for the latter, see the `HTML_CLEANERS` option.

By default, it will run `'uncms.html.format_html'`, which rewrites image references as inserted by the default [HTML editor](html-editor.md).
This list is _not_ additive to the defaults;
if you wish to retain the default HTML processing while adding your own output formatters,
you must include `'uncms.html.format_html'` in this list.

## `IMAGE_CLASS_PREFIX`

* Type: string (HTML class name prefix)
* Default: `image`

## `IMAGE_TEMPLATE`

* Type: string (template path)
* Default: `'media/multi_format_image.html'`

The template to use when [rendering images](rendering-images.md).

## `IMAGE_USE_WEBP`

* Type: boolean
* Default: `True`

When [rendering images](rendering-images.md),
WebP versions will be output in a `<source>` element, for browsers that support it.
This is a Web-optimised format supported by almost all browsers and gives substantial size reductions over PNG and JPEG.
To turn this off for whatever reason, set this to `False`.

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

## `MEDIA_UPLOAD_ALLOWED_EXTENSIONS`

* Type: list of strings (file extensions without leading ".")
* Default: `[]`

By default, UnCMS will only allow admin users to upload files with image-like file extensions to the [media library](media-app.md) if they do not have an explicit permission to upload any type of file.
If there are other file extensions you would like to allow,
you can specify them here.
The given file extensions should not have the leading dot.

To allow any file extension, use `'*'`; for this to work, it must be the only value in the list.

## `MEDIA_UPLOAD_ALWAYS_ALLOW_IMAGES`

* Type: boolean
* Default: `True`

Regardless of the value of `MEDIA_UPLOAD_ALLOWED_EXTENSIONS`,
admin users will always be allowed to upload files with image-like file extensions when this option is `True`,
which is the default.
To disable this behaviour, set this configuration item to `False`.

## `MEDIA_UPLOAD_PERMISSIONS_BYPASS`

* Type: boolean
* Default: `True`

Regardless of any values for `MEDIA_UPLOAD_ALWAYS_ALLOW_IMAGES` and `MEDIA_UPLOAD_ALLOWED_EXTENSIONS`,
users with the `media.upload_dangerous_files` permission
(including superusers, which have all permissions)
will always be allowed to upload any kind of file to the [media library](media-app.md).
To force even these users to only allow images and/or files with known file extensions,
set this configuration item to `False`.

## `MEDIA_URLS_NAMESPACE`

* Type: string
* Default: `'media_library'`

The recommended configuration in this documentation is to register the [media library](media-library.md) URLs under the `'media_library'` namespace.
If you are too smart to copy-and-paste examples from the documentation,
or otherwise need to use a different namespace for the media library views,
you may change it with this setting.

## `NAVIGATION_CLASS_PREFIX`

* Type: string
* Default: `'navigation'`

This controls prefixes for HTML class names within the navigation template.
It defaults to `navigation`, which gives class names such as
`.navigation`,
`.navigation__item`,
`.navigation-submenu`,
etc.
See [Rendering page navigation](rendering-navigation.md) for more details.

## `NAVIGATION_TEMPLATE`

* Type: string (template path)
* Default: `'pages/navigation/navigation.html'`

This controls which template will be used to render site navigation.
See [Rendering page navigation](rendering-navigation.md) for more details.

## `NAVIGATION_ITEM_TEMPLATE`

* Type: string (template path)
* Default: `'pages/navigation/navigation_item.html'`

This controls which template will be used to render individual top-level items inside the site navigation.
See [Rendering page navigation](rendering-navigation.md) for more details.

## `NAVIGATION_SUBMENU_TEMPLATE`

* Type: string (template path)
* Default: `'pages/navigation/navigation_submenu.html'`

This controls which template will be used to render sub-menus inside the site navigation.
See [Rendering page navigation](rendering-navigation.md) for more details.

## `NAVIGATION_SUBMENU_ITEM_TEMPLATE`

* Type: string (template path)
* Default: `'pages/navigation/navigation_submenu_item.html'`

This controls which template will be used to render individual items within sub-menus inside the site navigation.
See [Rendering page navigation](rendering-navigation.md) for more details.

## `ONLINE_DEFAULT`

* Type: boolean
* Default: `True`

This controls whether a new `Page` (and anything else that inherits from OnlineBase) will have `is_online` set to True by default when creating new objects in the admin.
Set it to `False` to make new pages be offline by default.

## `PAGE_MODEL`

* Type: string
* Default: 'pages.Page'

This setting should not be changed.
In future, this will permit project-local overrides of the `Page` model,
while continuing to use all the stock UnCMS `Page`-related features
such as middleware, navigation, etc.
See [#23](https://github.com/uncms-dev/uncms/issues/23).

## `PAGE_TREE_PREFETCH_DEPTH`

* Type: boolean
* Default: 2

The depth at which pages will be prefetched, measured from the home page.
By default, pages two levels deep from the home page will be prefetched.
This means that the entire navigation on any site with a homepage, top-level pages, and pages underneath that can be fetched with 3 database queries,
regardless of the number of pages you have on your site.

See the [performance section](performance.md) of this documentation for more on this.

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

## `SITE_DOMAIN`

* Type: string (bare domain name)
* Default: `None` (must be specified)
* Example form: `'example.com'`

This controls the canonical domain name used for converting URLs into paths,
e.g. converting `/path/` to `https://example.com/path/`.
It must be specified (the only mandatory setting here);
UnCMS will refused to start without it.

You do not need to specify a `www.` prefix if this is your preferred host for your site;
if you wish to canonicalise to `www.`, set Django's `PREPEND_WWW` setting to `True`.
Note that if you _do_ specify a `www.` prefix and you have `PREPEND_WWW` set to `True`,
URLs will be canonicalised as `www.www.example.com`, which you probably do not want.

## `WYSIWYG_OPTIONS`

* Type: dictionary
* Default: too large to put here; see `uncms/conf.py`

These are options for the optional [HTML editor](html-editor.md).
These map directly onto TinyMCE options.
A full set of options is available in the [TinyMCE documentation](https://www.tiny.cloud/docs-4x/configure/integration-and-setup/).
