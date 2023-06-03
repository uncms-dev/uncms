# The philosophy of UnCMS

UnCMS is intended to provide the minimum of functionality to build most CMS-backed websites.
Some of its philosophy is by [historic accident](history.md).
Some of it is by design.
Some of it has come from mistakes tried and made.
And a little of it comes by doing the opposite of what other Django CMSes are doing -
not because those things are the wrong things to do, but because other Django CMSes are doing those things already.

## Exactly one page will live at one URL

Specifically, it will never support things like
separate draft/published versions of the same page,
or different versions of the same page for different languages.
Supporting these cases massively increases complexity,
makes obvious performance optimisations harder,
and, in my experience, is rarely _needed_ for the small-to-medium-sized sites this project targets.
This decision was made with the full awareness that it will preclude using UnCMS for some projects.

For example, the [immediate ancestor of UnCMS](history.md) had internationalisation support.
This was one of the first features to be removed in the transition to UnCMS.
It never worked very well.
In some significant part, this was because it was minimally tested in the real world,
because most sites did not require it (I can think of four sites out of hundreds of previous deployments of the ancestor CMS);
it tended to cause occasional [bugs](https://github.com/onespacemedia/cms/issues/180) in projects which _didn't_ use it.
It ruined performance, though some later versions optimised this away with conditionals.

If multilingual support is important to you, you may want to look at [django CMS](https://www.django-cms.org/en/) instead of UnCMS.
Note, however, that UnCMS does _not_ preclude building multilingual or geographically-localised sites.
It merely has no opinion on how that should be implemented.

## UnCMS projects should look like Django projects

There will never be a requirement to use special fields for models on a UnCMS project.
This reduces the overhead required to get started with UnCMS,
and makes it easier to implement it progressively within an existing project.

## UnCMS does not have an opinion on your administrative interface

UnCMS has almost no opinions about what your `/admin/` should look like, or how it should behave.
The only place it has opinions is on the "Add a page" screen, which is trivial to override in your local project if you do not like it.
It must work fine with the standard Django administration.
It should also play nice with your favourite admin skin, too.
Patches are always welcomed to make it play better with any Django admin skin.

The immediate ancestor of UnCMS was heavily dependent on some admin skin or other, changing twice in its life.
The lesson taught was that admin skins tend to fall into dismaintenance after a few versions, so it is unwise to tie UnCMS to any admin skin;
the first priority for UnCMS is to make it work well with Django's built-in admin.
Django's built-in admin is not as pretty as it could be, but it is functional enough and it is stable.

If a beautiful admin interface out of the box is important to you,
or you wish to have features such as arbitrarily deeply-nested inlines,
you will certainly want to consider [Wagtail](https://wagtail.org/) instead of UnCMS.

## UnCMS will resist adding features

If a feature is not useful for the overwhelming majority of small-to-medium-sized sites, it probably will not be added.
If a feature is useful for many sites, but can reasonably be implemented per-project, it might not be added.
If a change _facilitates_ adding useful features to projects that use UnCMS,
such as by adding extension points,
it might well be added.

## Performance matters

Having a [performant UnCMS site](performance.md) should not depend on hot-rodding tricks such as caching.
Local development should be as performant as production development,
and setup of a performant local development environment should be as simple as possible.

Of course, it should always play nicely with caching tools and other hot-rodding tricks, too.

## Documentation matters

[This documentation](DOCUMENTATION-README.md) was written with love for the reader and joy in the heart.
I hope you enjoy reading it as much as I enjoyed writing it.

UnCMS will never have documentation generated from the source code,
because auto-generated documentation is not documentation.
Comments and docstrings in the UnCMS source code should assist a developer's understanding of the UnCMS source code.
Documentation should assist a developer's understanding of using UnCMS.

Ease of writing documentation also matters.
That is why this documentation uses [Docsify](https://docsify.js.org/).
I am fully aware of the reasons Markdown [should not be used for documentation](https://ericholscher.com/blog/2016/mar/15/dont-use-markdown-for-technical-docs/),
But Markdown has the distinct advantage that almost every developer knows Markdown.
A previous incarnation of UnCMS used a Sphinx-based build system.
Nobody cared much to learn it, so the documentation almost never got updated.
Technically, the system behind the documentation you are reading now is probably inferior to the old one by some measures, but vastly superior overall for one reason:
the easier it is to update documentation, the more likely it is to be done.
