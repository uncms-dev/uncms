import pkg_resources
import pytest


@pytest.mark.parametrize(
    "django_template, jinja2_template",
    [
        (
            "pages/templates/pages/breadcrumbs.html",
            "pages/jinja2/pages/breadcrumbs.jinja2",
        ),
        (
            "templates/edit-bar/edit_bar.html",
            "jinja2/edit-bar/edit_bar.jinja2",
        ),
    ],
)
def test_django_and_jinja_templates_are_identical(django_template, jinja2_template):
    """
    To reduce the maintenance burden of having both Jinja2 and Django
    templates, we should make sure that they are byte-for-byte identical.
    We have to go to minor extra efforts elsewhere to ensure that they *can*
    be (e.g. we track indexes in Python, rather than using "loop.index" or
    "forloop.counter" in the templates). This is worthwhile.
    """
    jinja2_path = pkg_resources.resource_filename("uncms", jinja2_template)
    django_path = pkg_resources.resource_filename("uncms", django_template)

    with open(jinja2_path, encoding="utf-8") as fd:
        jinja2_template_code = fd.read()

    with open(django_path, encoding="utf-8") as fd:
        django_template_code = fd.read()

    assert jinja2_template_code == django_template_code
