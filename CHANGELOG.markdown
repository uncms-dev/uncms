# Changelog

## 1.0.0

This is the first release of UnCMS, forked from version onespacemedia-cms 4.4.

* Rename! 🥳 This project is now UnCMS, because it is not quite a CMS. It now has a documented philosophy and a maintainer.
* Django 3.2 is now supported.
* Page localisation support has been removed. Its core idea was fatally flawed; it had an unjustified assumption that a user's _country_ would determine what language they preferred. On top of that, it was undocumented, and it never worked all that well. Not having more than one version of a page is now a core part of the UnCMS philosophy.
* TinyPNG support has been removed. Image size reduction is better implemented per-project with post-save hooks, if it is needed.
* Django Jet support has been removed, because Django Jet is dead.
* usertools dependency has been removed.
* historylinks is no longer a requirement.
* The `Link.new_window` field has been retired. It encouraged the slow practice of checking for `Page.content.new_window` in the navigation.
* The canonical location of `ImageRefField` is now `cms.apps.media.fields`. This permits easier project-local overrides of the media app, because UnCMS's `Page` and helper models no longer import from `cms.apps.media.models`.
* `cms.views.handler500` has been retired, as it does nothing more than Django's built-in 500 view.
* The old pages dashboard item has been retired. It has a new one that works with no Javascript! 🎉
* Probably fix the long-standing bug where the page tree gets randomly mangled.
* The `Video` model in the media app has been retired.
* `cms.context_processors`, which existed to put settings and the package version into templates, no longer exists.
