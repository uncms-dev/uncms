# UnCMS documentation

!> **Warning**: UnCMS is alpha software.
It is subject to change at no notice,
and version numbers will give no indication of breaking changes until version 1 is released.
Some functionality might be catastrophically broken.
At this time, it is recommended only for the brave.

UnCMS is a collection of Django extensions that add content-management facilities to Django projects.
It is not a CMS, but rather a toolkit that will help you build one,
with an emphasis on speed, simplicity, and familiarity.

## Requirements

UnCMS works best with a PostgreSQL database.
Other databases probably work, but have not been extensively tested.

## Features

UnCMS comes with just enough features for building small-to-medium-sized content-heavy websites,
and leaves other decisions to your project.
It has no opinions about how your project should be structured,
it has minimal opinions about how your admin area looks,
and it plays well with your existing models.

* Hierarchal [page management](pages-app.md) and [navigation menus](rendering-navigation.md) with no depth limit.
* [Publication controls](publication-control.md) with online preview.
* Pre-configured [WYSIWYG editor](html-editor.md) widgets (using TinyMCE).
* [Image and file management](media-app.md), with easy embedding via WYSIWYG editors or pure model fields.
* Internal / external links in menus (via bundled optional [links app](links-app.md)).
* Version control and rollback (via [django-reversion](https://github.com/etianen/django-reversion)).
* Full-text search with relevance ranking (via [django-watson](https://github.com/etianen/django-watson)).
* Many [helper models](helpers.md) and views for SEO-friendly user-visible models.
* [Support](using-jinja2.md) for Jinja2 templating.

## Getting started

* Read the [philosophy of UnCMS](philosophy.md) to decide if it is a good fit for you.
* Read the [walkthrough](walkthrough.md).
* Clone and have a poke around the [accompanying tiny UnCMS project repo](https://github.com/lewiscollard/tiny-uncms-project).

## Editing this document

This is a [docsify](https://docsify.js.org/) document. For an optimal editing experience:

```
npm install -g docsify-cli
docsify serve docs/
```

See the [meta-documentation](DOCUMENTATION-README.md) for more.
