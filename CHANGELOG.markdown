# Changelog

## 1.0.0

This is the first release of UnCMS, forked from version onespacemedia-cms 4.4.

* Rename! This project is now UnCMS, because it is not quite a CMS.
* Django 3.2 is now supported.
* Localisation support has been removed. It never worked well and it was undocumented.
* TinyPNG support has been removed. Image size reduction is better implemented per-project with post-save hooks.
* django-jet support has been removed, as django-jet is dead.
* usertools support has been removed.
* historylinks is no longer a requirement.
* The `Link.new_window` field has been retired.
* The canonical location of `ImageRefField` is now `cms.apps.media.fields`. This permits easier project-local overrides of the media app, because UnCMS never imports from `cms.apps.media.models`.
