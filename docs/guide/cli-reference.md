# CLI Reference

## Global Options

```sh
glossa [OPTIONS] COMMAND [ARGS]
```

| Option | Description |
| ------ | ----------- |
| `--version`, `-v` | Display the version and exit. |
| `--help` | Display the help message and exit. |

## Commands

### `glossa lint <paths>...`

Lint Python files and report diagnostics.

```sh
glossa lint src/
glossa lint src/ tests/ --select D1xx,D4xx
glossa lint src/ --ignore D205 --format json
glossa lint src/ --no-color
```

| Option | Description | Default |
| ------ | ----------- | ------- |
| `--config`, `-c` PATH | Path to configuration file. | Auto-detected |
| `--select CODES` | Enable only the specified rules (codes or groups like `D1xx`). | All |
| `--ignore CODES` | Disable the specified rules. | None |
| `--format`, `-f` `text\|json` | Output format. | `text` |
| `--no-color` | Disable colored output. | Off |

### `glossa fix <paths>...`

Apply validated automatic fixes in place.

```sh
glossa fix src/
glossa fix src/ --dry-run
glossa fix src/ -c custom.toml
```

| Option | Description | Default |
| ------ | ----------- | ------- |
| `--config`, `-c` PATH | Path to configuration file. | Auto-detected |
| `--dry-run` | List fixable issues without modifying files. | Off |

### `glossa check <paths>...`

Run `lint` in CI mode. The command exits with a non-zero code when fixable
issues exist.

```sh
glossa check src/
glossa check src/ -c custom.toml
```

| Option | Description | Default |
| ------ | ----------- | ------- |
| `--config`, `-c` PATH | Path to configuration file. | Auto-detected |

### `glossa info`

Display version and platform diagnostics.

```sh
glossa info
```

## Exit Codes

| Exit Code | Meaning |
| --------- | ------- |
| `0` | No diagnostics or pending fixes. |
| `1` | Diagnostics or available fixes detected. |
| `2` | Usage or configuration error. |
| `4` | Partial failure: some files processed, some failed. |
