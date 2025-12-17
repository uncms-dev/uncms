"""
Various tests of Django and Jinja2 template files.
"""

# pylint:disable=redefined-outer-name
# ^ because of the use of fixtures defined in this file being used in this file
import importlib.resources
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import pytest


@dataclass
class Template:
    """
    Dataclass representing the text content of a template.
    """

    path: Path

    @cached_property
    def content(self) -> str:
        return self.path.read_text(encoding="utf-8")

    @cached_property
    def lines(self) -> list[str]:
        return self.content.split("\n")


@pytest.fixture(scope="session")
def all_template_paths(repo_root) -> list[Path]:
    src_dir = repo_root / "src"

    paths = []
    paths.extend(src_dir.glob("**/*.html"))
    paths.extend(src_dir.glob("**/*.jinja2"))
    return sorted(paths)


@pytest.fixture(scope="session")
def all_templates(all_template_paths) -> list[Template]:
    """
    A session-scoped fixture to find all .html and .jinja2 template files in
    `src/`. Being session scoped, with `lines` being a cached_property on the
    objects it returns, it means that we can break out various whitespace
    tests into simpler, separate tests without repeatedly re-reading the
    same files.
    """
    return [Template(path=path) for path in all_template_paths]


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
    jinja2_path = importlib.resources.files("uncms") / jinja2_template
    django_path = importlib.resources.files("uncms") / django_template

    assert jinja2_path.read_text() == django_path.read_text()


def test_templates_use_4_space_indentation(all_templates):
    """
    Check that all templates use indentation that is a multiple of 4. That
    guarantees at least some consistency in indentation.
    """
    failures = []

    for template in all_templates:
        for line_num, line in enumerate(template.lines, start=1):
            # Ignore empty lines; a separate test will look at lines
            # containing only whitespace (which should not be allowed).
            stripped = line.strip()
            if not stripped:
                continue
            # Calculate indentation at the start of the line.
            indent = len(line) - len(line.lstrip())

            # Check if indentation is a multiple of 4
            if indent % 4 != 0:  # pragma: no cover
                failures.append(
                    f"{template.path}:{line_num}: file has indentation of {indent} spaces (not a multiple of 4)"
                )
                # Only report the first error in a file. If one line is wrong,
                # there's a good chance that all of the others are wrong too
                # and there's little point spamming up the output with it. And
                # in such cases a developer would normally go and check the
                # entire file, so giving the rest of the problems probably
                # doesn't help much.
                break

    assert not failures, "\n".join(failures)


def test_templates_have_no_whitespace_only_lines(all_templates):
    """
    Check that templates don't have lines containing only whitespace. That
    should be handled by the editorconfig.
    """
    failures = []

    for template in all_templates:
        for line_num, line in enumerate(template.lines, start=1):
            # Check if line has whitespace but no actual content
            if not line.strip() and line:  # pragma: no cover
                failures.append(
                    f"{template.path}:{line_num}: line contains only whitespace"
                )

    assert not failures, "\n".join(failures)


def test_templates_have_trailing_newline(all_templates):
    """
    Check that all templates end with a newline character.
    """
    failures = []

    for template in all_templates:
        if not template.content.endswith("\n"):  # pragma: no cover
            failures.append(f"{template.path}: file does not end with a newline")

    assert not failures, "\n".join(failures)
