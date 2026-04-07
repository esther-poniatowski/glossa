# Usage

Glossa operates through a Typer-based CLI and an equivalent Python API. The three
core commands -- `lint`, `fix`, and `check` -- cover the standard workflow from
diagnostic reporting to automatic correction.

See [CLI Reference](cli-reference.md) for all commands and options.
See [Configuration](configuration.md) for rule selection and fix policies.

## Lint

The `lint` command analyzes Python source files and reports docstring violations:

```sh
glossa lint src/
glossa lint src/ tests/
```

Restrict the analysis to specific rule groups or exclude individual rules:

```sh
glossa lint src/ --select presence,typed-entries
glossa lint src/ --ignore non-imperative-summary
```

JSON output supports machine consumption and CI integration:

```sh
glossa lint src/ --format json
```

## Fix

The `fix` command applies validated corrections in place:

```sh
glossa fix src/
```

Preview fixable issues without modifying files:

```sh
glossa fix src/ --dry-run
```

## CI Integration

The `check` command behaves like `lint` but exits with a non-zero code when
fixable issues exist. A typical pre-commit or CI step:

```sh
glossa check src/
```

## Python API

The same functionality works programmatically through `bootstrap`:

```python
from glossa.adapters.bootstrap import bootstrap

service = bootstrap()
result = service.lint_paths(["src/"])

for d in result.diagnostics:
    print(f"{d.target.source_id} {d.rule} {d.message}")
```

Single-string input bypasses file discovery:

```python
diagnostics = service.lint_source('def foo():\n    """does stuff"""\n')
```

## Next Steps

- [CLI Reference](cli-reference.md) -- Full command registry and options.
- [Configuration](configuration.md) -- Rule selection, fix policies, inline suppressions.
- [Docstring Guide](docstring-guide.md) -- The numpydoc conventions enforced by glossa.
