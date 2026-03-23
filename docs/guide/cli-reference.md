# CLI Reference

This guide documents the target CLI surface defined in the
[Design Plan](../design-plan.md). The current codebase may implement it incrementally.

## Global Options

```
glossa [OPTIONS] COMMAND [ARGS]
```

| Option | Description |
| ------ | ----------- |
| `--version`, `-v` | Display version and exit. |
| `--help` | Display help and exit. |
| `--config PATH` | Read configuration from an explicit file. |

## Commands

### `glossa lint <paths>...`

Lint Python files and report diagnostics.

```sh
glossa lint src/
glossa lint src/ tests/ --select D1xx,D4xx
glossa lint src/ --ignore D205 --format json
```

### `glossa fix <paths>...`

Apply validated automatic fixes.

```sh
glossa fix src/
glossa fix src/ --diff
glossa fix src/ --select D4xx
```

### `glossa check <paths>...`

Run lint in CI mode. Exit non-zero when diagnostics or pending fixes exist.

```sh
glossa check src/
```

## Exit Codes

| Exit Code | Meaning |
| --------- | ------- |
| `0` | Successful run with no diagnostics / no pending fixes |
| `1` | Successful run with diagnostics / available fixes |
| `2` | Usage or configuration error |
| `3` | Fatal operational error |
| `4` | Partial failure: some files processed, some failed |
