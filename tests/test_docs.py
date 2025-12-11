"""
Various tests of the documentation.
"""

import dataclasses
from functools import cached_property

import black
import pytest


@dataclasses.dataclass
class CodeBlock:
    _: dataclasses.KW_ONLY
    path: str
    start: int
    lines: list[str]
    language: str | None

    @cached_property
    def text(self) -> str:
        return "\n".join(self.lines)


@pytest.fixture(scope="session")
def markdown_files(repo_root):
    """
    A fixture for getting all Markdown files in the `docs/` directory..
    """
    docs_dir = repo_root / "docs"
    return list(docs_dir.glob("**/*.md"))


@pytest.fixture(scope="session")
# pylint:disable-next=redefined-outer-name
def markdown_code_blocks(markdown_files, repo_root):
    """
    A fixture for getting all the code blocks in all the Markdown files in
    `docs`.
    """
    blocks = []
    for md_file in markdown_files:
        lines = md_file.read_text().split("\n")

        in_code_block = False
        code_block_start = None
        code_block_lines = []
        code_block_language = None

        for line_num, line in enumerate(lines, start=1):
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
                            path=str(md_file.relative_to(repo_root)),
                            start=code_block_start,
                            lines=code_block_lines,
                            language=code_block_language,
                        )
                    )
                    in_code_block = False
            elif in_code_block:
                code_block_lines.append(line)

    return blocks


# pylint:disable-next=redefined-outer-name
def test_markdown_code_blocks_have_language(markdown_code_blocks):
    """
    Test that all fenced code blocks in Markdown files have a language
    declaration.
    """
    blocks_without_lang = [
        f"{block.path}:{block.start}"
        for block in markdown_code_blocks
        if block.language is None
    ]

    error_msg = (
        f"Found {len(blocks_without_lang)} fenced code block(s) without language declaration:\n"
        + "\n".join(f"  - {block}" for block in blocks_without_lang)
    )
    assert not blocks_without_lang, error_msg


# pylint:disable-next=redefined-outer-name
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
                    unformatted_python_blocks.append(f"{block.path}:{block.start}")
            # no cover is as above; we shouldn't get there.
            except black.InvalidInput as e:  # pragma: no cover
                unformatted_python_blocks.append(
                    f"{block.path}:{block.start} (syntax error: {e})"
                )

    error_msg = (
        f"Found {len(unformatted_python_blocks)} Python code block(s) not formatted with Black:\n"
        + "\n".join(f"  - {block}" for block in unformatted_python_blocks)
    )
    assert not unformatted_python_blocks, error_msg
