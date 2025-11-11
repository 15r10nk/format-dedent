"""Example showing the formatter working at different indentation levels."""
import textwrap
from textwrap import dedent


# Module level (0 spaces) -> dedent content at 4 spaces
MODULE_CONSTANT = dedent("""
    Module level string
    will be indented at 4 spaces.
""")


def function_example():
    """Function at 4 spaces -> dedent content at 8 spaces."""
    message = textwrap.dedent("""
        Function level string
        will be indented at 8 spaces.
            This line has extra indent.
    """)
    return message


class Example:
    """Class example."""

    CLASS_VAR = dedent("""
        Class variable (4 spaces)
        will be indented at 8 spaces.
    """)

    def method(self):
        """Method at 8 spaces -> dedent content at 12 spaces."""
        text = dedent("""
            Method level string
            will be indented at 12 spaces.
        """)

        if True:
            # Nested block at 12 spaces -> dedent content at 16 spaces
            nested = dedent("""
                Nested block string
                will be indented at 16 spaces.
            """)

            for i in range(1):
                # Even more nested at 16 spaces -> dedent content at 20 spaces
                deep = dedent("""
                    Deep nested string
                    will be indented at 20 spaces.
                """)
                return deep

        return text


if __name__ == "__main__":
    print("Before formatting, these strings have inconsistent indentation.")
    print("After formatting, they will be properly indented relative to their parent statement.")
