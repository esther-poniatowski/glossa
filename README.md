# glossa

[![Conda](https://img.shields.io/badge/conda-eresthanaconda--channel-blue)](docs/guide/installation.md)
[![Maintenance](https://img.shields.io/maintenance/yes/2026)]()
[![Last Commit](https://img.shields.io/github/last-commit/esther-poniatowski/glossa)](https://github.com/esther-poniatowski/glossa/commits/main)
[![Python](https://img.shields.io/badge/python-%E2%89%A53.12-blue)](https://www.python.org/)
[![License: GPL](https://img.shields.io/badge/License-GPL--3.0-yellow.svg)](https://opensource.org/licenses/GPL-3.0)

Lints and fixes Python docstrings to follow NumPy-style conventions.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Acknowledgments](#acknowledgments)
- [License](#license)

## Overview

Glossa statically analyzes Python source files to enforce docstring conventions based
on the [numpydoc](https://numpydoc.readthedocs.io/) standard. The tool reports
violations, suggests fixes, and optionally applies corrections automatically —
including propagating types from annotations into docstrings.

### Motivation

Consistent docstrings are essential for generated API documentation, IDE tooltips, and
codebase readability. Existing tools (pydocstyle, ruff's docstring rules) check basic
presence and formatting but lack deep NumPy-section validation, parameter–signature
synchronization, and automatic type propagation from annotations to docstrings. Glossa
fills this gap with a rule set designed specifically around numpydoc conventions.

### Advantages

- **NumPy-native rule set** — validates section headers, parameter entries, return
  documentation, and section ordering against the numpydoc standard.
- **Signature-aware** — cross-references docstring parameters and types against actual
  function signatures and type annotations.
- **Auto-fix with type sync** — generates missing sections, propagates types from
  annotations to docstrings, and fixes formatting, all through configurable policies.
- **Extensible rule system** — each rule is a self-contained unit; new rules integrate
  without modifying existing code.
- **Multiple output formats** — human-readable (Rich) and JSON for CI integration.

---

## Features

- [x] **Lint**: Report docstring violations against numpydoc conventions.
- [x] **Auto-fix**: Apply automatic corrections (missing periods, section underlines,
  blank lines, redundant sections).
- [x] **Type sync**: Generate or update docstring types from type annotations.
- [x] **Signature sync**: Detect undocumented or extraneous parameters by
  cross-referencing function signatures.
- [x] **Section validation**: Check section headers, ordering, and entry formatting.
- [x] **Configurable rules**: Enable, disable, or change the severity of individual
  rules via `pyproject.toml` or `.glossa.yaml`.
- [x] **Descriptive rule names**: Rules are identified by readable names (e.g.
  `missing-period`, `undocumented-parameter`) and organized into groups
  (`presence`, `prose`, `structure`, `typed-entries`, `anti-patterns`).
- [x] **CI-friendly**: The `check` command exits non-zero on violations; JSON output
  supports machine consumption.

---

## Quick Start

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

Select specific rule groups:

```sh
# Select specific rule groups:
glossa lint src/ --select presence,prose

# Ignore specific rules:
glossa lint src/ --ignore missing-period,first-person-voice
```

---

## Documentation

| Guide | Content |
| ----- | ------- |
| [Installation](docs/guide/installation.md) | Prerequisites, pip/conda/source setup |
| [Usage](docs/guide/usage.md) | Workflows and detailed examples |
| [CLI Reference](docs/guide/cli-reference.md) | Full command registry and options |
| [Configuration](docs/guide/configuration.md) | Configuration files, rule selection, fix policies |
| [Rule Reference](docs/guide/rules.md) | Complete rule catalog with groups and descriptions |
| [Docstring Guide](docs/guide/docstring-guide.md) | The numpydoc conventions enforced by glossa |
| [Architecture](docs/architecture.md) | Layered design, module responsibilities, dependencies |
| [Internals](docs/internals/index.md) | Contracts, domain models, fix pipeline, rule system |

Full API documentation and rendered guides are also available at
[esther-poniatowski.github.io/glossa](https://esther-poniatowski.github.io/glossa/).

---

## Contributing

Contribution guidelines are described in [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Acknowledgments

### Authors

**Author**: @esther-poniatowski

For academic use, the GitHub "Cite this repository" feature generates citations in
various formats. The [citation metadata](CITATION.cff) file is also available.

### Third-Party Dependencies

- **[Typer](https://typer.tiangolo.com/)** — CLI framework.
- **[Rich](https://rich.readthedocs.io/)** — Terminal output formatting.
- **[PyYAML](https://pyyaml.org/)** — YAML configuration parsing.

---

## License

This project is licensed under the terms of the
[GNU General Public License v3.0](LICENSE).
