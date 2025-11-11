# format-dedent

A Python formatter that formats **only** the literal string arguments of `textwrap.dedent()` calls in your source files.

## Features

- Finds all `textwrap.dedent()` and `dedent()` calls with literal string arguments
- Formats only those strings (removes trailing whitespace, normalizes spacing)
- Leaves all other code unchanged
- Can preview changes (dry-run mode) or modify files in-place

## Installation

```bash
# From the project directory
pip install format-dedent
```

## Usage as a Pre-commit Hook

You can use `format-dedent` as a [pre-commit](https://pre-commit.com/) hook to automatically format dedent strings before each commit.

### Add to your project

Add this to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/15r10nk/format-dedent
    rev: v0.1.0  # Use the version you want
    hooks:
      - id: format-dedent
```


### Manual run

You can also run it manually on all files:

```bash
pre-commit run format-dedent --all-files
```

## Usage

### Dry-run mode (preview changes)

```bash
python -m format_dedent test_example.py --dry-run
# or
python src/format_dedent/__main__.py test_example.py --dry-run
```

### Format in-place

```bash
python -m format_dedent test_example.py --in-place
# or with shorthand
python -m format_dedent test_example.py -i
```

### Show help

```bash
python -m format_dedent --help
```

## Example

Given a file with:

```python
import textwrap

def get_message():
    return textwrap.dedent("""
        Hello World!
        This has   trailing   spaces.
            And inconsistent indentation.
    """)
```

Running `format-dedent` will format only the string inside `dedent()` by:
1. Removing trailing whitespace
2. Indenting the content 4 spaces more than the parent statement (8 spaces in this case)

```python
import textwrap

def get_message():
    return textwrap.dedent("""
        Hello World!
        This has   trailing   spaces.
            And inconsistent indentation.
""")
```

The indented strings will be properly dedented when the code runs, but in the source file they are formatted to match the visual structure of the output.

Strings not inside `dedent()` calls remain unchanged.

## How it works

1. Parses Python source files using the AST module
2. Finds all `Call` nodes that invoke `textwrap.dedent()` or `dedent()`
3. Determines the indentation level of the parent statement
4. Extracts literal string arguments from these calls
5. Formats the strings by:
   - Removing trailing whitespace
   - Indenting the content with 4 spaces more than the parent statement
   - This makes the code match what the formatted output would look like after `dedent()` runs
6. Replaces the original strings in the source file

The key insight is that the strings are indented in the source to match the visual structure of the actual output after `textwrap.dedent()` processes them.

## Development

### Setup

Install the package with development dependencies:

```bash
pip install -e ".[dev]"
```

### Pre-commit Hooks

This repository uses pre-commit for code quality. To set it up:

```bash
# Install pre-commit hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

### Running tests

The project uses pytest with inline-snapshot for testing:

```bash
# Run tests
pytest tests/

# Run tests with verbose output
pytest tests/ -v
```

### Updating Test Snapshots

The tests use [inline-snapshot](https://15r10nk.github.io/inline-snapshot/) for snapshot testing. If you change the formatter behavior:

```bash
# Review and approve changes interactively
pytest tests/ --inline-snapshot=review

# Automatically update all snapshots
pytest tests/ --inline-snapshot=fix

# Preview what would change without applying
pytest tests/ --inline-snapshot=report
```

### Test coverage

The test suite includes 18 integration tests organized by category:
- Module level dedent (0 spaces → 4 spaces indent)
- Function level dedent (4 spaces → 8 spaces indent)
- Class level dedent (class attributes and methods)
- Nested block dedent (if, for, try/except blocks)
- Quote style preservation (`"""` and `'''`)
- Non-dedent strings remain unchanged
- Trailing whitespace removal
- Empty line preservation
- Real-world examples (SQL, HTML, JSON templates)

## Future enhancements

- Integrate with Black or other formatters for more sophisticated formatting
- Support for f-strings
- Configuration options for formatting style
- Support for formatting string concatenations
