# Agent Instructions for format-dedent

This document provides guidance for AI coding agents working on the `format-dedent` project.

## Project Overview

`format-dedent` is a Python code formatter that specifically formats multiline strings inside `textwrap.dedent()` calls. It ensures that the visual indentation in source code matches what `dedent()` produces at runtime.

**Key Insight:** The tool formats strings so their indentation in the source file visually matches the dedented output, making the code more readable while preserving exact runtime behavior.

## Project Structure

```
format-dedent/
├── src/format_dedent/
│   ├── __init__.py          # Package exports and version
│   ├── __main__.py          # CLI entry point
│   ├── cli.py               # Command-line interface logic
│   ├── formatter.py         # Core formatting functions
│   ├── add_dedent.py        # Add dedent() calls to strings
│   └── ast_helpers.py       # AST analysis utilities
├── tests/
│   ├── test_formatter.py    # Core formatting tests (33 tests)
│   ├── test_cli.py          # CLI integration tests (16 tests)
│   └── test_readme.py       # README code validation (3 tests)
├── README.md                # User documentation
├── pyproject.toml           # Project configuration
└── .pre-commit-hooks.yaml   # Pre-commit hook definition
```

## Development Environment

### Setup
```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Key Dependencies
- **Python 3.8+** - Project supports Python 3.8-3.12+
- **pytest** - Testing framework
- **inline-snapshot** - Snapshot testing (use `--inline-snapshot=fix` to update)
- **pre-commit** - Code quality hooks

### Shell Environment
- **Default shell: fish** - Use fish-compatible syntax in terminal commands
- **No heredocs** - Use `printf` or `echo` instead of EOF heredocs

## Running Tests

```bash
# Run all tests (52 total)
pytest

# Run specific test file
pytest tests/test_formatter.py

# Run with verbose output
pytest -v

# Update inline snapshots
pytest --inline-snapshot=fix

# Run README validation and auto-fix examples
pytest tests/test_readme.py::test_readme_code_examples_are_correct --inline-snapshot=fix
```

**Important:** Always run tests after making changes. The project has excellent test coverage.

## Code Architecture

### Core Modules

#### `ast_helpers.py`
- **Purpose:** AST analysis and node traversal
- **Key Functions:**
  - `find_dedent_strings(tree)` - Find all dedent() calls with string literals (uses `ast.walk()`)
  - `add_parent_info(tree)` - Add parent references to AST nodes
  - `find_multiline_strings(tree)` - Find strings that can be wrapped with dedent()
  - `is_module_level_assignment(node)` - Check if string is module-level
  - `is_in_dedent_call(node)` - Check if string is already in dedent()
  - `is_in_fstring(node)` - Check if string is in an f-string (can't be dedented)

**Design Note:** Uses `ast.walk()` instead of visitor pattern for simplicity. Parent tracking enables context-aware decisions.

#### `formatter.py`
- **Purpose:** Format strings inside dedent() calls
- **Key Functions:**
  - `format_dedent_strings(source, filename)` - Main formatting function
  - `format_string_content(content, indent_level)` - Format individual string
  - `check_format(original, formatted)` - Validate semantic equivalence

**Critical:** Always validates that `dedent(original) == dedent(formatted)` to ensure behavior is preserved.

#### `add_dedent.py`
- **Purpose:** Add dedent() calls to strings where `dedent(str) == str`
- **Function:** `add_dedent(source, filename)` - Wrap strings and add imports
- **Use case:** Automatically add dedent() to strings that don't need dedenting yet

#### `cli.py`
- **Purpose:** Command-line interface
- **Key Functions:**
  - `main()` - Argument parsing and orchestration
  - `format_file(path, in_place, add_dedent_mode)` - Process single file

**CLI Behavior:**
- Default (no flags): Output to stdout
- `--write` / `-w`: Modify files in place
- `--add-dedent`: Add dedent() calls mode

## Making Changes

### Code Style
- **Formatter:** Black (runs in pre-commit)
- **Import style:** Standard library → Third party → Local
- **Type hints:** Not required but appreciated for new code
- **Line length:** 88 characters (Black default)

### Testing Philosophy
1. **Comprehensive coverage** - Every feature has tests
2. **Snapshot testing** - Uses inline-snapshot for expected outputs
3. **Real-world examples** - Tests include SQL, HTML, JSON templates
4. **Semantic validation** - Always verify `dedent(original) == dedent(formatted)`

### Common Tasks

#### Adding a New Feature
1. Write tests first (TDD approach)
2. Implement in appropriate module
3. Update `__init__.py` if adding public API
4. Update README with examples
5. Run `pytest --inline-snapshot=fix` to update snapshots
6. Commit with descriptive message

#### Fixing a Bug
1. Add a failing test that reproduces the bug
2. Fix the bug
3. Verify test passes
4. Run full test suite
5. Commit with "Fix:" prefix

#### Updating Documentation
1. Edit README.md
2. Add test annotations: `<!-- test: format-input -->` and `<!-- test: format-output -->`
3. Run `pytest tests/test_readme.py::test_readme_code_examples_are_correct --inline-snapshot=fix`
4. This auto-generates correct output examples
5. Commit changes

### README Testing System

The README has automated validation using HTML comments:

```markdown
<!-- test: format-input -->
```python
# Input code here
```

