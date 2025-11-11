# format-dedent

**Format multiline strings with proper indentation** — A Python code formatter that formats **only** the literal string arguments of `textwrap.dedent()` calls.

## ✨ What does it do?

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
pip install format-dedent
```

---

## 🚀 Quick Start

### Format strings (default mode)

Preview formatted output without modifying files:
```bash
python -m format_dedent yourfile.py
```

Write changes to files:
```bash
python -m format_dedent yourfile.py --write
```

Format multiple files or directories:
```bash
python -m format_dedent src/ tests/ --write
```

### Add dedent() calls (--add-dedent mode)

Automatically wrap multiline strings with `dedent()` calls:
```bash
python -m format_dedent yourfile.py --add-dedent --write
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

**Examples:**

```bash
# Preview formatted code (output to stdout, no changes)
python -m format_dedent myfile.py

# Write changes to the file
python -m format_dedent myfile.py --write

# Format entire project
python -m format_dedent src/ tests/ --write

# Add dedent() to all multiline strings
python -m format_dedent myfile.py --add-dedent --write

# Read from stdin, write to stdout (pipe-friendly)
cat myfile.py | python -m format_dedent > formatted.py
```

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

Then install the hook:
```bash
pre-commit install
```

Run manually on all files:
```bash
pre-commit run format-dedent --all-files
```

---

## 💡 Examples

### Example 1: Formatting SQL queries

**Before formatting:**

<!-- test: format-input -->
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

<!-- test: format-output -->
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

✅ **What changed:**
- Inconsistent indentation is normalized
- Each line's indentation now reflects the SQL structure
- Trailing whitespace removed
- The formatted version shows what `dedent()` will produce at runtime

**The key insight:** The indentation you see in the source code now matches what `dedent()` returns. When this code runs, `dedent()` strips the common leading whitespace, and you get properly formatted SQL.

### Example 2: Using --add-dedent mode

**Before:**

<!-- test: add-dedent-input -->
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

<!-- test: format-input -->
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

<!-- test: format-output -->
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

### Example 4: JSON template

**Before:**

<!-- test: format-input -->
```python
import textwrap

CONFIG = textwrap.dedent('''
{
  "name": "my-app",
      "version": "1.0.0"
}
''')
```

**After:**

<!-- test: format-output -->
```python
import textwrap

CONFIG = textwrap.dedent('''
    {
      "name": "my-app",
          "version": "1.0.0"
    }
''')
```

### Example 5: Error message with inconsistent indentation

**Before:**

<!-- test: format-input -->
```python
from textwrap import dedent

def validate_user(user):
    if not user.email:
        raise ValueError(dedent("""
            Invalid user configuration:
                - Email is required
            - Must be a valid email address
                - Example: user@example.com
        """))
```

**After:**

<!-- test: format-output -->
```python
from textwrap import dedent

def validate_user(user):
    if not user.email:
        raise ValueError(dedent("""
            Invalid user configuration:
                - Email is required
            - Must be a valid email address
                - Example: user@example.com
        """))
```

✅ **What changed:**
- Mixed indentation levels are now consistent
- Each line's indentation shows the message structure
- The formatted version visually matches what users will see at runtime

---

## 🧠 How It Works

1. **Parse** — Uses Python's AST module to analyze source code
2. **Find** — Locates all `dedent()` or `textwrap.dedent()` calls with string arguments
3. **Analyze** — Determines the appropriate indentation level based on context
4. **Format** — Removes trailing whitespace and applies consistent indentation
5. **Validate** — Ensures `dedent(original) == dedent(formatted)` (behavior unchanged)
6. **Replace** — Updates the source file with formatted strings

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

### Test Suite

The project includes **51 comprehensive tests** covering:
- ✅ Module, function, and class level dedent formatting
- ✅ Nested blocks (if, for, try/except)
- ✅ Quote style preservation (`"""` and `'''`)
- ✅ Backslash line continuations
- ✅ Real-world examples (SQL, HTML, JSON templates)
- ✅ Edge cases and error handling
- ✅ CLI integration tests

Tests use [inline-snapshot](https://15r10nk.github.io/inline-snapshot/) for snapshot testing.

### Project Structure

```
format-dedent/
├── src/format_dedent/
│   ├── __init__.py          # Package exports
│   ├── __main__.py          # Entry point
│   ├── cli.py               # CLI interface
│   ├── formatter.py         # String formatting logic
│   ├── add_dedent.py        # Add dedent() calls
│   └── ast_helpers.py       # AST analysis utilities
└── tests/
    ├── test_formatter.py    # Formatting tests
    └── test_cli.py          # CLI integration tests
```

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## ⭐ Related Projects

- [Black](https://github.com/psf/black) — The uncompromising Python code formatter
- [inline-snapshot](https://github.com/15r10nk/inline-snapshot) — Snapshot testing for Python
