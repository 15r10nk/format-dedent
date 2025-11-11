"""format-dedent: Format multiline strings with proper indentation."""

__version__ = "0.1.1"

from .formatter import format_dedent_strings, format_string_content, check_format
from .add_dedent import add_dedent
from .cli import main, format_file

__all__ = [
    "format_dedent_strings",
    "format_string_content",
    "check_format",
    "add_dedent",
    "main",
    "format_file",
]
