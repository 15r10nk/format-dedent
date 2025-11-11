#!/usr/bin/env python3
"""Format only the literal string arguments of textwrap.dedent() calls."""

import ast
import sys
import argparse
from pathlib import Path
from typing import List


class DedentStringFinder(ast.NodeVisitor):
    """Find textwrap.dedent() calls with literal string arguments."""

    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.dedent_strings: List[ast.Constant] = []

    def visit_Call(self, node: ast.Call) -> None:
        """Visit Call nodes to find textwrap.dedent() calls."""
        # Check if this is a call to textwrap.dedent or just dedent
        is_dedent = False

        if isinstance(node.func, ast.Attribute):
            # textwrap.dedent() form
            if (
                node.func.attr == "dedent"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "textwrap"
            ):
                is_dedent = True
        elif isinstance(node.func, ast.Name):
            # dedent() form (imported directly)
            if node.func.id == "dedent":
                is_dedent = True

        if is_dedent and len(node.args) > 0:
            arg = node.args[0]
            # Check if the argument is a literal string (Constant in Python 3.8+)
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                # Store the AST node itself
                self.dedent_strings.append(arg)

        self.generic_visit(node)


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
    import textwrap

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
    import textwrap

    # Parse both versions
    try:
        original_tree = ast.parse(original_code)
        formatted_tree = ast.parse(formatted_code)
    except SyntaxError:
        # If either fails to parse, we can't verify
        return False

    # Find dedent strings in both
    original_finder = DedentStringFinder(original_code.splitlines(keepends=True))
    formatted_finder = DedentStringFinder(formatted_code.splitlines(keepends=True))

    original_finder.visit(original_tree)
    formatted_finder.visit(formatted_tree)

    # Should have the same number of dedent calls
    if len(original_finder.dedent_strings) != len(formatted_finder.dedent_strings):
        return False

    # Compare each pair of dedent strings
    for orig_node, fmt_node in zip(
        original_finder.dedent_strings, formatted_finder.dedent_strings
    ):
        orig_dedented = textwrap.dedent(orig_node.value)
        fmt_dedented = textwrap.dedent(fmt_node.value)

        if orig_dedented != fmt_dedented:
            return False

    return True


class MultilineStringFinder(ast.NodeVisitor):
    """Find multiline string literals that are not already in dedent() calls."""

    def __init__(self):
        self.multiline_strings: List[ast.Constant] = []
        self.dedent_string_ids: set = set()
        self.in_fstring = False

    def visit_Call(self, node: ast.Call) -> None:
        """Track strings inside dedent() calls to skip them."""
        is_dedent = False

        if isinstance(node.func, ast.Attribute):
            if (
                node.func.attr == "dedent"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "textwrap"
            ):
                is_dedent = True
        elif isinstance(node.func, ast.Name):
            if node.func.id == "dedent":
                is_dedent = True

        if is_dedent and len(node.args) > 0:
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                # Mark this string as already in a dedent call
                self.dedent_string_ids.add(id(arg))

        self.generic_visit(node)

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        """Visit f-strings and skip them (can't wrap f-strings with dedent)."""
        # Set flag to skip any string constants inside f-strings
        old_in_fstring = self.in_fstring
        self.in_fstring = True
        self.generic_visit(node)
        self.in_fstring = old_in_fstring

    def visit_Constant(self, node: ast.Constant) -> None:
        """Visit string constants to find multiline strings not in dedent()."""
        # Skip if we're inside an f-string
        if self.in_fstring:
            self.generic_visit(node)
            return

        # Check if the string literal spans multiple lines in the source code
        # (not just if the string value contains newlines)
        if isinstance(node.value, str) and node.lineno != node.end_lineno:
            # Only add if not already tracked as being in a dedent() call
            if id(node) not in self.dedent_string_ids:
                self.multiline_strings.append(node)

        self.generic_visit(node)


