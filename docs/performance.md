# Notes on performance

UnCMS is extremely performant.

The baseline overhead of UnCMS (the pages middleware, rendering the navigation, and accessing a page's content model) is significantly less than 100 milliseconds in local development for a typical mid-sized website with no caching.
A typical production configuration is faster than this.

If your time-to-first-byte performance is suffering, it is likely that your site is badly optimised elsewhere.
Read the [Django documentation](https://docs.djangoproject.com/en/dev/topics/performance/) for ideas as to why your performance is being hurt.

UnCMS has a couple of notable performance pitfalls, which are easy to avoid.

## Page.content is not free (the first time)

Accessing the `content` property of a page causes at least one database query, and sometimes two.
Because it is a [cached property](https://docs.djangoproject.com/en/dev/ref/utils/#django.utils.functional.cached_property),
subsequent accesses of it are close to free, but your first access of it is not.

Treating it as free might be damaging your performance.
A previously-common case of this would be accessing `page.content` for every item in the navigation, for example.
In this case, you should find some means to only access `Page.content` when you know you need to.

## Avoid expensive 404 pages

Because the pages middleware only attempts to render a page at a given URL when that URL would 404 otherwise, your 404 page is rendered before the page is served.
Therefore, if rendering your 404 page is expensive, all pages on your site will be expensive to render too.
In particular, rendering your navigation in your 404 page causes the navigation to be rendered _twice_- once for the 404 page, once for the navigation itself. This almost doubles UnCMS's baseline overhead!

For better results, strip down your 404 page to its absolute minimum.
