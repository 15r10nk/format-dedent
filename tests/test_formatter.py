"""Integration tests for the format-dedent formatter."""
from pathlib import Path
import pytest
import sys
from inline_snapshot import snapshot

from format_dedent.__main__ import format_dedent_strings


def format_source(code: str) -> str:
    """
    Format the given source code and return the formatted result.

    Args:
        code: Python source code as a string

    Returns:
        The formatted source code
    """
    return format_dedent_strings(code)


class TestModuleLevelDedent:
    """Test dedent() calls at module level (0 spaces indentation)."""

    def test_simple_module_level(self):
        """Module level dedent should indent content by 4 spaces."""
        source = '''from textwrap import dedent

MESSAGE = dedent("""
Hello World
This is a test
""")
'''
        assert format_source(source) == snapshot('''\
from textwrap import dedent

MESSAGE = dedent("""
    Hello World
    This is a test
""")
''')

    def test_module_level_with_relative_indent(self):
        """Module level dedent should preserve relative indentation."""
        source = '''import textwrap

SQL = textwrap.dedent("""
SELECT *
FROM users
WHERE active = true
    AND age > 18
""")
'''
        assert format_source(source) == snapshot('''\
import textwrap

SQL = textwrap.dedent("""
    SELECT *
    FROM users
    WHERE active = true
        AND age > 18
""")
''')


class TestFunctionLevelDedent:
    """Test dedent() calls inside functions (4 spaces indentation)."""

    def test_simple_function_dedent(self):
        """Function level dedent should indent content by 8 spaces."""
        source = '''from textwrap import dedent

def get_message():
    text = dedent("""
    Hello from function
    Multiple lines
    """)
    return text
'''
        assert format_source(source) == snapshot('''\
from textwrap import dedent

def get_message():
    text = dedent("""
        Hello from function
        Multiple lines
    """)
    return text
''')

    def test_function_with_complex_content(self):
        """Function dedent with complex multi-line content."""
        source = '''import textwrap

def generate_html():
    return textwrap.dedent("""
    <html>
        <body>
            <h1>Title</h1>
            <p>Paragraph</p>
        </body>
    </html>
    """)
'''
        assert format_source(source) == snapshot('''\
import textwrap

def generate_html():
    return textwrap.dedent("""
        <html>
            <body>
                <h1>Title</h1>
                <p>Paragraph</p>
            </body>
        </html>
    """)
''')


class TestClassLevelDedent:
    """Test dedent() calls inside classes."""

    def test_class_attribute_dedent(self):
        """Class attribute dedent should indent by 8 spaces."""
        source = '''from textwrap import dedent

class Example:
    TEMPLATE = dedent("""
    Class level string
    Multiple lines
    """)
'''
        assert format_source(source) == snapshot('''\
from textwrap import dedent

class Example:
    TEMPLATE = dedent("""
        Class level string
        Multiple lines
    """)
''')

    def test_method_dedent(self):
        """Method dedent should indent by 12 spaces."""
        source = '''from textwrap import dedent

class Database:
    def get_query(self):
        query = dedent("""
        SELECT id, name, email
        FROM users
        WHERE status = 'active'
        ORDER BY created_at DESC
        """)
        return query
'''
        assert format_source(source) == snapshot('''\
from textwrap import dedent

class Database:
    def get_query(self):
        query = dedent("""
            SELECT id, name, email
            FROM users
            WHERE status = 'active'
            ORDER BY created_at DESC
        """)
        return query
''')


class TestNestedBlockDedent:
    """Test dedent() calls inside nested blocks."""

    def test_if_block_dedent(self):
        """Dedent inside if block should have correct indentation."""
        source = '''from textwrap import dedent

def process():
    if True:
        msg = dedent("""
        Nested in if block
        Second line
        """)
        return msg
'''
        assert format_source(source) == snapshot('''\
from textwrap import dedent

def process():
    if True:
        msg = dedent("""
            Nested in if block
            Second line
        """)
        return msg
''')

    def test_deeply_nested_dedent(self):
        """Dedent in deeply nested structure."""
        source = '''from textwrap import dedent

def outer():
    for i in range(10):
        if i % 2 == 0:
            text = dedent("""
            Deep nesting level
            Multiple lines here
            """)
            print(text)
'''
        assert format_source(source) == snapshot('''\
from textwrap import dedent

def outer():
    for i in range(10):
        if i % 2 == 0:
            text = dedent("""
                Deep nesting level
                Multiple lines here
            """)
            print(text)
''')

    def test_try_except_dedent(self):
        """Dedent inside try/except blocks."""
        source = '''import textwrap

def handle_error():
    try:
        pass
    except Exception:
        error_msg = textwrap.dedent("""
        An error occurred
        Please try again
        """)
        return error_msg
'''
        assert format_source(source) == snapshot('''\
import textwrap

def handle_error():
    try:
        pass
    except Exception:
        error_msg = textwrap.dedent("""
            An error occurred
            Please try again
        """)
        return error_msg
''')


class TestQuoteStylePreservation:
    """Test that different quote styles are preserved."""

    def test_triple_double_quotes(self):
        """Triple double quotes should be preserved."""
        source = '''from textwrap import dedent

text = dedent("""
Content here
""")
'''
        assert format_source(source) == snapshot('''\
from textwrap import dedent

text = dedent("""
    Content here
""")
''')

    def test_triple_single_quotes(self):
        """Triple single quotes should be preserved."""
        source = """from textwrap import dedent

text = dedent('''
Content here
''')
"""
        assert format_source(source) == snapshot("""\
from textwrap import dedent

text = dedent('''
    Content here
''')
""")


