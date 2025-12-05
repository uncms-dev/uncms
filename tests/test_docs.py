import re


def test_markdown_code_blocks_have_language(repo_root):
    """
    Test that all fenced code blocks in Markdown files have a language
    declaration.
    """
    docs_dir = repo_root / "docs"
    markdown_files = list(docs_dir.glob("**/*.md"))

    blocks_without_lang = []

    for md_file in markdown_files:
        lines = md_file.read_text().split("\n")

        in_code_block = False

        for line_num, line in enumerate(lines, start=1):
            # Check if this line has three backticks at the start
            if line.startswith("```"):
                if not in_code_block:
                    # Opening a code block - check if it has a language
                    if re.match(r"^```\s*$", line):  # pragma: no cover
                        # No language declaration
                        relative_path = md_file.relative_to(repo_root)
                        blocks_without_lang.append(f"{relative_path}:{line_num}")
                    in_code_block = True
                else:
                    # Closing a code block
                    in_code_block = False

    error_msg = (
        f"Found {len(blocks_without_lang)} fenced code block(s) without language declaration:\n"
        + "\n".join(f"  - {block}" for block in blocks_without_lang)
    )
    assert not blocks_without_lang, error_msg
