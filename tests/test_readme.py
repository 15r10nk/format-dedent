"""Test that code examples in README.md are valid and work correctly."""

import re
import ast
from pathlib import Path

import pytest
from inline_snapshot import external_file

from format_dedent.formatter import format_dedent_strings
from format_dedent.add_dedent import add_dedent


def process_readme_code_blocks(readme_content: str) -> str:
    """
    Process README content to ensure code examples are correct.

    HTML comments before code blocks can specify metadata:
    <!-- test: format-input --> - Input for formatting test
    <!-- test: format-output --> - Will be auto-generated from input
    <!-- test: add-dedent-input --> - Input for add-dedent test
    <!-- test: add-dedent-output --> - Will be auto-generated from input
    <!-- test: skip --> - Skip validation for this block
    """
    lines = readme_content.split("\n")
    result_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]
        result_lines.append(line)

        # Check for HTML comment with test metadata
        if line.strip().startswith("<!--") and "test:" in line:
            match = re.search(r"<!--\s*test:\s*(\S+)\s*-->", line)
            if match:
                test_type = match.group(1)
                i += 1

                # Skip empty lines
                while i < len(lines) and not lines[i].strip():
                    result_lines.append(lines[i])
                    i += 1

                # Check for Python code block
                if i < len(lines) and lines[i].strip().startswith("```python"):
                    result_lines.append(lines[i])  # Add ```python line
                    i += 1
                    code_lines = []

                    # Collect code until closing ```
                    while i < len(lines) and not lines[i].strip().startswith("```"):
                        code_lines.append(lines[i])
                        i += 1

                    code = "\n".join(code_lines)

                    # Process based on type
                    if test_type == "format-output":
                        # Don't modify output blocks directly - they're handled by input blocks
                        for code_line in code_lines:
                            result_lines.append(code_line)
                    elif test_type == "format-input":
                        # Add the input code
                        for code_line in code_lines:
                            result_lines.append(code_line)
                        result_lines.append(lines[i])  # Add closing ```
                        i += 1

                        # Look ahead for the output block
                        # Skip lines until we find the format-output comment
                        while i < len(lines):
                            result_lines.append(lines[i])
                            if "<!-- test: format-output -->" in lines[i]:
                                i += 1
                                break
                            i += 1

                        # Skip empty lines
                        while i < len(lines) and not lines[i].strip():
                            result_lines.append(lines[i])
                            i += 1

                        # Found the output block - replace it with formatted code
                        if i < len(lines) and lines[i].strip().startswith("```python"):
                            result_lines.append(lines[i])  # Add ```python
                            i += 1

                            # Skip old output code
                            while i < len(lines) and not lines[i].strip().startswith(
                                "```"
                            ):
                                i += 1

                            # Generate correct output
                            formatted_code = format_dedent_strings(code)
                            for formatted_line in formatted_code.split("\n"):
                                result_lines.append(formatted_line)

                        # Don't add closing ``` yet, let the main loop handle it
                        continue

                    elif test_type == "add-dedent-output":
                        # Same logic for add-dedent
                        for code_line in code_lines:
                            result_lines.append(code_line)
                    elif test_type == "add-dedent-input":
                        # Add the input code
                        for code_line in code_lines:
                            result_lines.append(code_line)
                        result_lines.append(lines[i])  # Add closing ```
                        i += 1

                        # Look ahead for the output block
                        while i < len(lines):
                            result_lines.append(lines[i])
                            if "<!-- test: add-dedent-output -->" in lines[i]:
                                i += 1
                                break
                            i += 1

                        # Skip empty lines
                        while i < len(lines) and not lines[i].strip():
                            result_lines.append(lines[i])
                            i += 1

                        # Found the output block - replace it
                        if i < len(lines) and lines[i].strip().startswith("```python"):
                            result_lines.append(lines[i])  # Add ```python
                            i += 1

                            # Skip old output code
                            while i < len(lines) and not lines[i].strip().startswith(
                                "```"
                            ):
                                i += 1

                            # Generate correct output
                            dedent_code = add_dedent(code)
                            for dedent_line in dedent_code.split("\n"):
                                result_lines.append(dedent_line)

                        continue
                    else:
                        # Other types - just copy as is
                        for code_line in code_lines:
                            result_lines.append(code_line)

                    # Add closing ```
                    if i < len(lines):
                        result_lines.append(lines[i])
                        i += 1
                    continue

        i += 1

    return "\n".join(result_lines)


def test_readme_code_examples_are_correct():
    """
    Test that README code examples are correct and auto-generate correct versions.

    This test reads the README, processes code blocks with test annotations,
    and verifies the README has the correct formatted output examples.

    Run with --inline-snapshot=fix to automatically update the README:
        pytest tests/test_readme.py::test_readme_code_examples_are_correct --inline-snapshot=fix
    """
    readme_path = Path(__file__).parent.parent / "README.md"
    current_readme = readme_path.read_text()

    # Process the README to generate correct code blocks
    correct_readme = process_readme_code_blocks(current_readme)

    # Use external_file with .txt format to handle markdown
    # inline-snapshot will automatically update the file when run with --inline-snapshot=fix
    assert correct_readme == external_file("../README.md", format=".txt")


def test_readme_code_blocks_are_syntactically_valid():
    """All Python code blocks in README should be syntactically valid."""
    readme_path = Path(__file__).parent.parent / "README.md"
    content = readme_path.read_text()

    # Extract all Python code blocks
    blocks = []
    lines = content.split("\n")
    i = 0

    while i < len(lines):
        if lines[i].strip().startswith("```python"):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            code = "\n".join(code_lines)
            if code.strip():
                blocks.append(code)
        i += 1

    # Validate each block
    for code in blocks:
        try:
            ast.parse(code)
        except SyntaxError as e:
            pytest.fail(
                f"Invalid Python syntax in README code block:\n"
                f"Code:\n{code}\n"
                f"Error: {e}"
            )
