# Pre-commit Hook Setup Summary

This document summarizes the pre-commit hook configuration added to the format-dedent repository.

## Files Added

### 1. `.pre-commit-hooks.yaml` (Required for other repos to use this as a hook)
This file defines the hook that other projects can use. It tells pre-commit how to run format-dedent.

```yaml
- id: format-dedent
  name: Format dedent strings
  description: Format only the literal string arguments of textwrap.dedent() calls
  entry: format-dedent
  language: python
  types: [python]
  args: [--in-place]
```

### 2. `.pre-commit-config.yaml` (For this repository's development)
This file configures pre-commit hooks for developing format-dedent itself.

Features:
- Runs format-dedent on this repository's own Python files
- Includes standard pre-commit hooks (trailing whitespace, YAML checks, etc.)

### 3. `example-pre-commit-config.yaml` (Example for users)
A complete example showing how users would configure their projects to use format-dedent.

### 4. `MANIFEST.in` (Updated)
Ensures the `.pre-commit-hooks.yaml` file is included when the package is distributed.

### 5. `pyproject.toml` (Updated)
Added:
- Pre-commit to dev dependencies
- Package metadata (keywords, classifiers)
- Build system configuration
- Package data configuration

### 6. `README.md` (Updated)
Added comprehensive documentation on:
- How to use format-dedent as a pre-commit hook
- Installation instructions for pre-commit
- Development setup with pre-commit

## How Users Will Use This

### In Other Projects

1. Add to `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/yourusername/format-dedent
    rev: v0.1.0
    hooks:
      - id: format-dedent
```

2. Install and run:
```bash
pre-commit install
pre-commit run --all-files
```

### For Development of This Repo

1. Install with dev dependencies:
```bash
pip install -e ".[dev]"
```

2. Install pre-commit hooks:
```bash
pre-commit install
```

3. Hooks will now run automatically on commit, or manually:
```bash
pre-commit run --all-files
```

## Hook Configuration Details

- **Hook ID**: `format-dedent`
- **Language**: Python
- **File Types**: Python files only (`.py`)
- **Default Args**: `--in-place` (modifies files directly)
- **Entry Point**: Uses the `format-dedent` CLI command

## Benefits

1. **Automatic Formatting**: Dedent strings are automatically formatted before commit
2. **CI/CD Integration**: Can be run in CI pipelines with `pre-commit run --all-files`
3. **Team Consistency**: Ensures all team members format dedent strings consistently
4. **Easy Integration**: Works alongside other pre-commit hooks (Black, isort, flake8, etc.)

## Testing

All 19 tests pass with the new configuration:
```bash
pytest tests/test_formatter.py -v
```

The CLI command still works correctly:
```bash
format-dedent --help
```
