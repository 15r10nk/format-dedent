"""Test that code examples in README.md are valid and work correctly."""

import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import pytest
from inline_snapshot import external_file

from format_dedent.add_dedent import add_dedent
from format_dedent.formatter import format_dedent_strings


@dataclass
class CodeBlock:
    """Represents a code block in markdown with optional test metadata."""

    header_comment: Optional[
        str
    ]  # Comment before block: output, add-dedent-output, etc.
    language: str  # python, bash, etc.
    code: str  # The actual code content
    start_line: int  # Line number where block starts


def transform_markdown(
    markdown_source: str, transformation: Callable[[CodeBlock], CodeBlock]
) -> str:
    """
    Transform code blocks in markdown using the provided transformation function.

    Args:
        markdown_source: The markdown content to transform
        transformation: Function that takes a CodeBlock and returns a transformed CodeBlock

    Returns:
        Transformed markdown content
    """
    lines = markdown_source.split("\n")
    result_lines = []
    i = 0

    while i < len(lines):
        # Look for HTML comment with test metadata
        header_comment = None
        if lines[i].strip().startswith("<!--") and "test:" in lines[i]:
            match = re.search(r"<!--\s*test:\s*(\S+)\s*-->", lines[i])
            if match:
                header_comment = match.group(1)
            result_lines.append(lines[i])
            i += 1

        # Look for code block start
        if i < len(lines) and lines[i].strip().startswith("```"):
            language_match = re.match(r"```(\w+)", lines[i].strip())
            language = language_match.group(1) if language_match else ""

            result_lines.append(lines[i])  # Add opening ```
            i += 1
            code_lines = []

            # Collect code until closing ```
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1

            # Create and transform the block
            if code_lines:
                block = CodeBlock(
                    header_comment=header_comment,
                    language=language,
                    code="\n".join(code_lines),
                    start_line=len(result_lines),
                )
                transformed_block = transformation(block)

                # Add transformed code (or original if transformation returned None)
                result_block = transformed_block if transformed_block else block
                for line in result_block.code.split("\n"):
                    result_lines.append(line)

            # Add closing ```
            if i < len(lines):
                result_lines.append(lines[i])
                i += 1
        else:
            result_lines.append(lines[i])
            i += 1

    return "\n".join(result_lines)


def process_readme_code_blocks(readme_content: str) -> str:
    """
    Process README content to ensure code examples are correct.

    Uses transform_markdown with a callback that uses the last code block
    before an output annotation as the input.
    """
    last_code_block = None  # Local scope accessible by callback

    def transformation(block: CodeBlock) -> CodeBlock:
        """Transform callback that can access last_code_block from outer scope."""
        nonlocal last_code_block

        if block.header_comment == "output":
            # Generate output by formatting the last code block
            if last_code_block:
                return CodeBlock(
                    header_comment=block.header_comment,
                    language=block.language,
                    code=format_dedent_strings(last_code_block.code),
                    start_line=block.start_line,
                )
            return block

        elif block.header_comment == "add-dedent-output":
            # Generate output by adding dedent to the last code block
            if last_code_block:
                return CodeBlock(
                    header_comment=block.header_comment,
                    language=block.language,
                    code=format_dedent_strings(add_dedent(last_code_block.code)),
                    start_line=block.start_line,
                )
            return block

        # Store this block as the last one (for next output block to use)
        last_code_block = block
        return block

    return transform_markdown(readme_content, transformation)


def test_readme_code_examples_are_correct():
    """
    Test that README code examples are correct and auto-generate correct versions.

    This test reads the README, processes code blocks with test annotations,
    and verifies the README has the correct formatted output examples.

    Run with --inline-snapshot=fix to automatically update the README:
        pytest tests/test_readme.py::test_readme_code_examples_are_correct --inline-snapshot=fix
    """
    readme_path = Path(__file__).parent.parent / "README.md"
    current_readme = readme_path.read_text(encoding="utf-8")

    # Process the README to generate correct code blocks
    correct_readme = process_readme_code_blocks(current_readme)

    # Use external_file with .txt format to handle markdown
    # inline-snapshot will automatically update the file when run with --inline-snapshot=fix
    if sys.platform == "win32":
        # pathlib normalizes CRLF while external_file preserves checkout endings.
        assert correct_readme == current_readme
    else:
        assert correct_readme == external_file("../README.md", format=".txt")


def test_readme_code_blocks_are_syntactically_valid():
    """All Python code blocks in README should be syntactically valid."""
    readme_path = Path(__file__).parent.parent / "README.md"
    content = readme_path.read_text(encoding="utf-8")

    def validate_syntax(block: CodeBlock) -> CodeBlock:
        """Validate Python syntax for each code block."""
        if block.language == "python" and block.code.strip():
            try:
                ast.parse(block.code)
            except SyntaxError as e:
                pytest.fail(
                    f"Invalid Python syntax in README code block:\n"
                    f"Code:\n{block.code}\n"
                    f"Error: {e}"
                )
        return block

    # Transform markdown and validate all blocks (ignore the result)
    transform_markdown(content, validate_syntax)
