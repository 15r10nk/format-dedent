"""CLI for format-dedent."""

import sys
import argparse
from pathlib import Path

from .formatter import format_dedent_strings
from .add_dedent import add_dedent


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
        "-w",
        "--write",
        action="store_true",
        help="Write changes to files (default: output to stdout)",
    )
    parser.add_argument(
        "--add-dedent",
        action="store_true",
        help="Add dedent() calls to multiline strings where dedent(str) == str",
    )

    args = parser.parse_args()

    # If no paths provided, read from stdin and write to stdout
    if not args.paths:
        if args.write:
            print("Error: --write cannot be used with stdin input", file=sys.stderr)
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
            in_place=args.write,
            add_dedent_mode=args.add_dedent,
        )

        if not args.write:
            # For multiple files, show which file is being displayed
            if len(files_to_format) > 1:
                sys.stdout.write(f"=== {file_path} ===\n")
            sys.stdout.write(formatted)
            if len(files_to_format) > 1:
                sys.stdout.write("\n")  # Empty line between files
