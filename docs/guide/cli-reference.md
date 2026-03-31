# CLI Reference

## Global Options

```
glossa [OPTIONS] COMMAND [ARGS]
```

| Option | Description |
| ------ | ----------- |
| `--version`, `-v` | Display the version and exit. |
| `--help` | Display the help message and exit. |
| `--config PATH` | Read configuration from an explicit file. |

## Commands

### `glossa lint <paths>...`

Lint Python files and report diagnostics.

```sh
glossa lint src/
glossa lint src/ tests/ --select D1xx,D4xx
glossa lint src/ --ignore D205 --format json
```

| Option | Description | Default |
| ------ | ----------- | ------- |
| `--select CODES` | Enable only the specified rules (codes or groups like `D1xx`). | All |
| `--ignore CODES` | Disable the specified rules. | None |
| `--format text\|json` | Output format. | `text` |
| `--config PATH` | Path to configuration file. | Auto-detected |

### `glossa fix <paths>...`

Apply validated automatic fixes in place.

```sh
glossa fix src/
glossa fix src/ --diff
glossa fix src/ --select D4xx
```

| Option | Description | Default |
| ------ | ----------- | ------- |
| `--select CODES` | Apply only fixes from the specified rules. | All fixable |
| `--diff` | Print a unified diff instead of modifying files. | Off |
| `--check` | Exit non-zero if fixes are available (dry-run for CI). | Off |

### `glossa check <paths>...`

Run `lint` in CI mode. The command exits with a non-zero code when diagnostics or
pending fixes exist.

```sh
glossa check src/
```

### `glossa info`

Display version and platform diagnostics.

```sh
glossa info
```

## Exit Codes

| Exit Code | Meaning |
| --------- | ------- |
| `0` | Successful run with no diagnostics or pending fixes. |
| `1` | Successful run with diagnostics or available fixes. |
| `2` | Usage or configuration error. |
| `3` | Fatal operational error. |
| `4` | Partial failure: some files processed, some failed. |
