"""AST helper functions for analyzing Python code."""

import ast
from typing import List


def find_dedent_strings(tree: ast.AST) -> List[ast.Constant]:
    """Find textwrap.dedent() calls with literal string arguments."""
    dedent_strings = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

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
                dedent_strings.append(arg)

    return dedent_strings


def add_parent_info(tree: ast.AST) -> None:
    """Add parent attribute to every node in the AST."""
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            child.parent = parent  # type: ignore[attr-defined]


def is_module_level_assignment(node: ast.Constant) -> bool:
    """Check if a string constant is a direct value of a module-level assignment."""
    if not hasattr(node, "parent"):
        return False

    parent = node.parent  # type: ignore[attr-defined]

    # Check if parent is Assign or AnnAssign and node is the direct value
    if isinstance(parent, (ast.Assign, ast.AnnAssign)):
        if parent.value is node:
            # Check if the assignment's parent is ast.Module (module level)
            if hasattr(parent, "parent"):
                assignment_parent = parent.parent  # type: ignore[attr-defined]
                return isinstance(assignment_parent, ast.Module)
    return False


def is_in_dedent_call(node: ast.Constant) -> bool:
    """Check if a string constant is inside a dedent() call."""
    if not hasattr(node, "parent"):
        return False

    parent = node.parent  # type: ignore[attr-defined]

    # Check if parent is a Call node with dedent function
    if isinstance(parent, ast.Call) and parent.args and parent.args[0] is node:
        func = parent.func
        # Check for dedent() or textwrap.dedent()
        if isinstance(func, ast.Name) and func.id == "dedent":
            return True
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "dedent"
            and isinstance(func.value, ast.Name)
            and func.value.id == "textwrap"
        ):
            return True
    return False


def is_in_fstring(node: ast.Constant) -> bool:
    """Check if a string constant is inside an f-string."""
    if not hasattr(node, "parent"):
        return False

    # Walk up to check if any parent is a JoinedStr (f-string)
    current = node
    while hasattr(current, "parent"):
        current = current.parent  # type: ignore[attr-defined]
        if isinstance(current, ast.JoinedStr):
            return True
    return False


def find_multiline_strings(tree: ast.AST) -> List[ast.Constant]:
    """Find multiline string literals that are not already in dedent() calls."""
    # Add parent information to all nodes
    add_parent_info(tree)

    multiline_strings = []
    for node in ast.walk(tree):
        # Check if this is a string constant that spans multiple lines
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.lineno != node.end_lineno
        ):
            # Skip if:
            # 1. Inside an f-string (can't wrap f-strings with dedent)
            # 2. Already in a dedent() call
            # 3. Direct value of a module-level assignment
            if (
                not is_in_fstring(node)
                and not is_in_dedent_call(node)
                and not is_module_level_assignment(node)
            ):
                multiline_strings.append(node)

    return multiline_strings
