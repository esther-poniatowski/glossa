# Architecture

Glossa follows a layered architecture with strict dependency direction.
Each layer depends only on the layers below it, maximizing testability and
extensibility.

## Layers

| Layer | Modules | Responsibility |
| ----- | ------- | -------------- |
| Domain | `domain/models`, `domain/parsing`, `domain/rules/`, `domain/fixes` | Pure docstring models, parsing, rule logic, fix planning |
| Application | `application/contracts`, `application/protocols`, `application/policy`, `application/linting`, `application/fixing`, `application/registry` | DTO ownership, policy resolution, orchestration, explicit registries |
| Infrastructure | `infrastructure/discovery`, `infrastructure/extraction`, `infrastructure/files`, `infrastructure/config`, `infrastructure/plugins` | Source discovery, AST extraction, file I/O, config loading, plugin loading |
| Adapters | `adapters/cli`, `adapters/formatters`, `adapters/bootstrap` | CLI interface, output formatting, composition root |

## Design Principles

- **Single responsibility** — each module addresses one concern.
- **Dependency inversion** — upper layers depend on abstractions defined in the
  application layer, not on concrete infrastructure.
- **Extensible rules** — each rule is a self-contained unit registered in an
  explicit registry. Adding a rule requires no modification to existing code.
- **Configurable policies** — the application layer resolves rule selection,
  severity overrides, and fix strategies from a merged configuration.

For the full rule catalog and design rationale, see the
[Design Plan](design-plan.md) and [Design Principles](design-principles.md).
