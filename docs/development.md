# Contributing to UnCMS

_WIP: development and testing guide_

## Read the philosophy guide

[]

## Testing

UnCMS aims for a very high code coverage percentage.
Eventually, the goal is to reach 100% coverage, and to enforce this in CI.
Any new features should probably have a test.
Any bug fixes might need a regression test.

You should write new tests as pytest test functions.
Experience with test classes shows that they tend to smoosh together too many responsibilities.
If you are changing an existing test which is part of a test class,
it might be best to rewrite that test as a test function.

### Writing tests

With overridden methods of subclasses of standard Django classes,
it is best to test functionality at a higher level,
rather than test the functionality itself.
This means that the test will fail if Django's API changes in future,
which gives you confidence that it will work across Django upgrades.
Often, the Django view is the best place to write the test.

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

Generally, if you find yourself making mocks for an HTTP request,
it is a sign that you are trying to test at too low a level.
