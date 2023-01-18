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

## Do not tread carefully around legacy code

Despite the proud name,
"legacy" refers to old code, which may or may not be good.
UnCMS dates back to 2008,
and has contributions from many different people with varying ideas
(including the current maintainer, who has been many people depending on his mood on a given day).
Parts of it may not adhere to the guidelines in this document.

You will not hurt UnCMS's feelings if you rewrite things that do not make sense,
or if you remove things that are not necessary anymore.
Be bold! If you break something, the tests will probably catch it, and if the tests don't catch it, I probably will.

## Follow my coding style

There are three linters used on this codebase: pylint, flake8, and isort.
They do most of the work of forcing my personal preferences on other people.
The other tiny hills I like to die on follow, with rationales in italics:

* Prefer `'single quotes'` over `"double quotes"`, except for docstrings. _They're easier to type on a UK keyboard without pressing the shift key. I am **that** lazy._
* Avoid fussy indentation on continuation lines; indentation should always be a multiple of 4, and should never be more than 4 spaces than the indentation of the line above it. _I find fussy indentation harder to read._
* Use dangling commas. _It makes diffs easier to read, because insertions and deletions only affect the line inserted or removed, not the one above it._
* Avoid type annotations, except on [data classes](https://docs.python.org/3/library/dataclasses.html). _They provide no clear benefit that I can see and they make code uglier. If your tests are sensible -- see below -- they will uncover basically all bugs that can be caused by type confusion anyway._
* Avoid the Python `match` statement. _This is a misfeature. There is a world in which this could have been implemented in a reasonable and rational way, but that is not the world we got._
* Do not write docstrings or comments if they do not add any useful information to someone reading it. _Comments should help with understanding the code._

## Testing

UnCMS aims for very high code coverage.
Eventually, the goal is to reach 100% coverage, and to enforce this in CI,
so any new features should have full line test coverage.
Any bug fixes should have a regression test, if it makes sense to do so.

You should write new tests as pytest test functions, rather than [unittest](https://docs.python.org/3/library/unittest.mock.html) test classes.
Experience with test classes shows that they tend to smoosh together too many responsibilities,
that repetition is easy to avoid in test functions,
and that whatever repetition remains is cheaper than the complexity that inevitably creeps in to test classes.
If you are changing an existing test which is part of a test class,
it might be best to rewrite that test as a test function.

### Writing tests

With overridden methods of subclasses of standard Django classes,
it is best to test functionality at a higher level,
rather than test individual functions.
This gives you more confidence that the test will remain relevant if Django's API changes in future (or fail loudly if it is not relevant),
which means it is more likely to be meaningful across Django upgrades.
Often, a Django view is the best thing to test.

For example, the ModelAdmin for the File model in the [media app](media-app.md) contains an override of `get_fieldsets`,
to conditionally show or hide the "Usage" fieldset depending on whether a new file is being created or if we are editing an existing one.
It would be tempting to test this function directly,
but we do not care what value this function returns.
We care whether a certain fieldset is correctly shown or hidden on the page.
In this example, we fetch the `admin:media_file_add` `admin:media_file_change` views directly with the test client,
and then peek into the fieldsets from the template context.

Another example, also from the media app, is that the stylesheet for the fancy grid view on the list page is conditionally shown or hidden based on a setting.
The most meaningful way - which happens to be the simplest - to test whether this works is to use BeautifulSoup to look at the rendered HTML,
and see if there is an appropriate `<link>` tag in it or not.

## Don't forget about Jinja2

If you add new template tags, it is a very good idea to make sure there is a Jinja2 global function which does the same thing
(except where this does not make sense, such as for enhancements to `/admin/`).
If you have added templates, it is also a good idea to ensure there are Jinja2
To keep it maintainable,
Jinja2 global functions should take the same arguments,
and Jinja2 templates should be byte-for-byte identical with their Django equivalents.
It's a good idea to write tests to ensure parity between Django and Jinja2;
see [this commit](https://github.com/uncms-dev/uncms/commit/e509b38af17630e75429a433511f5758bbdfd997) for ideas,
or just ask for help from the maintainer.

## JavaScript

Javascript should never be required for anything on the user-visible parts of an UnCMS-powered website,
because UnCMS should never have opinions on such things.

Javascript should rarely be required in the administrative area.
The stock Django admin works fine without it,
so UnCMS should too.

Some things are impossible to implement without JS.
For example, the [HTML editor](html-editor.md) can never be implemented - even awkwardly - without it.
But one should strive for the simplest possible implementation of something.

This maintainer does not like Javascript build systems.
For example, a Webpack build system, even a relatively trivial one, will have several hundred dependencies.
I believe this to be irresponsible.
Until such time as the Node ecosystem moves away from microdependencies, UnCMS will never require a frontend build system for building and developing UnCMS.

If you do write JavaScript, you are free to target only widely-used modern browsers.
That means recent versions of Chromium-based browsers, Firefox, and Safari.
This does not mean that you should use _every_ feature that newer versions of Javascript make available,
because I think many of them are misfeatures.

All JS code should be shipped _unminified_.
This includes vendor code.
Because of UnCMS's JS-light approach, there should never be significant enough amounts of JavaScript on any admin page such that minification would make any real speed improvement.
This includes asset concatenation, too; in the world of HTTP/2 deployments there may be little point in doing this anyway.
