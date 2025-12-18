# UnCMS

!> **Warning**: UnCMS is currently in alpha, best suited for the curious and fearless.

UnCMS is a developer's CMS toolkit for Django emphasising simplicity, speed, and familiarity.

## System requirements

UnCMS works with the major open source databases supported by Django.
PostgreSQL is recommended, but MySQL and SQLite pass the comprehensive test suite, so will also work fine.

## Installation

`pip install uncms`

## Features

UnCMS comes with just enough features for building small-to-medium-sized content-heavy websites,
and leaves other decisions to your project.
It has no opinions about how your project should be structured,
it has minimal opinions about how your admin area looks,
and it plays well with your existing models.

* Hierarchal [page management](pages-app.md) and [navigation menus](rendering-navigation.md) with no depth limit.
* [Publication controls](publication-control.md) with online preview.
* Pre-configured [WYSIWYG HTML editor](html-editor.md) widgets (using [Trumbowyg](https://alex-d.github.io/Trumbowyg/)).
* [Image and file management](media-app.md), with easy embedding via WYSIWYG editors or pure model fields.
* Internal / external links in menus (via bundled optional [links app](links-app.md)).
* An improved app for creating [redirects](redirects-app.md)
* Version control and rollback (via [django-reversion](https://github.com/etianen/django-reversion)).
* Full-text search with relevance ranking (via [django-watson](https://github.com/etianen/django-watson)).
* Many [helper models](helpers.md) and views for SEO-friendly user-visible models.
* A completely optional [edit bar](edit-bar.md) for the front-end of your site.
* [Support](using-jinja2.md) for Jinja2 templating.

## Getting started

* Read the [philosophy of UnCMS](philosophy.md) to decide if it is a good fit for you.
* Read the [walkthrough](walkthrough.md).
* Clone and have a poke around the [accompanying tiny UnCMS project repo](https://github.com/uncms-dev/tiny-uncms-project).

## Editing this document

This is a [docsify](https://docsify.js.org/) document. For an optimal editing experience:

```bash
npm install -g docsify-cli
docsify serve docs/
```

See the [meta-documentation](DOCUMENTATION-README.md) for more.
