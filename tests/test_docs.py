"""
Various tests of the documentation.
"""

# pylint:disable=redefined-outer-name
import dataclasses
import re
from functools import cached_property
from pathlib import Path
from urllib.parse import urlparse

import black
import pytest


@dataclasses.dataclass
class DocFile:
    """
    Dataclass for tracking a Markdown file in `docs/`.
    """

    _: dataclasses.KW_ONLY
    path: Path
    repo_root: Path

    def __hash__(self):
        return hash(self.path)

    @cached_property
    def content(self):
        return self.path.read_text(encoding="utf-8")

    @cached_property
    def lines(self):
        return self.content.split("\n")

    @cached_property
    def relative_path(self):
        # Coverage skipped because it's only used for diagnostics in the
        # failure case.
        return self.path.relative_to(self.repo_root)  # pragma: no cover


@dataclasses.dataclass
class CodeBlock:
    """
    Dataclass for tracking code blocks found in Markdown files in `docs/`.
    """

    _: dataclasses.KW_ONLY
    doc: DocFile
    start: int
    end: int
    lines: list[str]
    language: str | None

    @cached_property
    def text(self) -> str:
        return "\n".join(self.lines)


@dataclasses.dataclass
class Link:
    """
    Dataclass for tracking links found in Markdown files in `docs/`.
    """

    _: dataclasses.KW_ONLY
    doc: DocFile
    line: int
    url: str
    is_image: bool

    @cached_property
    def is_external(self):
        return bool(self.parsed_url.scheme)

    @cached_property
    def has_sensible_proto(self):
        return self.parsed_url.scheme in ["https", "http", "mailto"]

    @cached_property
    def parsed_url(self):
        return urlparse(self.url)

    @cached_property
    def path(self) -> str:
        """The path component of the URL (without query strings or fragments)."""
        return self.parsed_url.path


@pytest.fixture(scope="session")
def docs_dir(repo_root):
    return repo_root / "docs"


@pytest.fixture(scope="session")
def markdown_files(repo_root, docs_dir):
    """
    A fixture for getting all Markdown files in the `docs/` directory. This
    and all the other fixtures here, being session-scoped, just prevent us
    from re-reading the same files every time. We'll load them all once and
    have them in memory.
    """
    return [
        DocFile(path=path, repo_root=repo_root) for path in docs_dir.glob("**/*.md")
    ]


@pytest.fixture(scope="session")
def markdown_code_blocks(markdown_files):
    """
    A fixture for getting all the code blocks in all the Markdown files in
    `docs`.
    """
    blocks = []
    for md_file in markdown_files:
        in_code_block = False
        code_block_start = None
        code_block_lines = []
        code_block_language = None
        for line_num, line in enumerate(md_file.lines, start=1):
            # We're either starting or ending a code block.
            if line.startswith("```"):
                # We're starting a code block.
                if not in_code_block:
                    in_code_block = True
                    code_block_start = line_num
                    code_block_lines = []
                    code_block_language = line[3:].strip() or None
                # We're ending a code block.
                else:
                    blocks.append(
                        CodeBlock(
                            doc=md_file,
                            start=code_block_start,
                            end=line_num,
                            lines=code_block_lines,
                            language=code_block_language,
                        )
                    )
                    in_code_block = False
            elif in_code_block:
                code_block_lines.append(line)

    return blocks


@pytest.fixture(scope="session")
def markdown_links(markdown_files, markdown_code_blocks):
    """
    A fixture for getting all links and images in all the Markdown files in
    `docs`, excluding links inside code blocks.
    """
    # A map of code blocks by file. We don't want to include links shown in
    # code blocks (there's exactly one of these and I don't want to
    # special-case it). Of course we could solve this by having an actual
    # parser rather than bashing it with regexes, but...
    code_blocks_by_file = {}
    for block in markdown_code_blocks:
        code_blocks_by_file.setdefault(block.doc, []).append(block)

    # ...let's bash it with regexes. This matches[text](url) and ![alt](url).
    # LLM says so don't blame me. Of course there are edge cases like Markdown
    # in code blocks (above) but this does 99.9% of the work of a real parser
    # (also it was good enough for Markdown.pl so it's good enough for me).
    link_pattern = re.compile(r"!?\[([^\]]*)\]\(([^)]+)\)")

    links = []
    for md_file in markdown_files:
        for match in link_pattern.finditer(md_file.content):
            is_image = match.group(0).startswith("!")
            url = match.group(2)

            # It would be nice if a match would give us a line number, but.
            line_num = md_file.content[: match.start()].count("\n") + 1

            if md_file in code_blocks_by_file:
                if any(
                    block.start <= line_num <= block.end
                    for block in code_blocks_by_file[md_file]
                ):
                    continue
            assert url
            links.append(
                Link(
                    doc=md_file,
                    line=line_num,
                    url=url,
                    is_image=is_image,
                )
            )

    return links


