<!--
TODO: Review and adapt all descriptive content to reflect the specific details of the
project (e.g., feature list, command-line examples, configuration options).

TODO: Remove sections marked OPTIONAL if they do not apply to the project.
-->
# glossa

[![Conda](https://img.shields.io/badge/conda-eresthanaconda--channel-blue)](#installation)
[![Maintenance](https://img.shields.io/maintenance/yes/2026)]()
[![Last Commit](https://img.shields.io/github/last-commit/esther-poniatowski/glossa)](https://github.com/esther-poniatowski/glossa/commits/main)
[![Python](https://img.shields.io/badge/python-%E2%89%A53.12-blue)](https://www.python.org/)
[![License: GPL](https://img.shields.io/badge/License-GPL--3.0-yellow.svg)](https://opensource.org/licenses/GPL-3.0)

Documentation linter for Python projects

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Support](#support)
- [Contributing](#contributing)
- [Acknowledgments](#acknowledgments)
- [License](#license)

## Overview

<!--
Provide a 2-4 sentence summary of what the project does and why it exists.
Then include Motivation and Advantages subsections.
-->

### Motivation

<!--
Explain the problem this project solves. What pain point or gap does it address?
-->

### Advantages

<!--
List 3-5 key advantages of this project over alternatives or manual approaches.
-->

---

## Features

- [X] **Feature 1:** Description.
- [ ] **Feature 2:** Description.

---

## Installation

To install the package and its dependencies, use one of the following methods:

### Using pip

Install the package from the GitHub repository URL:

```bash
pip install git+https://github.com/esther-poniatowski/glossa.git
```

### Using conda

Install the package from the eresthanaconda channel:

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

<!--
Provide a minimal, concrete example that gets the user from zero to a working result.
This should be copy-pasteable and demonstrate the core value proposition.
Include both CLI and Python API examples if applicable.
-->

### CLI

```sh
glossa --help
```

### Python

```python
import glossa

glossa.info()
```

---

## Usage

### Command Line Interface (CLI)

<!--
Document the main CLI commands with concrete examples and expected output.
Show real commands, not just --help. Include at least one end-to-end example.
-->

```sh
glossa --help
```

### Programmatic Usage

<!--
Show how to use the package as a Python library. Include import statements,
object construction, and a representative workflow.
-->

```python
import glossa
```

---

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
| -------- | ----------- | ------- | -------- |
| `VAR_1` | Description. | None | Yes |
| `VAR_2` | Description. | `false` | No |

### Configuration File

Configuration options are specified in YAML files located in the `config/` directory.

The canonical configuration schema is provided in [`config/default.yaml`](config/default.yaml).

```yaml
var_1: value1
var_2: value2
```

---

## Documentation

- [User Guide](https://esther-poniatowski.github.io/glossa/guide/)
- [API Documentation](https://esther-poniatowski.github.io/glossa/api/)

> [!NOTE]
> Documentation can also be browsed locally from the [`docs/`](docs/) directory.

---

<!-- OPTIONAL: Include for projects with non-trivial internal structure. -->
## Architecture

<!--
Describe the high-level module organization and architectural layers.
Include a table of modules or a diagram if helpful.
-->

| Layer | Modules | Responsibility |
| ----- | ------- | -------------- |
| Domain | `module_a` | Core business logic |
| Application | `module_b` | Use-case orchestration |
| Infrastructure | `module_c` | File I/O, config loading |
| Adapters | `cli` | CLI interface |

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

- **[Library A](link)** -- Purpose
- **[Library B](link)** -- Purpose

---

## License

This project is licensed under the terms of the [GNU General Public License v3.0](LICENSE).
