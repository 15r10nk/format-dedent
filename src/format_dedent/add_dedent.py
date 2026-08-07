"""Add dedent() calls to multiline strings."""

import ast
import textwrap

from .ast_helpers import find_multiline_strings


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
    source_lines = source.splitlines(keepends=True)

    # Parse the AST
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as e:
        raise SyntaxError(f"Error parsing {filename}: {e}") from e

    # Find multiline strings not already in dedent() calls
    multiline_strings = find_multiline_strings(tree)

    if not multiline_strings:
        return source

    # Check which strings would benefit from dedent
    strings_to_wrap = []
    for node in multiline_strings:
        original = node.value
        assert isinstance(original, str)
        dedented = textwrap.dedent(original)
        # Only wrap if dedenting doesn't change the string
        if original == dedented:
            strings_to_wrap.append(node)

    if not strings_to_wrap:
        return source

    dedent_callable = None
    for import_node in ast.walk(tree):
        if isinstance(import_node, ast.ImportFrom) and import_node.module == "textwrap":
            for alias in import_node.names:
                if alias.name == "dedent":
                    dedent_callable = alias.asname or alias.name
                    break
        elif isinstance(import_node, ast.Import):
            for alias in import_node.names:
                if alias.name == "textwrap":
                    dedent_callable = f"{alias.asname or alias.name}.dedent"
                    break
        if dedent_callable is not None:
            break

    needs_dedent_import = dedent_callable is None
    if needs_dedent_import:
        dedent_callable = "dedent"

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
        assert node.end_lineno is not None
        assert node.end_col_offset is not None
        end_line = node.end_lineno - 1

        # Calculate positions using pre-calculated line positions
        start_pos = line_positions[start_line] + node.col_offset
        end_pos = line_positions[end_line] + node.end_col_offset

        # Get the original string literal
        original_literal = "".join(source_chars[start_pos:end_pos])

        # Wrap with the dedent name provided by the existing imports
        wrapped = f"{dedent_callable}({original_literal})"

        # Replace in source
        source_chars[start_pos:end_pos] = list(wrapped)

    result = "".join(source_chars)

    # Add import if needed
    if needs_dedent_import:
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
                assert docstring_end_line is not None
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
