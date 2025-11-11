"""Formatting logic for dedent strings."""

import ast
import textwrap
from typing import List

from .ast_helpers import find_dedent_strings


def format_string_content(content: str, indent_level: int = 0) -> str:
    """
    Format the content of a string by indenting it properly.
    The content will be indented to align with the opening quote.

    Args:
        content: The string content to format
        indent_level: The target indentation level (in spaces) - aligns with the opening quote

    Returns:
        The formatted string with proper indentation
    """
    # First dedent to get the "real" content without any indentation
    dedented = textwrap.dedent(content)

    # Remove leading/trailing empty lines
    lines = dedented.split("\n")

    # Find first and last non-empty lines
    first_non_empty = 0
    last_non_empty = len(lines) - 1

    for i, line in enumerate(lines):
        if line.strip():
            first_non_empty = i
            break

    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip():
            last_non_empty = i
            break

    # Keep leading/trailing empty lines but process the content
    result_lines = []
    indent_str = " " * indent_level  # Use the exact indentation level passed

    for i, line in enumerate(lines):
        if i < first_non_empty or i > last_non_empty:
            # Keep empty lines at start/end empty
            result_lines.append("")
        elif line.strip():
            # Non-empty line: add indentation (preserve trailing whitespace)
            result_lines.append(indent_str + line)
        else:
            # Empty line in the middle: keep it empty
            result_lines.append("")

    return "\n".join(result_lines)


def check_format(original_code: str, formatted_code: str) -> bool:
    """
    Check that formatting doesn't change the semantics of dedent strings.

    Verifies that dedent(original_string) == dedent(formatted_string) for all
    dedent() calls in the code.

    Args:
        original_code: The original source code
        formatted_code: The formatted source code

    Returns:
        True if the formatting is semantically equivalent, False otherwise
    """
    # Parse both versions
    try:
        original_tree = ast.parse(original_code)
        formatted_tree = ast.parse(formatted_code)
    except SyntaxError:
        # If either fails to parse, we can't verify
        return False

    # Find dedent strings in both
    original_strings = find_dedent_strings(original_tree)
    formatted_strings = find_dedent_strings(formatted_tree)

    # Should have the same number of dedent calls
    if len(original_strings) != len(formatted_strings):
        return False

    # Compare each pair of dedent strings
    for orig_node, fmt_node in zip(original_strings, formatted_strings):
        orig_dedented = textwrap.dedent(orig_node.value)
        fmt_dedented = textwrap.dedent(fmt_node.value)

        if orig_dedented != fmt_dedented:
            return False

    return True


def format_dedent_strings(source: str, filename: str = "<string>") -> str:
    """
    Format only the literal string arguments of textwrap.dedent() calls.

    Args:
        source: Python source code as a string
        filename: Optional filename for error messages (default: "<string>")

    Returns:
        The formatted source code
    """
    source_lines = source.splitlines(keepends=True)

    # Parse the AST
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as e:
        raise SyntaxError(f"Error parsing {filename}: {e}") from e

    # Find dedent strings
    dedent_strings_list = find_dedent_strings(tree)

    if not dedent_strings_list:
        return source

    # Sort by position (reverse order so we can replace from bottom to top)
    dedent_strings = sorted(
        dedent_strings_list,
        key=lambda node: (node.lineno, node.col_offset),
        reverse=True,
    )

    # Pre-calculate cumulative line positions for O(n) lookups instead of O(n²)
    line_positions = [0]
    for line in source_lines:
        line_positions.append(line_positions[-1] + len(line))

    # Convert source to list of characters for easier manipulation
    source_chars = list(source)

    # Replace each dedent string
    for node in dedent_strings:
        lineno = node.lineno
        col_offset = node.col_offset
        end_lineno = node.end_lineno
        end_col_offset = node.end_col_offset
        opening_quote_col = node.col_offset
        # Convert to 0-based indexing
        start_line = lineno - 1
        end_line = end_lineno - 1

        # Calculate actual position in source using pre-calculated positions
        start_pos = line_positions[start_line] + col_offset
        end_pos = line_positions[end_line] + end_col_offset

        # Extract the original string literal (including quotes)
        original_literal = "".join(source_chars[start_pos:end_pos])

        # Determine quote style
        if original_literal.startswith('"""') or original_literal.startswith("'''"):
            quote = original_literal[:3]
            quote_len = 3
        elif original_literal.startswith('"') or original_literal.startswith("'"):
            quote = original_literal[0]
            quote_len = 1
        else:
            continue  # Skip if we can't determine quote style

        # Check if there's a backslash after the opening quotes (line continuation)
        has_backslash = original_literal[quote_len : quote_len + 1] == "\\"

        original_content = str(node.value)

        # Determine the correct indentation for the content
        # Get the line where the opening quote is
        quote_line = source_lines[start_line].rstrip("\n\r")
        first_non_space = len(quote_line) - len(quote_line.lstrip())

        # Check if the opening quote is at the start of the line (possibly with leading whitespace)
        if opening_quote_col == first_non_space:
            # Quote is at the start of the line, use its indentation
            content_indent = opening_quote_col
        else:
            # Quote is after other code on the line, use line indentation + 4
            content_indent = first_non_space + 4

        # Format the content with proper indentation
        formatted_content = format_string_content(original_content, content_indent)

        # Escape the formatted content for the target quote style
        # We need to escape backslashes and the quote character being used
        escaped_content = formatted_content.replace(
            "\\", "\\\\"
        )  # Escape backslashes first
        if quote == '"""':
            # In triple double quotes, escape any """ sequences
            escaped_content = escaped_content.replace('"""', r"\"\"\"")
        elif quote == "'''":
            # In triple single quotes, escape any ''' sequences
            escaped_content = escaped_content.replace("'''", r"\'\'\'")
        elif quote == '"':
            escaped_content = escaped_content.replace('"', '\\"')
        elif quote == "'":
            escaped_content = escaped_content.replace("'", "\\'")

        # Reconstruct the string literal
        # If there was a backslash after the opening quote, we need to add newline after it
        if has_backslash:
            # Backslash continuation: add newline after backslash
            opening = f"{quote}\\\n"
        else:
            opening = quote

        # Add proper indentation to the closing quote if the content ends with a newline
        if escaped_content.endswith("\n"):
            # Remove the trailing newline and add closing quote at the line's indentation
            formatted_literal = (
                f"{opening}{escaped_content[:-1]}\n{' ' * first_non_space}{quote}"
            )
        else:
            formatted_literal = f"{opening}{escaped_content}{quote}"

        # Replace in source
        source_chars[start_pos:end_pos] = list(formatted_literal)

    # Convert back to string
    formatted_source = "".join(source_chars)

    # Verify that formatting preserves semantics
    if not check_format(source, formatted_source):
        raise RuntimeError(
            f"Formatting validation failed for {filename}: dedented strings don't match"
        )

    return formatted_source
