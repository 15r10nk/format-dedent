"""CLI integration tests for format-dedent."""

from textwrap import dedent

import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
import sys
from inline_snapshot import snapshot

# Common test strings used across multiple tests
SOURCE = dedent(
    '''    from textwrap import dedent

    message = dedent("""
    line1
    line2
    """)
    '''
)

EXPECTED = snapshot(
    dedent(
        '''        from textwrap import dedent

        message = dedent("""
            line1
            line2
        """)
        '''
    )
)

SYNTAX_ERROR_SOURCE = dedent(
    """    from textwrap import dedent

    # This has a syntax error
    def broken(:
        pass
    """
)


def run_cli(
    args_list: List[str],
    files_dict: Optional[Dict[str, str]] = None,
    expected_stdout: Optional[str] = None,
    expected_stderr: Optional[str] = None,
    changed_files_dict: Optional[Dict[str, str]] = None,
    stdin_input: Optional[str] = None,
    return_code: int = 0,
) -> None:
    """
    Run the format-dedent CLI in a subprocess within a temporary directory.

    Args:
        args_list: Command line arguments (not including the script name)
        files_dict: Dictionary of {filename: content} to create before running
        expected_stdout: Expected stdout content (if None, not checked)
        expected_stderr: Expected stderr content (if None, not checked)
        changed_files_dict: Dictionary of {filename: expected_content} after running
        stdin_input: Input to provide via stdin (if None, no stdin input)
        return_code: Expected return code (default: 0)

    Raises:
        AssertionError: If outputs don't match expectations
    """
    files_dict = files_dict or {}
    changed_files_dict = changed_files_dict or {}

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create input files
        for filename, content in files_dict.items():
            file_path = tmp_path / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)

        # Find the format-dedent script
        # Assuming we're running from the tests directory
        main_module = (
            Path(__file__).parent.parent / "src" / "format_dedent" / "__main__.py"
        )

        # Run the CLI
        cmd = [sys.executable, str(main_module)] + args_list
        result = subprocess.run(
            cmd,
            cwd=tmp_path,
            capture_output=True,
            text=True,
            input=stdin_input,
        )

        # Check return code
        assert result.returncode == return_code, (
            f"Return code mismatch:\n"
            f"Expected: {return_code}\n"
            f"Got: {result.returncode}\n"
            f"Stderr: {result.stderr}"
        )

        # Check stdout
        if expected_stdout is not None:
            assert result.stdout == expected_stdout, (
                f"Stdout mismatch:\n"
                f"Expected:\n{expected_stdout}\n"
                f"Got:\n{result.stdout}"
            )

        # Check stderr
        if expected_stderr is not None:
            assert result.stderr == expected_stderr, (
                f"Stderr mismatch:\n"
                f"Expected:\n{expected_stderr}\n"
                f"Got:\n{result.stderr}"
            )

        # Check changed files
        for filename, expected_content in changed_files_dict.items():
            file_path = tmp_path / filename
            assert file_path.exists(), f"File {filename} was not created"
            actual_content = file_path.read_text()
            assert actual_content == expected_content, (
                f"File {filename} content mismatch:\n"
                f"Expected:\n{expected_content}\n"
                f"Got:\n{actual_content}"
            )


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_single_file(self):
        """Test formatting a single file."""
        run_cli(
            args_list=["test.py"],
            files_dict={"test.py": SOURCE},
            expected_stdout=EXPECTED,
        )

    def test_single_file_in_place(self):
        """Test formatting a single file in-place."""
        run_cli(
            args_list=["--write", "test.py"],
            files_dict={"test.py": SOURCE},
            changed_files_dict={"test.py": EXPECTED},
        )

    def test_multiple_files(self):
        """Test formatting multiple files."""
        run_cli(
            args_list=["file1.py", "file2.py"],
            files_dict={"file1.py": SOURCE, "file2.py": SOURCE},
            expected_stdout=snapshot(
                dedent(
                    '''\
                    === file1.py ===
                    from textwrap import dedent

                    message = dedent("""
                        line1
                        line2
                    """)

                    === file2.py ===
                    from textwrap import dedent

                    message = dedent("""
                        line1
                        line2
                    """)

                    '''
                )
            ),
        )

    def test_directory(self):
        """Test formatting all Python files in a directory."""
        run_cli(
            args_list=["--write", "src"],
            files_dict={
                "src/test1.py": SOURCE,
                "src/test2.py": SOURCE,
            },
            changed_files_dict={
                "src/test1.py": EXPECTED,
                "src/test2.py": EXPECTED,
            },
        )

    def test_stdin_stdout(self):
        """Test reading from stdin and writing to stdout."""
        run_cli(
            args_list=[],
            stdin_input=SOURCE,
            expected_stdout=EXPECTED,
        )


