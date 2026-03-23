# glossa

[![Conda](https://img.shields.io/badge/conda-eresthanaconda--channel-blue)](#installation)
[![Maintenance](https://img.shields.io/maintenance/yes/2026)]()
[![Last Commit](https://img.shields.io/github/last-commit/esther-poniatowski/glossa)](https://github.com/esther-poniatowski/glossa/commits/main)
[![Python](https://img.shields.io/badge/python-%E2%89%A53.12-blue)](https://www.python.org/)
[![License: GPL](https://img.shields.io/badge/License-GPL--3.0-yellow.svg)](https://opensource.org/licenses/GPL-3.0)

A Python docstring linter and auto-fixer for NumPy-style docstrings.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Architecture](#architecture)
- [Support](#support)
- [Contributing](#contributing)
- [Acknowledgments](#acknowledgments)
- [License](#license)

## Overview

Glossa statically analyzes Python source files to enforce docstring conventions based
on the [numpydoc](https://numpydoc.readthedocs.io/) standard. It reports violations,
suggests fixes, and optionally applies corrections automatically — including generating
docstring types from type annotations.

### Motivation

Consistent docstrings are essential for generated API documentation, IDE tooltips, and
codebase readability. Existing tools (pydocstyle, ruff's docstring rules) check basic
presence and formatting but lack deep NumPy-section validation, parameter/signature
synchronization, and automatic type propagation from annotations to docstrings.
Glossa fills this gap with a rule set designed specifically around numpydoc conventions.

### Advantages

- **NumPy-native rule set**: Validates section headers, parameter entries, return
  documentation, and section ordering against the numpydoc standard.
- **Signature-aware**: Cross-references docstring parameters and types against actual
  function signatures and type annotations.
- **Auto-fix with type sync**: Generates missing sections, propagates types from
  annotations to docstrings, and fixes formatting — all configurable.
- **Extensible rule system**: Each rule is a self-contained unit. New rules can be
  added without modifying existing code.
- **Multiple output formats**: Human-readable (Rich) and JSON for CI integration.

---

## Features

- [x] **Lint**: Report docstring violations against numpydoc conventions.
- [x] **Auto-fix**: Apply automatic corrections (missing periods, section underlines,
  blank lines, redundant sections).
- [x] **Type sync**: Generate or update docstring types from type annotations.
- [x] **Signature sync**: Detect undocumented or extraneous parameters by
  cross-referencing function signatures.
- [x] **Section validation**: Check section headers, ordering, and entry formatting.
- [x] **Configurable rules**: Enable, disable, or change severity of individual rules
  via `pyproject.toml` or `.glossa.yaml`.
- [x] **CI-friendly**: `check` command exits non-zero on violations; JSON output for
  machine consumption.

---

## Installation

### Using pip

```bash
pip install git+https://github.com/esther-poniatowski/glossa.git
```

### Using conda

```bash
conda install glossa -c eresthanaconda
```

### From source

1. Clone the repository:

      ```bash
      git clone https://github.com/esther-poniatowski/glossa.git
      ```

2. Create a dedicated virtual environment and install:

      ```bash
      cd glossa
      conda env create -f environment.yml
      conda activate glossa
      ```

---

## Quick Start

### CLI

Lint a file or directory:

```sh
glossa lint src/
```

Apply auto-fixes:

```sh
glossa fix src/
```

CI mode (non-zero exit on violations):

```sh
glossa check src/
```

### Python

```python
from glossa.application.linting import lint_source

diagnostics = lint_source(source_code, file_path="example.py")
for d in diagnostics:
    print(f"{d.code}: {d.message}")
```

---

## Usage

### Command Line Interface (CLI)

#### `glossa lint`

Lint files and report diagnostics to stderr.

```sh
glossa lint src/ tests/
glossa lint src/module.py --select D1xx,D4xx
glossa lint src/ --ignore D200 --format json
```

| Option | Description |
| ------ | ----------- |
| `--select CODES` | Enable only these rules (codes or groups like `D1xx`). |
| `--ignore CODES` | Disable specific rules. |
| `--format text\|json` | Output format (default: `text`). |
| `--config PATH` | Path to configuration file. |

#### `glossa fix`

Apply auto-fixes to files in place.

```sh
glossa fix src/
glossa fix src/ --diff          # preview changes without writing
glossa fix src/ --select D4xx   # only apply type-sync fixes
```

| Option | Description |
| ------ | ----------- |
| `--select CODES` | Apply only fixes from these rules. |
| `--diff` | Print unified diff instead of modifying files. |
| `--check` | Exit non-zero if fixes are available (dry-run for CI). |

#### `glossa check`

Alias for `glossa lint` with a non-zero exit code on any diagnostic. Designed for CI
pipelines and pre-commit hooks.

```sh
glossa check src/
```

### Programmatic Usage

```python
from pathlib import Path
from glossa.adapters.bootstrap import create_linter

linter = create_linter()
diagnostics = linter.lint(Path("src/"))

for d in diagnostics:
    print(f"{d.target.source_id} {d.code} {d.message}")
```

---

## Configuration

### Configuration File

Glossa reads configuration from `pyproject.toml` or `.glossa.yaml`. The resolved
policy is built from defaults, config files, per-file overrides, inline suppressions,
and CLI flags.

#### pyproject.toml

```toml
[tool.glossa.rules]
select = ["D1xx", "D2xx", "D3xx", "D4xx", "D5xx"]
ignore = ["D205"]

[tool.glossa.rules.severity_overrides]
D201 = "error"

[tool.glossa.rules.per_file_ignores]
"tests/**.py" = ["D102"]

[tool.glossa.rules.rule_options.D104]
simple_property_requires_returns = false

[tool.glossa.fix]
enabled = true
apply = "safe"
validate_after_apply = true

[tool.glossa.output]
format = "text"
color = true
```

#### .glossa.yaml

```yaml
rules:
  select: ["D1xx", "D2xx", "D3xx", "D4xx", "D5xx"]
  ignore: ["D205"]
  severity_overrides:
    D201: error
  per_file_ignores:
    "tests/**.py": ["D102"]
  rule_options:
    D104:
      simple_property_requires_returns: false

fix:
  enabled: true
  apply: safe
  validate_after_apply: true

suppressions:
  inline_enabled: true
  directive_prefix: "glossa: ignore="

output:
  format: text
  color: true
  show_source: true
```

### Key Options

| Option | Description | Default |
| ------ | ----------- | ------- |
| `rules.select` | Rule codes or groups to enable. | All |
| `rules.ignore` | Rule codes to disable. | None |
| `rules.per_file_ignores` | Disable specific rules for matching file globs. | None |
| `rules.rule_options` | Resolve ambiguous guide policies explicitly. | None |
| `fix.apply` | Apply no fixes, validated safe fixes, or explicitly unsafe fixes. | `safe` |
| `suppressions.inline_enabled` | Enable inline `glossa: ignore=` directives. | `true` |
| `output.format` | Output format (`text` or `json`). | `text` |

---

## Documentation

- [User Guide](https://esther-poniatowski.github.io/glossa/guide/)
- [API Documentation](https://esther-poniatowski.github.io/glossa/api/)
- [Design Plan](docs/design-plan.md)
- [Design Principles](docs/design-principles.md)
- [Docstring Guide](docs/guide/docstring-guide.md) — the conventions enforced by glossa

> [!NOTE]
> Documentation can also be browsed locally from the [`docs/`](docs/) directory.

---

## Architecture

Glossa follows a layered architecture with strict dependency direction to maximize
testability and extensibility.

| Layer | Modules | Responsibility |
| ----- | ------- | -------------- |
| Domain | `domain/models`, `domain/parsing`, `domain/rules/`, `domain/fixes` | Pure docstring models, parsing, rule logic, fix planning |
| Application | `application/contracts`, `application/protocols`, `application/policy`, `application/linting`, `application/fixing`, `application/registry` | DTO ownership, policy resolution, orchestration, explicit registries |
| Infrastructure | `infrastructure/discovery`, `infrastructure/extraction`, `infrastructure/files`, `infrastructure/config`, `infrastructure/plugins` | Source discovery, AST extraction, file I/O, config loading, plugin loading |
| Adapters | `adapters/cli`, `adapters/formatters`, `adapters/bootstrap` | CLI interface, output formatting, composition root |

For full architectural details and the rule catalog, see the [Design Plan](docs/design-plan.md)
and [Design Principles](docs/design-principles.md).

---

## Support

**Issues**: [GitHub Issues](https://github.com/esther-poniatowski/glossa/issues)

**Email**: `esther.poniatowski@ens.psl.eu`

---

## Contributing

Please refer to the [contribution guidelines](CONTRIBUTING.md).

---

## Acknowledgments

### Authors & Contributors

**Author**: @esther-poniatowski

**Contact**: `esther.poniatowski@ens.psl.eu`

For academic use, please cite using the GitHub "Cite this repository" feature to
generate a citation in various formats.

Alternatively, refer to the [citation metadata](CITATION.cff).

### Third-Party Dependencies

- **[Typer](https://typer.tiangolo.com/)** — CLI framework
- **[Rich](https://rich.readthedocs.io/)** — Terminal output formatting
- **[PyYAML](https://pyyaml.org/)** — YAML configuration parsing

---

## License

This project is licensed under the terms of the [GNU General Public License v3.0](LICENSE).
