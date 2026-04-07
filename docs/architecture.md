# Architecture

Glossa follows a four-layer architecture with strict dependency direction. Each
layer depends only on the layers below it, maximizing testability and
extensibility.

## Layer Diagram

```text
Adapters -> Application -> Domain
                |
                -> Infrastructure (via application-defined protocols)
```

There is exactly one composition root: `glossa/adapters/bootstrap.py`.

## Domain (`glossa/domain/`)

Pure logic. No filesystem access, no environment access, no logging, no `Path`,
no `ast.AST`, and no hidden mutable state.

| Module | Responsibility |
| ------ | -------------- |
| `models.py` | Immutable semantic and syntax-preserving docstring models |
| `parsing.py` | Parse raw docstring text into lossless and semantic structures |
| `rules/` | Rule implementations over pure lint targets |
| `fixes.py` | Pure edit planning, conflict detection, and fix validation helpers |
| `traceability.py` | Mapping between guide clauses and rules / out-of-scope items |

## Application (`glossa/application/`)

Use-case orchestration. The application layer owns the contracts that
infrastructure must satisfy and assembles the pure inputs consumed by the domain.

| Module | Responsibility |
| ------ | -------------- |
| `contracts.py` | Immutable DTOs shared across layers |
| `protocols.py` | Discovery, extraction, config, editing, and plugin ports |
| `policy.py` | Rule selection, per-file overrides, inline suppressions |
| `linting.py` | Discover -> extract -> parse -> assemble targets -> run rules |
| `fixing.py` | Resolve fix conflicts -> apply edits -> validate output |
| `registry.py` | Explicit rule registry and plugin loading orchestration |

## Infrastructure (`glossa/infrastructure/`)

Performs effects. Infrastructure implements application-defined protocols and
stops at explicit DTO boundaries.

| Module | Responsibility |
| ------ | -------------- |
| `discovery.py` | Walk configured paths and yield Python source files |
| `extraction.py` | Parse Python source with `ast` and emit immutable `ExtractedTarget` DTOs |
| `files.py` | Read source files and write edited output |
| `config.py` | Load raw configuration data from `pyproject.toml` and `.glossa.yaml` |
| `plugins.py` | Load third-party rule providers from entry points |

## Adapters (`glossa/adapters/`)

Translate external inputs and outputs. Adapters may depend on concrete
application services but contain no business logic.

| Module | Responsibility |
| ------ | -------------- |
| `cli.py` | Typer-based CLI commands |
| `formatters.py` | Text and JSON reporters |
| `bootstrap.py` | Composition root that wires protocols, registry, and use cases |

## Extraction vs Parsing Boundary

This boundary is strict:

- **Infrastructure extraction ends** when `extraction.py` emits immutable
  `ExtractedTarget` DTOs. These DTOs may contain raw docstring text,
  docstring-local formatting metadata, signature facts, control-flow facts, and
  source spans.
- **Domain parsing begins** when `parsing.py` receives only raw docstring text
  and docstring-local metadata from an `ExtractedDocstring` DTO. No `ast.AST`,
  `Path`, or file handles cross into the domain.

AST processing never appears in rules. Rules operate only on pure `LintTarget`
instances assembled by the application layer.

## Design Principles

- **Single responsibility** -- each module addresses one concern.
- **Dependency inversion** -- upper layers depend on abstractions defined in the
  application layer, not on concrete infrastructure.
- **Extensible rules** -- each rule is a self-contained unit registered in an
  explicit registry. Adding a rule requires no modification to existing code.
- **Configurable policies** -- the application layer resolves rule selection,
  severity overrides, and fix strategies from a merged configuration.

For the full design rationale, see the
[Design Principles](design-principles.md).

## Dependencies

| Dependency | Purpose |
| ---------- | ------- |
| `ast` (stdlib) | Python syntax parsing in infrastructure extraction |
| `pathlib` (stdlib) | File handling inside infrastructure and adapters only |
| `tomllib` (stdlib 3.11+) | `pyproject.toml` parsing |
| `pyyaml` | `.glossa.yaml` parsing |
| `typer` | CLI adapter |
| `rich` | Text formatter adapter |
| `importlib.metadata` (stdlib) | Plugin entry point discovery |

No parser generator or AST wrapper is required for v1. If this changes, the new
dependency must preserve the layer boundary rules described above.
