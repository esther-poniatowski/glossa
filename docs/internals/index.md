# Internals

Developer documentation for glossa's architecture and implementation.
The internals section explains how the tool works, not how to use it.

| Document | Content |
| -------- | ------- |
| [Architecture](../architecture.md) | Layer structure, module responsibilities, dependency direction |
| [Contracts](contracts.md) | Cross-layer DTOs, extracted data, lint targets |
| [Domain Models](domain-models.md) | Lossless and semantic docstring models |
| [Fix Pipeline](fix-pipeline.md) | Diagnostics, edit plans, fix safety, conflict detection |
| [Rule System](rule-system.md) | Rule contract, dispatch, registry, extensibility, configuration design |
| [Error Handling](error-handling.md) | Exception hierarchy, failure semantics, exit codes |
| [Processing Pipeline](pipeline.md) | End-to-end lint and fix processing flow |
| [Testing Strategy](testing.md) | Test layer boundaries, edge-case matrix |
| [Design Principles](../design-principles.md) | Standing architectural constraints |