<!-- test: format-output -->
```python
# Output will be auto-generated
```
```

**Annotations:**
- `format-input` / `format-output` - Format mode example pairs
- `add-dedent-input` / `add-dedent-output` - Add-dedent mode pairs
- `skip` - Skip validation for this block

**To update:** Run `pytest tests/test_readme.py::test_readme_code_examples_are_correct --inline-snapshot=fix`

## Pre-commit Hooks

The project uses pre-commit hooks:
- `format-dedent` - Run on own codebase
- `black` - Code formatting
- `trailing-whitespace` - Remove trailing spaces
- `end-of-file-fixer` - Ensure newline at EOF
- `check-yaml` - YAML syntax validation
- `check-toml` - TOML syntax validation
- `debug-statements` - Catch debug code

Run manually: `pre-commit run --all-files`

## Key Concepts

### Indentation Logic
- **Module level (0 indent)** → Content gets 4 spaces
- **Function level (4 indent)** → Content gets 8 spaces
- **Nested blocks** → Content indents relative to statement + 4

**Example:**
```python
# Before
def func():
    return dedent("""
    line1
    line2
    """)

# After (content gets 8 spaces - function indent + 4)
def func():
    return dedent("""
        line1
        line2
    """)
```

### What Gets Formatted
✅ Literal strings inside `textwrap.dedent()` calls
✅ Literal strings inside `dedent()` calls (when imported)
❌ Regular strings (not in dedent)
❌ F-strings (can't be wrapped with dedent)
❌ Module-level docstrings
❌ String concatenations

### Safety Guarantees
- **Semantic preservation:** `dedent(original) == dedent(formatted)` always
- **Quote style:** Preserves `"""` vs `'''`
- **Escape sequences:** Correctly handles backslashes
- **Trailing whitespace:** Removed (per dedent semantics)

## Common Pitfalls

### 1. Fish Shell Syntax
❌ **Don't use EOF heredocs:**
```bash
cat <<EOF
content
EOF
```

✅ **Use printf instead:**
```bash
printf 'line1\nline2\n'
```

### 2. AST Parent Tracking
Always call `add_parent_info(tree)` before checking parent relationships:
```python
tree = ast.parse(source)
add_parent_info(tree)  # Required!
if is_module_level_assignment(node):
    ...
```

### 3. Inline Snapshots
When tests fail due to expected output changes:
```bash
# Review changes interactively
pytest --inline-snapshot=review

# Auto-fix all snapshots
pytest --inline-snapshot=fix
```

### 4. Import Statements
The CLI uses absolute imports in `__main__.py` (when run as script):
```python
if __name__ == "__main__":
    from format_dedent.cli import main
    main()
```

## Git Workflow

### Commit Message Format
- `Fix:` - Bug fixes
- `Feat:` - New features
- `Docs:` - Documentation changes
- `Refactor:` - Code refactoring
- `Test:` - Test additions/changes
- `Chore:` - Build/tooling changes

### Before Committing
1. Run `pytest` - All tests must pass
2. Run `pre-commit run --all-files` - All hooks must pass
3. Update README if adding user-facing features
4. Update AGENTS.md if changing architecture

## Building and Publishing

```bash
# Build distribution
uv build

# Check for warnings
uv build 2>&1 | grep -i warning

# Install locally for testing
pip install -e .
```

## Debugging Tips

### 1. Test a Specific Example
```bash
printf 'import textwrap\n\ndef test():\n    return textwrap.dedent("""\n    hello\n    """)\n' | python -m format_dedent
```

### 2. Check AST Structure
```python
import ast
tree = ast.parse(source)
print(ast.dump(tree, indent=2))
```

### 3. Validate Formatting
```python
from format_dedent.formatter import check_format
assert check_format(original, formatted)  # Must be True
```

### 4. Test Pre-commit Hook
```bash
env PYTHONPATH=src python3 -m format_dedent --write file.py
```

## Module Dependencies

```
cli.py
  ├─→ formatter.py
  │     └─→ ast_helpers.py
  └─→ add_dedent.py
        └─→ ast_helpers.py
```

**Important:** Keep modules focused and avoid circular dependencies.

## Performance Considerations

- **AST parsing** - Only parse once per file
- **Parent tracking** - O(n) operation, done once
- **String replacement** - Done in reverse order (bottom-to-top) to maintain positions

## Future Enhancement Ideas

- [ ] Configuration file support (`.format-dedent.toml`)
- [ ] Custom indentation levels
- [ ] IDE integration (LSP server)
- [ ] Integration with Black for combined formatting
- [ ] Support for string concatenations
- [ ] Parallel file processing for large projects

## Questions?

- Check existing tests for examples
- Read module docstrings for detailed API docs
- Review git history for context on design decisions
- The code is well-commented - read the source!

## Last Updated

2025-11-13 - Initial creation with project structure documentation
