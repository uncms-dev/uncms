# Template tags

A collection of template tags are included with the pages module, mostly for the purposes of simplifying SEO.

## Page metadata tags

### TL;DR

The `<head>` of your document should look like this:

```
{% load uncms_pages %}
<meta name="robots" content="{% meta_robots %}">
<meta name="description" content="{% meta_description %}">

<meta property="og:title" content="{% og_title %}">
<meta property="og:url" content="{% canonical_url %}">
<meta property="og:type" content="website">
<meta property="og:description" content="{% og_description %}">
<meta property="og:image" content="{% og_image %}">

<meta name="twitter:card" content="{% twitter_card %}" />
<meta name="twitter:title" content="{% twitter_title %}" />
<meta name="twitter:description" content="{% twitter_description %}" />
<meta name="twitter:image" content="{% twitter_image %}" />

<link rel="canonical" href="{% canonical_url %}" />

<title>{% block title %}{% title %}{% endblock %}</title>
```

Or,
much more simply,
if you are happy with the way UnCMS behaves by default,
you can include `pages/head_meta.html` which will do this all for you:

```
{% include 'pages/head_meta.html' %}
```

Or for [Jinja2](using-jinja2.md):

```
{% include 'pages/head_meta.jinja2' %}
```

### `{% title %}`

* **Load with:** `{% load uncms_pages %}`
* **[Jinja2](using-jinja2.md) equivalent:** `{{ render_title() }}`

Renders, in this order of priority:

1. The title of the current object, or
2. The title of the current page, or
3. The title of the home page.

```
<title>{% title %}</title>
```

In the first case, it works by simply checking the template context for a key called `title`, and outputs that if it is present
(our [helper views](helpers.md) `PageDetailMixin` and `PageDetailView` will place it there).
As such, you can override the title by setting a context variable called `title`:

```
{% with title = "foo" %}
  {% title %}
{% endwith %}
```

By default this will be rendered with the template `pages/title.html`.
You can override this template if, e.g., you wanted to place the name of your site into every `<title>` tag.

### `{% meta_description %}`

* **Load with:** `{% load uncms_pages %}`
* **[Jinja2](using-jinja2.md) equivalent:** `{{ get_meta_description() }}`

Renders the content of the meta description tag for the current page:

```
<meta name="description" value="{% meta_description %}">
```

You can override the meta description by setting a context variable called `meta_description`.

```
{% with meta_description='foo' %}
  <meta name="description" content="{% meta_description %}">
{% endwith %}
```
You might want to set this in, e.g. the `get_context_data` method of a class-based view to set a default for models that do not inherit from `SearchMetaBase`.

### `{% meta_robots %}`

* **Load with:** `{% load uncms_pages %}`
* **[Jinja2](using-jinja2.md) equivalent:** `{{ get_meta_robots() }}`


Renders the content of the meta robots tag for the current page:

```
<meta name="robots" content="{% meta_robots %}">
```

You can override the meta robots by setting boolean context variables called
`robots_index`, `robots_archive` and `robots_follow`:

```
{% with robots_follow=True %}
  {% meta_robots }}
{% endwith %}
```

You can also provide the meta robots as three boolean arguments to this
tag in the order 'index', 'follow' and 'archive':

```
{% meta_robots True True True %}
```

## Navigation functions

### `{% navigation pages [section] %}`

* **Load with:** `{% load uncms_pages %}`

Renders the site navigation for the given set of pages.

```
{% load pages %}
<nav>
  {% render_navigation pages.homepage.navigation %}
</nav>
```

See [rendering navigation](rendering-navigation.md) for more.


### `render_breadcrumbs(page=None, extended=False)`

Renders the breadcrumbs trail for the current page:

```
{{ render_breadcrumbs() }}
```

This will use the template `pages/breadcrumbs.html`, which you will probably want to override in your project.

To override and extend the breadcrumb trail within page applications, add the `extended` flag to the tag and add your own breadcrumbs underneath:

```
{{ render_breadcrumbs(extended=1) }}
```

### `get_page_url(page, view_func=None, *args, **kwargs)`

Resolves the URL of a route defined in a page's `urlconf`, passing positional and/or keyword arguments to the resolver.
It is a thin wrapper around `Page.reverse`.

```
{{ get_page_url(pages.current, 'article_detail', slug=article.slug) }}
```

### `{% canonical_url %}`

* **Load with:** `{% load uncms_pages %}`
* **[Jinja2](using-jinja2.md) equivalent:** `{{ get_canonical_url() }}`

Returns the canonical URL for the currently viewed URL.
It merely ensures that any query string junk does not cause a page to be indexed more than once by search engines.

## OpenGraph functions (for Facebook and others)
* **Load with:** `{% load uncms_pages %}`
* **[Jinja2](using-jinja2.md) equivalent:** `{{ get_og_title() }}`, `{{ get_og_image() }}`, `{{ get_og_description() }}`


`{% og_title %}`, `{% og_description %}` and `{% og_image %}` render the OpenGraph title, description, and image for the current object.
It is widely used by social media sites and apps (including Facebook) to display link previews.

You will want to use them like so:

```
<meta property="og:title" content="{% og_title %}">
{# note we just use canonical_url for this :) #}
<meta property="og:url" content="{% canonical_url %}">
<meta property="og:type" content="website">
<meta property="og:description" content="{% og_description %}">
<meta property="og:image" content="{% og_image %}">
```

`{% og_title %}` is smart enough to fall back to the current object's browser title override or `title` attribute.

`{% og_image %}` checks for an image to use as an OpenGraph image in the following order:

* if `og_image` is in the context, assume it's an [UnCMS File object](media-library.md) and return its URL
* if `og_image_url` is in the context, assume it is an arbitrary URL with a path part and return a canonicalised version of that URL; you may place `og_image_url` into the context to force an OpenGraph image override using a field which is not an UnCMS File (such as a Django `ImageField`)
* if `object` is in the context (standard for views that inherit from Django's `DetailView`), check the object's `image` and `photo` attributes, in that order; it will return the first of those which are an UnCMS File
* the OpenGraph image of the current page, if it is set

## Twitter card functions

`{% twitter_card %}`, `{% twitter_description %}` and `{% twitter_image %}` render the current Twitter card information for the current object. You will want to use them like so:

```
<!-- Twitter card data -->
<meta name="twitter:card" content="{% twitter_card %}" />
<meta name="twitter:title" content="{% twitter_title %}" />
<meta name="twitter:description" content="{% twitter_description %}" />
<meta name="twitter:image" content="{% twitter_image %}" />
```

If no Twitter card information is set on the current object, Twitter will look at the OpenGraph fields above.