def add_dedent(source: str, filename: str = "<string>") -> str:
    """
    Add dedent() calls to multiline strings where dedent(str) == str.

    This wraps multiline strings with textwrap.dedent() when they would
    benefit from it (i.e., when dedenting would not change the string).
    Also adds the necessary import if not present.

    Args:
        source: Python source code as a string
        filename: Optional filename for error messages (default: "<string>")

    Returns:
        The modified source code with dedent() calls added
    """
    import textwrap

    source_lines = source.splitlines(keepends=True)

    # Parse the AST
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as e:
        raise SyntaxError(f"Error parsing {filename}: {e}") from e

    # Find multiline strings not already in dedent() calls
    finder = MultilineStringFinder()
    finder.visit(tree)

    if not finder.multiline_strings:
        return source

    # Check which strings would benefit from dedent
    strings_to_wrap = []
    for node in finder.multiline_strings:
        original = node.value
        dedented = textwrap.dedent(original)
        # Only wrap if dedenting doesn't change the string
        if original == dedented:
            strings_to_wrap.append(node)

    if not strings_to_wrap:
        return source

    # Sort by position (reverse order so we can replace from bottom to top)
    strings_to_wrap = sorted(
        strings_to_wrap, key=lambda n: (n.lineno, n.col_offset), reverse=True
    )

    # Pre-calculate cumulative line positions for O(n) lookups instead of O(n²)
    line_positions = [0]
    for line in source_lines:
        line_positions.append(line_positions[-1] + len(line))

    # Convert source to list of characters for easier manipulation
    source_chars = list(source)

    # Wrap each string with dedent()
    for node in strings_to_wrap:
        start_line = node.lineno - 1
        end_line = node.end_lineno - 1

        # Calculate positions using pre-calculated line positions
        start_pos = line_positions[start_line] + node.col_offset
        end_pos = line_positions[end_line] + node.end_col_offset

        # Get the original string literal
        original_literal = "".join(source_chars[start_pos:end_pos])

        # Wrap with dedent()
        wrapped = f"dedent({original_literal})"

        # Replace in source
        source_chars[start_pos:end_pos] = list(wrapped)

    result = "".join(source_chars)

    # Check if textwrap import exists
    tree = ast.parse(result, filename=filename)
    has_textwrap_import = False
    has_dedent_import = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "textwrap":
                    has_textwrap_import = True
        elif isinstance(node, ast.ImportFrom):
            if node.module == "textwrap":
                for alias in node.names:
                    if alias.name == "dedent":
                        has_dedent_import = True

    # Add import if needed
    if not has_textwrap_import and not has_dedent_import:
        # Find the right place to add the import (after any docstring, before other code)
        lines = result.splitlines(keepends=True)
        insert_pos = 0

        # Skip shebang and encoding declarations
        for i, line in enumerate(lines):
            if line.startswith("#"):
                insert_pos = i + 1
            else:
                break

        # Skip module docstring if present
        try:
            tree = ast.parse(result)
            if (
                tree.body
                and isinstance(tree.body[0], ast.Expr)
                and isinstance(tree.body[0].value, ast.Constant)
                and isinstance(tree.body[0].value.value, str)
            ):
                # There's a module docstring
                docstring_end_line = tree.body[0].end_lineno
                insert_pos = docstring_end_line
        except (SyntaxError, AttributeError):
            pass

        # Insert the import
        import_line = "from textwrap import dedent\n"
        if insert_pos < len(lines):
            lines.insert(insert_pos, import_line)
        else:
            lines.append(import_line)

        result = "".join(lines)

    return result


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
    finder = DedentStringFinder(source_lines)
    finder.visit(tree)

    if not finder.dedent_strings:
        return source

    # Sort by position (reverse order so we can replace from bottom to top)
    dedent_strings = sorted(
        finder.dedent_strings,
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
        escaped_content = formatted_content.replace("\\", "\\\\")  # Escape backslashes first
        if quote == '"""':
            # In triple double quotes, escape any """ sequences
            escaped_content = escaped_content.replace('"""', r'\"\"\"')
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


def format_file(
    file_path: Path, in_place: bool = False, add_dedent_mode: bool = False
) -> str:
    """
    Format dedent strings in a file.

    Args:
        file_path: Path to the Python source file
        in_place: If True, modify the file in place
        add_dedent_mode: If True, add dedent() calls instead of formatting existing ones

    Returns:
        The formatted source code
    """
    source = file_path.read_text()

    try:
        if add_dedent_mode:
            formatted = add_dedent(source, filename=str(file_path))
        formatted = format_dedent_strings(
            formatted if add_dedent_mode else source, filename=str(file_path)
        )
    except SyntaxError as e:
        print(f"{e}", file=sys.stderr)
        sys.exit(1)

    if formatted != source and in_place:
        file_path.write_text(formatted)
        print(f"Formatted {file_path}")

    return formatted


def main():
    parser = argparse.ArgumentParser(
        description="Format only the literal string arguments of textwrap.dedent() calls"
    )
    parser.add_argument(
        "paths",
        type=Path,
        nargs="*",  # Changed from "+" to "*" to allow zero arguments
        help="Python source file(s) or folder(s) to format (reads from stdin if not provided)",
    )
    parser.add_argument(
        "-i", "--in-place", action="store_true", help="Modify the file in place"
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying the file",
    )
    parser.add_argument(
        "--add-dedent",
        action="store_true",
        help="Add dedent() calls to multiline strings where dedent(str) == str",
    )

    args = parser.parse_args()

    # If no paths provided, read from stdin and write to stdout
    if not args.paths:
        if args.in_place:
            print("Error: --in-place cannot be used with stdin input", file=sys.stderr)
            sys.exit(1)

        source = sys.stdin.read()
        try:
            if args.add_dedent:
                formatted = add_dedent(source, filename="<stdin>")
            formatted = format_dedent_strings(
                formatted if args.add_dedent else source, filename="<stdin>"
            )
        except SyntaxError as e:
            print(f"{e}", file=sys.stderr)
            sys.exit(1)

        sys.stdout.write(formatted)
        return

    # Collect all Python files from the given paths
    files_to_format = []
    for path in args.paths:
        if not path.exists():
            print(f"Error: Path {path} does not exist", file=sys.stderr)
            sys.exit(1)

        if path.is_file():
            if path.suffix == ".py":
                files_to_format.append(path)
            else:
                print(f"Warning: Skipping non-Python file: {path}", file=sys.stderr)
        elif path.is_dir():
            # Recursively find all .py files in the directory
            py_files = sorted(path.rglob("*.py"))
            files_to_format.extend(py_files)
        else:
            print(f"Error: {path} is neither a file nor a directory", file=sys.stderr)
            sys.exit(1)

    if not files_to_format:
        print("No Python files found to format", file=sys.stderr)
        sys.exit(1)

    # Format each file
    for file_path in files_to_format:
        formatted = format_file(
            file_path,
            in_place=args.in_place and not args.dry_run,
            add_dedent_mode=args.add_dedent,
        )

        if args.dry_run or not args.in_place:
            # For multiple files, show which file is being displayed
            if len(files_to_format) > 1:
                sys.stdout.write(f"=== {file_path} ===\n")
            sys.stdout.write(formatted)
            if len(files_to_format) > 1:
                sys.stdout.write("\n")  # Empty line between files


if __name__ == "__main__":
    main()
