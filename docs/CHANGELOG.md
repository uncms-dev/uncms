# Changelog

## 1.0.0

This is the first release of UnCMS, forked from onespacemedia-cms version 4.4.

* Rename! 🥳 This project is now UnCMS, because it is not quite a CMS. It now has a documented philosophy and a maintainer.
* Major renames:
* * all `cms` imports are now `uncms`
* * `cms.plugins.moderation` is now `uncms.moderation` (rationale: "plugins" doesn't make sense)
* Django 3.2 is now supported.
* Page localisation support has been removed. Its core idea was fatally flawed; it had an unjustified assumption that a user's _country_ would determine what language they preferred. On top of that, it was undocumented, and it never worked all that well. Not having more than one version of a page is now a core part of the UnCMS philosophy.
* Massive upgrades to the default navigation templates and tags make the navigation system much more usable as-is. The rendered template now renders sub-items to arbitrary depth, and provides a sensible BEM naming convention for HTML classes that make it possible to target it with sensible CSS. There are now numerous extension points within the templates and in the `render_navigation` template function. There is still no default styling, but a deliberately-ugly sample stylesheet is provided as a starting point. See [Rendering page navigation](rendering-navigation.md) in the documentation for more.
* Rendering page navigation has gained some massive efficiencies (partly as a consequence of removing page localisation). Tweaking the `PAGE_TREE_PREFETCH_DEPTH` option for your site can mean that the number of database queries required to render your navigation is the same as the total _depth_ of your page tree.
* `PageMiddleware` now checks for the page requiring authentication _before_ rendering the page. If any view inside a page had a side-effect _and_ `requires_authentication` was used for access control, this could have been a security issue.
* There is now a multi-format image rendering template tag for rendering your images on the front-end of your site. It has many benefits if you choose to use it, such as having _no_ impact on time-to-first byte, WebP support, and so on. See [rendering images](rendering-images.md) in the documentation for more.
* Configuration is now handled in a single `UNCMS` dictionary in your config file. `WYSIWYG_OPTIONS` and `PUBLICATION_MIDDLEWARE_EXCLUDE_URLS` now have sensible defaults. If you have changed any of the defaults you may wish to move them into the `UNCMS` configuration dictionary. See [Configuration](configuration.md) for more.
* It is now possible to use a different key for path signing, rather than `SECRET_KEY`.
* Paths in `PUBLICATION_MIDDLEWARE_EXCLUDE_URLS` must now begin with a forward slash.
* The `html` template filter now sanitises output. It is also sanitised before rendering it in the HTML editor.
* TinyPNG support has been removed. Image size reduction is better implemented per-project with post-save hooks, if it is needed.
* Django Jet support has been removed, because Django Jet is dead. Not being tied to any particular admin skin, and being made with the stock Django admin as a first-class citizen, is now a core part of the UnCMS philosophy.
* usertools dependency has been removed.
* historylinks is no longer a requirement.
* `get_canonical_url` template tag now always returns an HTTPS URL except when `settings.DEBUG == False`.
* `get_canonical_url` now uses `settings.UNCMS['SITE_DOMAIN']`, and this is now a required setting. (It was de facto required in the past, but UnCMS would start without it.)
* The `Link.new_window` field has been retired. It encouraged the slow practice of checking for `Page.content.new_window` in the navigation.
* The canonical location of `ImageRefField` is now `uncms.media.fields`. This permits easier project-local overrides of the media app, because UnCMS's `Page` and helper models no longer import from `uncms.media.models`.
* On that note, it is possible to override the default media file model with the `MEDIA_FILE_MODEL` configuration option.
* The media app now has a fancy grid list view in the Django admin. It can be turned off with the `MEDIA_LIST_GRID_VIEW` configuration option.
* `views.handler500` has been retired, as it does nothing more than Django's built-in 500 view.
* The old pages dashboard item has been retired. It has a new one that works with no Javascript! 🎉
* Probably fix the long-standing bug where the page tree gets randomly mangled.
* The `Video` model in the media app has been retired
.* The `truncate_paragraphs` function and template filter has been retired, as auto-generated summaries are usually bad.
* `context_processors`, which existed to put settings and the package version into templates, no longer exists. Having settings in the context by default makes it easy to make mistakes which expose secret settings. The package version was only ever there to advertise this software in the admin, but UnCMS no longer cares what your admin looks like.
* `uncms.models.base.BasePage` no longer has `in_navigation`, because this did not make sense for the things `PageBase` is intended for. It is now a field on `Page`.
* A pile of template overrides were removed.
* The tests have been drastically simplified. There is still work to do.
