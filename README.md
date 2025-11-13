# format-dedent

**Format multiline strings with proper indentation** — A Python code formatter that formats **only** the literal string arguments of `textwrap.dedent()` calls.

## ✨ What does it do?
![ci](https://github.com/15r10nk/format-dedent/actions/workflows/ci.yml/badge.svg?branch=main)
[![Docs](https://img.shields.io/badge/docs-mkdocs-green)](https://15r10nk.github.io/format-dedent/)
[![pypi version](https://img.shields.io/pypi/v/format-dedent.svg)](https://pypi.org/project/format-dedent/)
![Python Versions](https://img.shields.io/pypi/pyversions/format-dedent)
![PyPI - Downloads](https://img.shields.io/pypi/dw/format-dedent)
[![coverage](https://img.shields.io/badge/coverage-100%25-blue)](https://15r10nk.github.io/format-dedent/contributing/#coverage)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/15r10nk)](https://github.com/sponsors/15r10nk)

`format-dedent` automatically formats multiline strings inside `textwrap.dedent()` calls to make them visually match their runtime output. This makes your code more readable while preserving the exact behavior.

**Key features:**
- 🎯 **Surgical precision** — Only formats strings inside `dedent()` calls, leaves everything else untouched
- 🔄 **Two modes** — Format existing dedent strings OR automatically add `dedent()` to strings that need it
- 👀 **Safe** — Validates that formatting doesn't change runtime behavior
- 🎨 **Smart indentation** — Aligns content with the visual structure of your code
- 🧹 **Clean** — Removes trailing whitespace and normalizes spacing

---

## 📦 Installation

```bash
uv tool install format-dedent
```

---

## 🚀 Quick Start

### Format strings (default mode)

Preview formatted output without modifying files:
```bash
uvx format-dedent yourfile.py
```

Write changes to files:
```bash
uvx format-dedent yourfile.py --write
```

Format multiple files or directories:
```bash
uvx format-dedent src/ tests/ --write
```

### Add dedent() calls (--add-dedent mode)

Automatically wrap multiline strings with `dedent()` calls:
```bash
uvx format-dedent yourfile.py --add-dedent --write
```

This will:
- Find multiline strings where `dedent(str) == str` (no leading indentation to remove)
- Wrap them with `dedent()` calls
- Add `from textwrap import dedent` import if needed

---

## 📖 Usage Options

```bash
python -m format_dedent [OPTIONS] [FILES/DIRECTORIES]

Options:
  -w, --write       Write changes to files (default: output to stdout)
  --add-dedent      Add dedent() calls to multiline strings
  -h, --help        Show help message
```

**Behavior:**
- **Default** → Output formatted code to stdout (no file modification)
- **`--write`** → Modify files directly and print confirmation

---

## 🔧 Pre-commit Hook

Use `format-dedent` as a [pre-commit](https://pre-commit.com/) hook to automatically format dedent strings before each commit.

Add this to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/15r10nk/format-dedent
    rev: v0.1.0  # Use the latest version
    hooks:
      - id: format-dedent
```

---

## 💡 Examples

### Example 1: Formatting SQL queries

**Before formatting:**

```python
import textwrap

def get_sql_query():
    return textwrap.dedent("""
SELECT users.name, orders.total
FROM users
JOIN orders ON users.id = orders.user_id
WHERE orders.status = 'complete'
    """)
```

Inconsistent indentation inside the string makes it hard to read and understand the actual SQL query structure.

**After formatting:**

<!-- test: output -->
```python
import textwrap

def get_sql_query():
    return textwrap.dedent("""
        SELECT users.name, orders.total
        FROM users
        JOIN orders ON users.id = orders.user_id
        WHERE orders.status = 'complete'
    """)
```

**The key insight:** The indentation you see in the source code now matches what `dedent()` returns. When this code runs, `dedent()` strips the common leading whitespace, and you get properly formatted SQL.

### Example 2: Using --add-dedent mode

**Before:**

```python
def get_message():
    message = """
Hello World!
This is a message.
"""
    return message
```

**After running with `--add-dedent`:**

<!-- test: add-dedent-output -->
```python
from textwrap import dedent
def get_message():
    message = dedent("""
        Hello World!
        This is a message.
    """)
    return message
```

✅ **What changed:**
1. Detected that the string has no leading whitespace (left-aligned)
2. Wrapped it with `dedent()` for consistency
3. Added the import statement automatically
4. Reformatted with proper indentation matching the code structure

**Why use dedent here?** Even though this string doesn't need dedenting now, using `dedent()` consistently makes it easier to modify the string later. You can add indentation for readability without affecting the runtime output.

### Example 3: HTML template formatting

**Before:**

```python
from textwrap import dedent

def render_html():
    return dedent("""
    <div class="container">
        <h1>Welcome</h1>
            <p>This is a paragraph.</p>
    </div>
    """)
```

**After:**

<!-- test: output -->
```python
from textwrap import dedent

def render_html():
    return dedent("""
        <div class="container">
            <h1>Welcome</h1>
                <p>This is a paragraph.</p>
        </div>
    """)
```


---

<!--[[[cog
import requests,cog

url = "https://raw.githubusercontent.com/15r10nk/sponsors/refs/heads/main/sponsors_readme.md"
response = requests.get(url)
response.raise_for_status()  # Raise an exception for bad status codes
cog.out(response.text)
]]]-->
## Sponsors

I would like to thank my sponsors. Without them, I would not be able to invest so much time in my projects.

### Silver sponsor 🥈

<p align="center">
  <a href="https://pydantic.dev/logfire">
    <img src="https://pydantic.dev/assets/for-external/pydantic_logfire_logo_endorsed_lithium_rgb.svg" alt="logfire" width="300"/>
  </a>
</p>
<!--[[[end]]]-->

---

## 🧠 How It Works

1. **Parse** — Uses Python's AST module to analyze source code
2. **Find** — Locates all `dedent()` or `textwrap.dedent()` calls with string arguments
3. **Analyze** — Determines the appropriate indentation level based on context
4. **Validate** — Ensures `dedent(original) == dedent(formatted)` (behavior unchanged)
5. **Replace** — Updates the source file with formatted strings

**The key insight:** Strings are formatted in the source to visually match their runtime output after `dedent()` processes them. This makes the code more readable without changing behavior.

---

## 🛡️ Safety & Compatibility

- **Non-destructive** — Always validates that `dedent(original) == dedent(formatted)`
- **Preserves behavior** — Formatted strings have identical runtime output
- **Quote style aware** — Maintains your choice of `"""` vs `'''`
- **Escape handling** — Correctly handles backslashes and escape sequences
- **Python 3.8+** — Works with modern Python versions

**What gets formatted:**
- ✅ Literal strings inside `textwrap.dedent()` calls
- ✅ Literal strings inside `dedent()` calls (when imported)

**What doesn't get formatted:**
- ❌ Regular strings (not in dedent calls)
- ❌ F-strings (can't be wrapped with dedent)
- ❌ String concatenations
- ❌ Docstrings at module level
- ❌ All other code (completely untouched)

---

## 🧪 Development

### Setup

```bash
# Clone the repository
git clone https://github.com/15r10nk/format-dedent.git
cd format-dedent

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_formatter.py
```

Tests use [inline-snapshot](https://15r10nk.github.io/inline-snapshot/) for snapshot testing.

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
