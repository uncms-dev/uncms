# Rendering and customising breadcrumbs

Sometimes, especially when you have very deep page trees, it is useful to indicate to users where they are on the site.
UnCMS comes with template tags to help you render a page navigation trail,
or "breadcrumbs".

The simplest form of this is the following:

```
{% load uncms_pages %}
<nav aria-label="breadcrumbs">
  {% breadcrumbs %}
</nav>
```

The equivalent [Jinja2](using-jinja2.md) global function is `render_breadcrumbs`;
it takes exactly the same arguments as `{% breadcrumbs %}`.

By default, this will render a trail of breadcrumbs,
with appropriate [structured data markup](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb#microdata),
consisting of the following:

* All pages up to and including the current page's parent.
* If there is an object called "object" in the template context, the current page (_not_ the current object).

Note that this does not include the current page when no `object` is in the context,
and if `object` is in the context, it will not include that object.
That is to say, it will not include whatever page or object the user is currently viewing;
UnCMS calls this the "tail".
Opinions (and designers) differ on whether you should include the tail.
If you would like to include the current page or object in the breadcrumb trail,
use the `show_tail` argument:

```
{% load uncms_pages %}
<nav aria-label="breadcrumbs">
  {% breadcrumbs show_tail=True %}
</nav>
```

You can also override this globally with the [`BREADCRUMBS_SHOW_TAIL`](configuration.md?id=breadcrumbs_show_tail) configuration option.

## Customising with CSS

UnCMS comes with no default styling for breadcrumbs,
because it has no opinions on that kind of thing.
But breadcrumbs are made easy to style, using a sensible BEM class naming convention.
To style them, use the following selectors:

* `.breadcrumbs`: the top-level wrapper for all breadcrumb items (a `<ul>` element)
* `.breadcrumbs__item`: an `<li>` element representing an item in the breadcrumb trail
* `.breadcrumbs__item-link`: the `<a>` element containing a link
* `.breadcrumbs__item-text`: the text inside the `<a>` element

The `breadcrumbs` class prefix is configurable with the [`BREADCRUMBS_CLASS_PREFIX`](configuration.md?id=breadcrumbs_class_prefix) configuration option.
Alternatively, you can override it per instance with the `class_prefix` argument:

```
{% load uncms_pages %}
<nav aria-label="breadcrumbs">
  {% breadcrumbs class_prefix='breadcrumbs-compact' %}
</nav>
```

## Customising the template

You can override the template used for rendering breadcrumbs with the [`BREADCRUMBS_TEMPLATE`](configuration.md?id=breadcrumbs_template) configuration option.
By default, this is `'pages/breadcrumbs.{extension}`, wherein `{extension}` is replaced with the appropriate file extension depending on whether you are using the Django template tag (`.html`) or the Jinja2 global function (`.jinja2`).
You can replace this with your own template, and override one of the following block names if you wish:

* `item_top`: rendered immediately after the opening `<li>` tag
* `item_bottom`: rendered immediately before the closing `</li>` tag

For example, if we want to add an arrow right before the closing `</li>` but _only_ if we are the last element in the list, we could do this:

```
{% extends 'pages/breadcrumbs.html' %}

{% block item_bottom %}
  {% if not breadcrumb.index == count %}<span aria-hidden="true">➡️</span>{% endif %}
{% endblock %}
```

Here, `count` will be available as the total number of breadcrumbs that will be rendered,
and `breadcrumb.index` will be the 1-based index of the breadcrumb being rendered.
Hence, the arrow will only be shown if this is not the last item in the trail.

Note that it is unnecessary to change `BREADCRUMBS_TEMPLATE` if you are using Django templates.
You can simply make your own project-local `pages/breadcrumbs.html` and extend from the base template.
You cannot do this with Jinja2 templates, as that is now how Jinja2 inheritance works;
you will get an infinite loop and hit `RecursionError`.

## Advanced usage

Let's say that we have a containing element for your breadcrumbs,
which has a background colour and a defined height,
and you do not wish to show the breadcrumbs if there are no breadcrumbs to show
(for example, when you are on the homepage).
You also do not wish to show _any_ breadcrumbs unless there are at least 2 items to show;
it might not make sense to show a breadcrumb trail when you are on the top level page.

We can use `{% get_breadcrumbs %}` for this (if you are using Jinja2, it is the `get_breadcrumbs` global function):

```
{% get_breadcrumbs as page_breadcrumbs %}
{% if page_breadcrumbs.count > 2 %}
  <nav aria-label="breadcrumbs">
    {% breadcrumbs page_breadcrumbs %}
  </nav>
{% endif %}
```

`{% get_breadcrumbs %}` will return a `uncms.pages.types.Breadcrumbs` instance,
which has the following attributes:

* `count`, an integer with the count of all breadcrumbs. Note that this _always_ includes tail items (which is why the conditional above is on _more_ than two items)
* `items`, a list of `uncms.pages.types.Breadcrumb` instances, each of which has the following attribute:
* * `title`: visible name of the breadcrumb
* * `url`: URL that the breadcrumb should link to (optional)
* * `index`: 1-based position of the item in the list (first is 1)
* * `index0`: 0-based position of the item in the list (first is 0)

Let's say you also do not want the default behaviour of extending the pages breadcrumb trail with the current object.
But you do have an object called `thingy` in the context which you want to extend it with.

```
{% load uncms_pages %}
{% get_breadcrumbs extend_with=thingy auto_extend=False as page_breadcrumbs %}
{% if page_breadcrumbs.count > 2 %}
  <nav aria-label="breadcrumbs">
    {% breadcrumbs page_breadcrumbs %}
  </nav>
{% endif %}
```

`thingy` can be any of the following things:

* an instance of a Django model; it should define `get_absolute_url` and have a meaningful `__str__`, and this works even better if it is a subclass of `PageBase`
* an instance of `uncms.pages.types.Breadcrumb`
* an iterable containing any of the above

By passing the `breadcrumb_list` parameter, using the same types of parameters, you can even override the trail of pages too,
but that is a niche exercise for the readers that might ever need to do that.