class TestCLIErrors:
    """Test error handling in CLI."""

    def test_nonexistent_file(self):
        """Test error when file doesn't exist."""

        run_cli(
            args_list=["nonexistent.py"],
            files_dict={},
            expected_stderr=snapshot("Error: Path nonexistent.py does not exist\n"),
            return_code=1,
        )

    def test_non_python_file_warning(self):
        """Test warning for non-Python files."""

        run_cli(
            args_list=["test.txt"],
            files_dict={},
            expected_stderr=snapshot("Error: Path test.txt does not exist\n"),
            return_code=1,
        )

    def test_syntax_error_in_file(self):
        """Test handling of files with syntax errors via stdin."""

        run_cli(
            args_list=[],
            stdin_input=SYNTAX_ERROR_SOURCE,
            expected_stderr=snapshot(
                "Error parsing <stdin>: invalid syntax (<stdin>, line 4)\n"
            ),
            return_code=1,
        )


class TestCLIReturnCodes:
    """Test return codes for various scenarios."""

    def test_successful_format_returns_zero(self):
        """Test that successful formatting returns exit code 0."""
        run_cli(
            args_list=["--write", "test.py"],
            files_dict={"test.py": SOURCE},
            return_code=0,
        )

    def test_stdin_mode_returns_zero(self):
        """Test that stdin mode returns exit code 0 on success."""
        run_cli(
            args_list=[],
            stdin_input=SOURCE,
            return_code=0,
        )


class TestAddDedentCLI:
    """Test the --add-dedent CLI flag."""

    def test_add_dedent_stdin(self):
        """Test --add-dedent with stdin input."""
        input_source = dedent(
            '''            x = """
            hello
            world
            """
            '''
        )
        run_cli(
            args_list=["--add-dedent"],
            stdin_input=input_source,
            expected_stdout=snapshot(
                '''\
x = """
hello
world
"""
'''
            ),
        )

    def test_add_dedent_file(self):
        """Test --add-dedent with a file."""
        input_source = dedent(
            '''            x = """
            hello
            world
            """

            y = """
                indented
                content
            """
            '''
        )
        expected_output = snapshot(
            '''\
x = """
hello
world
"""

y = """
    indented
    content
"""
'''
        )

        run_cli(
            args_list=["--add-dedent", "test.py"],
            files_dict={"test.py": input_source},
            expected_stdout=expected_output,
        )

    def test_add_dedent_in_place(self):
        """Test --add-dedent with --write."""
        input_source = dedent(
            '''            def func():
                text = """
            line1
            line2
            """
                return text
            '''
        )
        expected_output = snapshot(
            dedent(
                '''\
                from textwrap import dedent
                def func():
                    text = dedent("""
                        line1
                        line2
                    """)
                    return text
                '''
            )
        )

        run_cli(
            args_list=["--add-dedent", "--write", "test.py"],
            files_dict={"test.py": input_source},
            changed_files_dict={"test.py": expected_output},
        )

    def test_add_dedent_preserves_existing_dedent(self):
        """Test that --add-dedent doesn't double-wrap existing dedent calls."""
        input_source = dedent(
            '''            from textwrap import dedent

            x = dedent("""
            already wrapped
            """)

            y = """
            new string
            """
            '''
        )
        expected_output = snapshot(
            '''\
from textwrap import dedent

x = dedent("""
    already wrapped
""")

y = """
new string
"""
'''
        )

        run_cli(
            args_list=["--add-dedent", "test.py"],
            files_dict={"test.py": input_source},
            expected_stdout=expected_output,
        )

    def test_add_dedent_multiple_files(self):
        """Test --add-dedent with multiple files."""
        input_source1 = dedent(
            '''            x = """
            hello
            """
            '''
        )
        input_source2 = dedent(
            '''            y = """
            world
            """
            '''
        )

        run_cli(
            args_list=["--add-dedent", "file1.py", "file2.py"],
            files_dict={"file1.py": input_source1, "file2.py": input_source2},
            expected_stdout=snapshot(
                '''\
=== file1.py ===
x = """
hello
"""

=== file2.py ===
y = """
world
"""

'''
            ),
        )

    def test_add_dedent_with_docstring(self):
        """Test --add-dedent with module docstring."""
        input_source = dedent(
            '''            """Module docstring."""

            x = """
            content
            """
            '''
        )
        expected_output = snapshot(
            '''\
"""Module docstring."""

x = """
content
"""
'''
        )

        run_cli(
            args_list=["--add-dedent", "test.py"],
            files_dict={"test.py": input_source},
            expected_stdout=expected_output,
        )


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