class TestNonDedentStringsIgnored:
    """Test that strings not in dedent() are left unchanged."""

    def test_regular_string_unchanged(self):
        """Regular strings should not be modified."""
        source = '''regular = """
    Original indentation
    With trailing spaces
"""
'''
        assert format_source(source) == snapshot('''\
regular = """
    Original indentation
    With trailing spaces
"""
''')

    def test_mixed_dedent_and_regular(self):
        """Only dedent strings should be formatted."""
        source = '''from textwrap import dedent

formatted = dedent("""
This will be formatted
""")

unformatted = """
    This stays the same
"""
'''
        assert format_source(source) == snapshot('''\
from textwrap import dedent

formatted = dedent("""
    This will be formatted
""")

unformatted = """
    This stays the same
"""
''')


class TestTrailingWhitespaceRemoval:
    """Test that trailing whitespace is removed from dedent strings."""

    def test_removes_trailing_spaces(self):
        """Trailing spaces should be removed."""
        source = '''from textwrap import dedent

text = dedent("""
Line with spaces
Another line with tabs\t\t
""")
'''
        assert format_source(source) == snapshot('''\
from textwrap import dedent

text = dedent("""
    Line with spaces
    Another line with tabs
""")
''')


class TestEmptyLinesPreserved:
    """Test that empty lines within content are preserved."""

    def test_preserves_empty_lines(self):
        """Empty lines in the middle should be kept."""
        source = '''from textwrap import dedent

text = dedent("""
First paragraph

Second paragraph

Third paragraph
""")
'''
        assert format_source(source) == snapshot('''\
from textwrap import dedent

text = dedent("""
    First paragraph

    Second paragraph

    Third paragraph
""")
''')


class TestRealWorldExamples:
    """Real-world usage examples."""

    def test_sql_query_formatting(self):
        """SQL query in a method."""
        source = '''import textwrap

class UserRepository:
    def get_active_users(self):
        return textwrap.dedent("""
        SELECT
            u.id,
            u.username,
            u.email,
            COUNT(p.id) as post_count
        FROM users u
        LEFT JOIN posts p ON u.id = p.user_id
        WHERE u.active = true
        GROUP BY u.id
        ORDER BY post_count DESC
        LIMIT 100
        """)
'''
        assert format_source(source) == snapshot('''\
import textwrap

class UserRepository:
    def get_active_users(self):
        return textwrap.dedent("""
            SELECT
                u.id,
                u.username,
                u.email,
                COUNT(p.id) as post_count
            FROM users u
            LEFT JOIN posts p ON u.id = p.user_id
            WHERE u.active = true
            GROUP BY u.id
            ORDER BY post_count DESC
            LIMIT 100
        """)
''')

    def test_html_template_formatting(self):
        """HTML template formatting."""
        source = '''from textwrap import dedent

def render_email(name):
    html = dedent("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Welcome</title>
    </head>
    <body>
        <h1>Hello, {name}!</h1>
        <p>Welcome to our service.</p>
    </body>
    </html>
    """)
    return html.format(name=name)
'''
        assert format_source(source) == snapshot('''\
from textwrap import dedent

def render_email(name):
    html = dedent("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Welcome</title>
        </head>
        <body>
            <h1>Hello, {name}!</h1>
            <p>Welcome to our service.</p>
        </body>
        </html>
    """)
    return html.format(name=name)
''')

    def test_json_template_formatting(self):
        """JSON template with proper indentation."""
        source = '''import textwrap

CONFIG = textwrap.dedent("""
{
    "database": {
        "host": "localhost",
        "port": 5432
    },
    "logging": {
        "level": "INFO",
        "file": "/var/log/app.log"
    }
}
""")
'''
        assert format_source(source) == snapshot('''\
import textwrap

CONFIG = textwrap.dedent("""
    {
        "database": {
            "host": "localhost",
            "port": 5432
        },
        "logging": {
            "level": "INFO",
            "file": "/var/log/app.log"
        }
    }
""")
''')

    def test_dedent_in_list(self):
        """JSON template with proper indentation."""
        source = '''\
import textwrap

l = [
    1,
    textwrap.dedent(
        """
SELECT *

FROM users    \n\
WHERE active = true
    AND age > 18
"""
    ),
    2,
    3,
]
'''
        assert format_source(source) == snapshot('''\
import textwrap

l = [
    1,
    textwrap.dedent(
        """
        SELECT *

        FROM users
        WHERE active = true
            AND age > 18
        """
    ),
    2,
    3,
]
''')


class TestBackslashContinuation:
    """Test strings with backslash after opening quotes."""

    def test_backslash_after_opening_quotes(self):
        """Test dedent with backslash continuation (no leading newline)."""
        source = '''\
from textwrap import dedent

message = dedent("""\\
line1
line2
line3
""")
'''
        assert format_source(source) == snapshot('''\
from textwrap import dedent

message = dedent("""\\
    line1
    line2
    line3
""")
''')

    def test_backslash_in_function(self):
        """Test backslash continuation in function context."""
        source = '''\
import textwrap

def get_text():
    return textwrap.dedent("""\\
    First line
    Second line
        Indented line
    """)
'''
        assert format_source(source) == snapshot('''\
import textwrap

def get_text():
    return textwrap.dedent("""\\
        First line
        Second line
            Indented line
    """)
''')

    def test_backslash_with_triple_single_quotes(self):
        """Test backslash continuation with single quotes."""
        source = """\
from textwrap import dedent

text = dedent('''\\
No leading newline
Second line
''')
"""
        assert format_source(source) == snapshot("""\
from textwrap import dedent

text = dedent('''\\
    No leading newline
    Second line
''')
""")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
