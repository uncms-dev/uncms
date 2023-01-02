# Contributing to UnCMS

_WIP: development and testing guide_

## Read the philosophy guide

You should read [the philosophy of UnCMS](philosophy.md) before implementing new features.
There are certain features that will never be considered for UnCMS,
such as multiple concurrent versions of one page.
For example, having the "same" page in two different languages will never be supported.
Publication workflows that require having draft versions and published versions of the same page will never be supported.
And features that are not useful for the overwhelming majority of projects are best implemented in your project,
not in UnCMS.

## Testing

UnCMS aims for a very high code coverage percentage.
Eventually, the goal is to reach 100% coverage, and to enforce this in CI,
so any new features should have full line test coverage.
Any bug fixes might need a regression test.

You should write new tests as pytest test functions.
Experience with test classes shows that they tend to smoosh together too many responsibilities.
If you are changing an existing test which is part of a test class,
it might be best to rewrite that test as a test function.

### Writing tests

With overridden methods of subclasses of standard Django classes,
it is best to test functionality at a higher level,
rather than test individual functions.
This gives you more confidence that the test will remain relevant if Django's API changes in future (or fail loudly if it is not relevant),
which gives you confidence that the thing your tests are across Django upgrades.
Often, a Django view is the best thing to test.

For example, the ModelAdmin for the File model in the [media app](media-app.md) contains an override of `get_fieldsets`,
to conditionally show or hide the "Usage" fieldset depending on whether a new file is being created or if we are editing an existing one.
It would be tempting to test this function directly,
but we do not care what value this function returns.
We care whether a certain fieldset is correctly shown or hidden on the page.
In this example, we fetch the `admin:media_file_add` `admin:media_file_change` views directly with the test client,
and then peek into the fieldsets from the template context.

Another example, also from the media app, is that the stylesheet for the fancy grid view on the list page is conditionally shown or hidden based on a setting.
The simplest way to test that this is working is to use BeautifulSoup to look at the rendered HTML,
and see if there is an appropriate `<link>` tag in it.

## Jinja2

If you add new template tags, it is a very good idea to make sure there is a Jinja2 global function which does the same thing
(except where this does not make sense, such as for enhancements to `/admin/`).
If you have added templates, it is also a good idea to ensure there are Jinja2
To keep it maintainable,
Jinja2 global functions should take the same arguments,
and templates should be byte-for-byte identical with their Django equivalents.
It's a good idea to write tests to ensure parity between Django and Jinja2;
see [this commit](https://github.com/uncms-dev/uncms/commit/e509b38af17630e75429a433511f5758bbdfd997) for ideas,
or just ask for help from the maintainer.
