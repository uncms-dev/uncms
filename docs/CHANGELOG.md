# Changelog

## 0.0.12

* The [now-deprecated](https://github.com/mozilla/bleach/issues/698) Bleach has been replaced with [nh3](https://github.com/messense/nh3). As a consequence, `BLEACH_OPTIONS` is now `NH3_OPTIONS`.
* `BLEACH_OPTIONS` was never validated, and that would cause an exception to happen at runtime, where it might not be tested. The replacement `NH3_OPTIONS` is now validated with a system check, because that happens immediately on startup, and is almost free to run.
* The `UNCMS` [configuration](configuration.md) dictionary is now validated to ensure that all keys correspond to known configuration options.
* The dashboard module for the admin homepage no longer explodes if no pages are present.

## 0.0.11

It is now [possible](configuration.md?id=PAGE_ADMIN_ANCESTORS) to configure `PageAdmin` to inherit from arbitrary classes.

## 0.0.10

* It is now [possible](configuration.md?id=OPENGRAPH_FALLBACK_IMAGE) to specify an Open Graph fallback image for `SearchMetaBase` subclasses.
* Twitter fields have been removed from `SearchMetaBase` (and thus `Page`). These fields have for years not merited the prominence they have because Twitter has long supported OpenGraph metadata, and merit it even less now that Twitter is a dying website.
* All model `help_text`s are now translatable.

## 0.0.9

* The [media app](media-app.md) now has `RestrictedFileRefField`. It gives an easy way to have a `FileRefField` which only allows certain file extensions. `ImageRefField` and `VideoRefField` are now subclasses of this.
* SVG files in the file changelist in the media app now display the SVG as a thumbnail.
* The `File` model in the media app now has `contents` (contents of the `File`'s file as bytes), and `text_contents` (same, but as a string). These are intended to be safe to use in templates; they should not raise an exception on I/O errors, or Unicode errors in the case of `text_contents`.
* The fancy grid view for the file changelist in the media app is no longer mangled by very long file titles without spaces (e.g. those which have been auto-generated from a nonsense filename).

## 0.0.8

* Django 4.2 is now a requirement.
* [Testing your project](testing-your-project.md) is now easier;
there are now [Factory Boy](https://factoryboy.readthedocs.io/) factories available for creating UnCMS [pages](pages-app.md) and [media files](media-app.md).
These were written some time ago for testing UnCMS itself. They are now available in the UnCMS package so that you don't need to re-invent them for your project.

## 0.0.7 (2023-03-12)

* The [HTML editor](html-editor.md) now has structure options for `<h[2-4]>` and `<blockquote>`.
* The HTML editor no longer throws a JS exception when adding a new inline formset.
* The sidebar now shows on the page type selection view in the admin.
* A system check now ensures that `MEDIA_URL` is not set to `/`, which will be the case for any project started with `django-admin startproject` and will stop the pages middleware from working (since it skips any request whose path starts with `MEDIA_URL`). A site would almost certainly never be deployed in this configuration; this just avoids mysterious failures in the early stages of development.

## 0.0.6

* There is now an [app for handling redirects](redirects-app.md), allowing redirection of old URLs to new ones. It is a massively upgraded version of the one [built in to Django](https://docs.djangoproject.com/en/dev/ref/contrib/redirects/).
* `HTMLField` now uses [Trumbowyg](https://alex-d.github.io/Trumbowyg/) as its editor. The editor now has a much easier-to-use image insertion tool that does not require IFrames (and thus does not require weakening `X-Frame-Options` from its strictest value). This also _somewhat_ solves the [massive pile of vendor JS](https://github.com/lewiscollard/uncms/issues/14) problem, because Trumbowyg is much smaller; TinyMCE clocked in at 1.4 megabytes minified, and Trumbowyg (minus the plugins we don't need) weighs about 230 kilobytes _unminified_.
* There is now a system check for required middleware and context processors; UnCMS will fail loudly and early if these are not present.
* A system check now ensures that the `PUBLICATION_MIDDLEWARE_EXCLUDE_URLS` config item includes your site's Django admin. Previously, if you had moved your admin to another location for some reason, this would cause offline objects to not appear in your admin. Another system check ensures that `PUBLICATION_MIDDLEWARE_EXCLUDE_URLS` is a list or tuple and _not_ a string; this misconfiguration could also cause it to break silently.
* Add compatibility for Django 4.x series, in anticipation of 4.2 LTS. Tests now pass; this might not necessarily be the same as it _working_.
* `FileAdmin.remote_view` was retired; it was unused. This allowed replacing an existing image file with one from a URL, but not uploading from a remote URL. The latter would have been useful, and may be implemented at some future time.

## 0.0.5

* The `media.upload_dangerous_files` permission added in 0.0.4 caused a model state change that was not reflected in a migration. This has been added.
* Unit tests have been further rationalised.

## 0.0.4

* The previously minimally-functional breadcrumb template tags have been [upgraded](rendering-breadcrumbs.md) to be much more useful out of the box.
* There are restrictions on what files can be uploaded to the [media library](media-app.md). For non-superusers, and those without the new `media.upload_dangerous_files` permission, it defaults to image files only.

## 0.0.3

* WebP rendering was broken in actual browsers. It is not anymore. (The "alpha" warning everywhere in this documentation is real.)

## 0.0.2

* The `html` template filter now uses the multi-format image renderer to downsize images.
* Remove a random vendored jQuery.

## 0.0.1

This is the first public release of UnCMS, forked from onespacemedia-cms version 4.4.4.
It is intended for the fearless and curious.

### The big one

* Rename! 🥳 This project is now UnCMS, because it is not a CMS. It now has a documented [philosophy](philosophy.md) and a maintainer.

### New features

* Massive upgrades to the default navigation templates and tags make the navigation system much more usable as-is. The rendered template now renders sub-items to arbitrary depth, and provides a sensible BEM naming convention for HTML classes that make it possible to target it with sensible CSS. There are now numerous extension points within the templates and in the `{% navigation %}` template tag. There is still no default styling, but a deliberately-ugly sample stylesheet is provided as a starting point. See [Rendering page navigation](rendering-navigation.md) in the documentation for more.
* Rendering page navigation has gained some massive efficiencies (partly as a consequence of removing page localisation). Tweaking the `PAGE_TREE_PREFETCH_DEPTH` option for your site can mean that the number of database queries required to render your navigation is the same as the total _depth_ of your page tree.
* Rendering links to pages referenced in a `ForeignKey` can be made much more efficient by using `RequestPageManager.get_page(page_or_page_id)`. If you have already rendered your navigation (and picked an appropriate `PAGE_TREE_PREFETCH_DEPTH`), this will usually cause zero database queries to be made.
* There is now a multi-format image rendering template tag for rendering your images on the front-end of your site. It has many benefits if you choose to use it, such as having _no_ impact on time-to-first byte, WebP support, and so on. See [rendering images](rendering-images.md) in the documentation for more.

### API changes

* Major renames:
* * all `cms` imports are now `uncms`
* * `cms.plugins.moderation` is now `uncms.moderation` (rationale: "plugins" doesn't make sense)
* * anything under `cms.apps` is now at the top level of the package, e.g. `cms.apps.media -> uncms.media`
* Vanilla Django templates are now supported. Jinja2 is now supported via Django's built-in backend, rather than with django-jinja. See [Using Jinja2 with UnCMS](using-jinja2.md) for details.
* Page localisation support has been removed. Its core idea was fatally flawed; it had an unjustified assumption that a user's _geographical location_ would determine what language they preferred. It was also undocumented and never worked that well. Those things may have been fixable with a rewrite. Instead of a rewrite, not having more than one version of a page is now a core part of the UnCMS [philosophy](philosophy.md). A potentially breaking change here for single-language sites is that _parent and slug uniqueness is now being enforced_; if you have pages with the same parent with non-unique slugs you will need to fix those before migrating, because nothing was stopping you from doing that before. It was intended to be enforced in the past, but did [not work](https://github.com/onespacemedia/cms/issues/180#issuecomment-537069865) when `country_group` was `NULL`.
* The `Video` model in the media app has been retired. Video handling is best implemented per-project.
* The `truncate_paragraphs` function and template filter has been retired, because summaries auto-generated in this way are usually bad.
* `context_processors`, which existed to put settings and the package version into templates, no longer exists. Having settings in the context by default makes it easy to make mistakes which expose secret settings. The package version was only ever there to advertise this software in the admin, but UnCMS no longer cares what your admin looks like.
* `permalinks` has been retired. It made everything with a `get_absolute_url` method publically visible by object enumeration. You probably shouldn't have actual _secret_ stuff hidden that way, but still. It was only in use internally to give permanent links to images inserted in the HTML editor, and that can be implemented in a much simpler and safer way. If you want to avoid links breaking, you might want to consider [django-historylinks](https://github.com/etianen/django-historylinks) instead.
* TinyPNG support has been removed. Image size reduction is better implemented per-project with post-save hooks, if it is needed. It is rarely needed, however, because it's better to store full-size minimally-compressed images and to only reduce their size on output.
* The `html` template filter now sanitises output. It is also sanitised before rendering it in the HTML editor.
* The `Link.new_window` field has been retired. It encouraged the slow practice of checking for `Page.content.new_window` in the navigation.
* The canonical location of `ImageRefField` is now `uncms.media.fields`. This might permit easier project-local overrides of the media app, because UnCMS's `Page` and helper models no longer import from `uncms.media.models`.
* On that note, it should be possible to override the default media file model with the `MEDIA_FILE_MODEL` configuration option.
* `uncms.models.base.BasePage` no longer has `in_navigation`, because this did not make sense for the things `PageBase` is intended for. It is now a field on `Page`. Similarly, `PageBaseAdmin` no longer has `NAVIGATION_FIELDS`.

### Config changes

* Configuration is now handled in a single `UNCMS` dictionary in your config file. `WYSIWYG_OPTIONS` and `PUBLICATION_MIDDLEWARE_EXCLUDE_URLS` now have sensible defaults. If you have changed any of the defaults you may wish to move them into the `UNCMS` configuration dictionary. See [Configuration](configuration.md) for more.
* It is now possible to use a different key for path signing, rather than `SECRET_KEY`.
* Paths in `PUBLICATION_MIDDLEWARE_EXCLUDE_URLS` must now begin with a forward slash.
* `canonical_url` template tag now always returns an HTTPS URL except when `settings.DEBUG == False`.
* `canonical_url` now uses `settings.UNCMS['SITE_DOMAIN']`, and this is now a required setting. (`SITE_DOMAIN` was de facto required in the past, but UnCMS would start without it.)

### Admin

* Django Jet support (really, an undeclared dependency) has been removed, because Django Jet is dead. Not being tied to any particular admin skin, and being made with the stock Django admin as a first-class citizen, is now a core part of the UnCMS philosophy.
* A pile of admin template overrides have been removed.
* The old pages dashboard item has been retired. It has a new one that works with no Javascript! 🎉
* The media app now has a fancy grid list view in the Django admin, using CSS only. It can be turned off with the `MEDIA_LIST_GRID_VIEW` configuration option.
* Image editing in the admin is now done on a separate page, which avoids loading a giant pile of JS when it is not needed.

### Tech debt

* Django 3.2 is now supported. It is the minimum supported Django version.
* `views.handler500` has been retired, as it does nothing more than Django's built-in 500 view.
* The tests have been drastically simplified. There is still work to do.

### Bug fixes, misc fun

* Non-Postgres databases are probably supported. Postgres-specific raw SQL queries have been removed, and tests seem to pass with the `sqlite3` backend.
* `PageMiddleware` now checks for the page requiring authentication _before_ rendering the page. If any view inside a page had a side-effect _and_ `requires_authentication` was used for access control, this could have been a security issue.
* usertools dependency has been removed; how users are handled should be implemented per-project.
* psycopg2 is no longer a requirement, as other databases should be supported. It is still a requirement when using the `[dev]` extra.
* historylinks is no longer a requirement.
* _Probably_ fix the long-standing bug where the page tree gets randomly mangled.
