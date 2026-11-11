# CLI Reference

## Global Options

```sh
glossa [OPTIONS] COMMAND [ARGS]
```

| Option | Description |
| ------ | ----------- |
| `--version`, `-v` | Display the version and exit. |
| `--help` | Display the help message and exit. |

## Root and Configuration File

The commands `lint` and `fix` resolve the root of the project in this order, and stop at the
first answer:

1. the option `--root`;
2. the environment variable `GLOSSA_ROOT`;
3. the nearest ancestor of the current folder that holds a configuration file, in `config/tools/` or
   at its own level;
4. the current folder.

Without `--config`, the configuration file is read from `config/tools/glossa.yml` or `glossa.yml`
below the root, or from the same names with the extension `.toml`. When several of these files
exist, the command stops with an error that names them. Without any configuration file, the built-in
defaults apply. A file named by `--config` and absent is an error.

The paths given on the command line are read from the current folder. The paths written in the
configuration file, such as the globs of `rules.per_file_ignores`, are read from the root. Without a
path argument, the command analyzes `src` below the root.

## Commands

### `glossa lint <paths>...`

Lint Python files and report diagnostics.

```sh
glossa lint src/
glossa lint src/ tests/ --select presence,typed-entries
glossa lint src/ --ignore markdown-in-docstring --format json
glossa lint src/ --no-color
```

| Option | Description | Default |
| ------ | ----------- | ------- |
| `--root`, `-r` PATH | Root of the project. | Resolved as stated above |
| `--config`, `-c` PATH | Configuration file. | `config/tools/glossa.yml` or `glossa.yml` below the root |
| `--select RULES` | Rule names or groups to enable. | All |
| `--ignore RULES` | Rule names or groups to disable. | None |
| `--format` `text\|json` | Output format. | `text` |
| `--no-color` | Disable colored output. | Off |

### `glossa fix <paths>...`

Apply validated automatic fixes in place. The fixes rewrite source files, so the command asks for a
confirmation on a terminal. `--yes` answers it; without a terminal and without `--yes`, the
command stops with status 2.

```sh
glossa fix src/
glossa fix src/ --yes
glossa fix src/ --dry-run
glossa fix src/ --check
glossa fix src/ -c custom.yml
```

| Option | Description | Default |
| ------ | ----------- | ------- |
| `--root`, `-r` PATH | Root of the project. | Resolved as stated above |
| `--config`, `-c` PATH | Configuration file. | `config/tools/glossa.yml` or `glossa.yml` below the root |
| `--dry-run` | List the fixable issues without changing any file, and exit 0. | Off |
| `--check` | List the fixable issues without changing any file, and exit 1 when one exists. | Off |
| `--yes` | Apply the fixes without asking for a confirmation. | Off |

### `glossa info`

Display version and platform diagnostics.

```sh
glossa info
```

## Exit Codes

| Exit Code | Meaning |
| --------- | ------- |
| `0` | No diagnostics, no available fix with `--check`, or every fix applied. |
| `1` | Diagnostics found by `lint`, available fixes found by `fix --check`, or fixes skipped by `fix`. |
| `2` | Usage or configuration error, a missing path, or a file that cannot be analyzed. |