def test_markdown_code_blocks_have_language(markdown_code_blocks):
    """
    Test that all fenced code blocks in Markdown files have a language
    declaration.
    """
    blocks_without_lang = [
        f"{block.doc.relative_path}:{block.start}"
        for block in markdown_code_blocks
        if block.language is None
    ]

    error_msg = (
        f"Found {len(blocks_without_lang)} fenced code block(s) without language declaration:\n"
        + "\n".join(f"  - {block}" for block in blocks_without_lang)
    )
    assert not blocks_without_lang, error_msg


def test_markdown_python_code_blocks_are_black_formatted(markdown_code_blocks):
    """
    Test that all Python code blocks in Markdown files are formatted with Black.
    """
    unformatted_python_blocks = []

    for block in markdown_code_blocks:
        if block.language == "python" and block.text.strip():
            try:
                formatted = black.format_str(block.text + "\n", mode=black.Mode())
                # `no cover`d because if everything is fine we should not get
                # there
                if block.text + "\n" != formatted:  # pragma: no cover
                    unformatted_python_blocks.append(
                        f"{block.doc.relative_path}:{block.start}"
                    )
            # no cover is as above; we shouldn't get there.
            except black.InvalidInput as e:  # pragma: no cover
                unformatted_python_blocks.append(
                    f"{block.doc.relative_path}:{block.start} (syntax error: {e})"
                )

    error_msg = (
        f"Found {len(unformatted_python_blocks)} Python code block(s) not formatted with Black:\n"
        + "\n".join(f"  - {block}" for block in unformatted_python_blocks)
    )
    assert not unformatted_python_blocks, error_msg


def test_markdown_links_are_valid(markdown_links):
    """
    Test that all internal links in the docs/ directory are to files that
    exist.
    """
    broken_links = []

    for link in markdown_links:
        # Skip the following:
        # - images (we have another test for that)
        # - external URLs (we might want to test those some other time)
        # - "/" (special case to allow linking to the root)
        if link.is_image or link.has_sensible_proto or link.path == "/":
            continue

        # Note using link.doc.path.parent and not docs_dir - don't assume that
        # we'll never have subdirectories in docs_dir.
        target_path = (link.doc.path.parent / link.path).resolve()
        if not target_path.exists():  # pragma: no cover
            broken_links.append(
                f"{link.doc.relative_path}:{link.line}: link to non-existent file '{link.path}' -> {target_path}"
            )

    error_msg = f"Found {len(broken_links)} broken markdown link(s):\n" + "\n".join(
        f"  - {ref}" for ref in broken_links
    )
    assert not broken_links, error_msg


def test_markdown_images_are_valid(markdown_links):
    """
    Test that all image references in markdown files are to local files which
    exist.
    """
    broken_images = []

    for link in markdown_links:
        if not link.is_image:
            continue

        # Refuse external URLs. They can go away at any time.
        if link.is_external:  # pragma: no cover
            broken_images.append(
                f"{link.doc.relative_path}:{link.line}: external image URL not allowed"
            )
            continue

        target_path = (link.doc.path.parent / link.path).resolve()
        if not target_path.exists():  # pragma: no cover
            broken_images.append(
                f"{link.doc.relative_path}:{link.line}: image reference to non-existent file '{link.path}' -> {target_path}"
            )

    error_msg = f"Found {len(broken_images)} broken image reference(s):\n" + "\n".join(
        f"  - {ref}" for ref in broken_images
    )
    assert not broken_images, error_msg
