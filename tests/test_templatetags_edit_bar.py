import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser

from tests.mocks import request_with_pages
from tests.testing_app.models import NotRegisteredInAdminModel, PageBaseModel
from uncms.jinja2_environment.edit_bar import render_edit_bar
from uncms.templatetags.uncms_edit_bar import edit_bar
from uncms.testhelpers.factories import UserFactory


def expect_edit_bar(data, *, has_add, has_change, has_query_count):
    soup = BeautifulSoup(data, "html.parser")
    assert soup.find(attrs={"class": "edit-bar"})
    assert bool(soup.find(attrs={"class": "edit-bar__item--add"})) is has_add
    assert bool(soup.find(attrs={"class": "edit-bar__item--edit"})) is has_change
    assert (
        bool(soup.find(attrs={"class": "edit-bar__item--query-count"}))
        is has_query_count
    )


@pytest.mark.parametrize("test_func", [edit_bar, render_edit_bar])
def test_edit_bar_empty_without_user(test_func, simple_page_tree, use_jinja2):
    request = request_with_pages()
    request.user = AnonymousUser()
    context = {
        "request": request,
    }
    assert test_func(context) == ""


@pytest.mark.django_db
def test_edit_bar_with_no_object(use_jinja2):
    request = request_with_pages()
    request.user = UserFactory(superuser=True)
    context = {"request": request, "csrf_token": "abc"}
    rendered = edit_bar(context)
    assert rendered
    # Ensure that the Django version and the Jinja2 version render identically,
    # other than Jinja2 removing trailing whitespace.
    assert rendered.strip() == render_edit_bar(context)
    expect_edit_bar(rendered, has_add=False, has_change=False, has_query_count=False)


@pytest.mark.django_db
def test_edit_bar_with_page_object(use_jinja2, simple_page_tree):
    request = request_with_pages()
    request.user = UserFactory(superuser=True)
    context = {"request": request, "csrf_token": "abc"}
    rendered = edit_bar(context)
    assert rendered
    # Ensure that the Django version and the Jinja2 version render identically,
    # other than Jinja2 removing trailing whitespace.
    assert rendered.strip() == render_edit_bar(context)
    expect_edit_bar(rendered, has_add=True, has_change=True, has_query_count=False)


@pytest.mark.django_db
def test_edit_bar_with_unregistered_object(use_jinja2, simple_page_tree):
    """
    Test that objects not editable in the admin do not show add/change links.
    """
    request = request_with_pages()
    request.user = UserFactory(superuser=True)
    context = {"request": request, "object": NotRegisteredInAdminModel.objects.create()}
    rendered = edit_bar(context)
    assert rendered.strip() == render_edit_bar(context)
    expect_edit_bar(rendered, has_add=False, has_change=False, has_query_count=False)


@pytest.mark.django_db
def test_edit_bar_with_change_permission_only(use_jinja2, simple_page_tree):
    """
    Test that users with only a change permission will only show the change
    link.
    """
    obj = PageBaseModel.objects.create(title="test", slug="test")
    request = request_with_pages()
    request.user = UserFactory(
        is_staff=True, permissions=["testing_app.change_pagebasemodel"]
    )
    context = {"request": request, "object": obj}
    rendered = edit_bar(context)
    assert rendered.strip() == render_edit_bar(context)
    expect_edit_bar(rendered, has_add=False, has_change=True, has_query_count=False)


@pytest.mark.django_db
def test_edit_bar_with_add_permission_only(use_jinja2, simple_page_tree):
    """
    Test that users with only a add permission will only show the add link.
    """
    obj = PageBaseModel.objects.create(title="test", slug="test")
    request = request_with_pages()
    request.user = UserFactory(
        is_staff=True, permissions=["testing_app.add_pagebasemodel"]
    )
    context = {"request": request, "object": obj}
    rendered = edit_bar(context)
    assert rendered.strip() == render_edit_bar(context)
    expect_edit_bar(rendered, has_add=True, has_change=False, has_query_count=False)


@pytest.mark.django_db
def test_edit_bar_with_add_and_change_permissions(use_jinja2, simple_page_tree):
    """
    More branch excercise: make sure that a user with both add and change
    permissions will show both links.
    """
    obj = PageBaseModel.objects.create(title="test", slug="test")
    request = request_with_pages()
    request.user = UserFactory(
        is_staff=True,
        permissions=[
            "testing_app.add_pagebasemodel",
            "testing_app.change_pagebasemodel",
        ],
    )
    context = {"request": request, "object": obj}
    rendered = edit_bar(context)
    assert rendered.strip() == render_edit_bar(context)
    expect_edit_bar(rendered, has_add=True, has_change=True, has_query_count=False)


@pytest.mark.django_db
@pytest.mark.parametrize("debug", [True, False])
def test_edit_bar_shows_query_count(use_jinja2, debug, settings):
    """
    Test the "should the query count show" branch.
    """
    settings.DEBUG = debug
    request = request_with_pages()
    request.user = UserFactory(superuser=True)
    context = {"request": request}
    rendered = edit_bar(context)
    assert rendered.strip() == render_edit_bar(context)
    expect_edit_bar(rendered, has_add=False, has_change=False, has_query_count=debug)
