# Usage

Glossa operates through a Typer-based CLI and an equivalent Python API. The three
core commands — `lint`, `fix`, and `check` — cover the standard workflow from
diagnostic reporting to automatic correction.

For the exhaustive list of commands and options, refer to
[CLI Reference](cli-reference.md). For rule selection and fix policies, refer to
[Configuration](configuration.md).

## Linting

The `lint` command analyzes Python source files and reports docstring violations:

```sh
glossa lint src/
glossa lint src/ tests/
```

Restrict the analysis to specific rule groups or exclude individual rules:

```sh
glossa lint src/ --select D1xx,D4xx
glossa lint src/ --ignore D200
```

JSON output is available for machine consumption and CI integration:

```sh
glossa lint src/ --format json
```

## Fixing

The `fix` command applies validated corrections in place:

```sh
glossa fix src/
```

Preview the changes as a unified diff without modifying files:

```sh
glossa fix src/ --diff
```

Restrict fixes to a specific rule group (e.g., type-sync rules only):

```sh
glossa fix src/ --select D4xx
```

## CI Integration

The `check` command behaves like `lint` but exits with a non-zero code when
violations exist. A typical pre-commit or CI step:

```sh
glossa check src/
```

## Python API

The same functionality is accessible programmatically:

```python
from pathlib import Path
from glossa.adapters.bootstrap import create_linter

linter = create_linter()
diagnostics = linter.lint(Path("src/"))

for d in diagnostics:
    print(f"{d.target.source_id} {d.code} {d.message}")
```

## Next Steps

- [CLI Reference](cli-reference.md) — Full command registry and options.
- [Configuration](configuration.md) — Rule selection, fix policies, inline suppressions.
- [Docstring Guide](docstring-guide.md) — The numpydoc conventions enforced by glossa.
