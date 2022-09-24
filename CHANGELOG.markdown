# Changelog

## 1.0.0

This is the first release of UnCMS, forked from version onespacemedia-cms 4.4.

* Rename! 🥳 This project is now UnCMS, because it is not quite a CMS.
* Django 3.2 is now supported.
* Localisation support has been removed. It never worked well and it was undocumented. Not having more than one version of a page is now a core part of the UnCMS philosophy.
* TinyPNG support has been removed. Image size reduction is better implemented per-project with post-save hooks, if it is needed.
* Django Jet support has been removed, because Django Jet is dead.
* usertools dependency has been removed.
* historylinks is no longer a requirement.
* The `Link.new_window` field has been retired. It encouraged the slow practice of checking for `Page.content.new_window` in the navigation.
* The canonical location of `ImageRefField` is now `cms.apps.media.fields`. This permits easier project-local overrides of the media app, because UnCMS's `Page` and helper models no longer import from `cms.apps.media.models`.
* `cms.views.handler500` has been retired, as it does nothing more than Django's built-in 500 view.
* The old pages dashboard item has been retired. It has a new one that works with no Javascript! 🎉
* Probably fix the long-standing bug where the page tree gets randomly mangled.
