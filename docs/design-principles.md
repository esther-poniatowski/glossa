# Design Principles

Implementation standards for glossa. These principles are normative and constrain all
production code, tests, and future design documents.

## 1. Goals

The architecture must remain:

- testable without filesystem or environment access in the domain layer
- explicit about boundaries and dependencies
- safe when performing automatic edits
- extensible without hidden state or import-order behavior

## 2. Layered Architecture

### 2.1 Dependency Direction

Dependencies point inward:

```text
Adapters -> Application -> Domain
                |
                -> Infrastructure (through application-owned protocols)
```

The domain layer depends on nothing outside itself. Infrastructure never defines the
interfaces that govern its own use.

### 2.2 Single Composition Root

There is exactly one composition root, in the adapter layer. The root handles:

- constructing infrastructure implementations
- loading plugins
- assembling registries
- wiring application services

No other module may perform global wiring as import-time side effects.

### 2.3 Protocol Ownership

All effectful capabilities are modeled as application-defined protocols, including:

- source discovery
- source reading and writing
- Python extraction
- configuration loading
- plugin loading

Infrastructure may implement these protocols but may not widen them ad hoc.

### 2.4 Boundary DTOs

Cross-layer data transfer uses immutable DTOs with explicit schemas. No layer may pass:

- `pathlib.Path` into the domain
- `ast.AST` outside infrastructure
- open file objects, loggers, or CLI types across boundaries

## 3. Domain Rules

### 3.1 Purity

Domain code performs no I/O, no environment access, and no mutation of shared state.
Domain behavior must be testable with plain value objects.

### 3.2 Immutable Models

Frozen dataclasses with mutable fields are not sufficient. Domain and application DTOs
must use immutable containers such as tuples and immutable mappings.

### 3.3 No Infrastructure Types

The domain may represent spans, positions, source identifiers, and formatting metadata,
but it may not depend on infrastructure-specific classes such as `Path` or `ast.AST`.

### 3.4 Lossless and Semantic Models

When the system both analyzes and edits text, it must preserve two views:

- a semantic model for rule evaluation
- a lossless model for precise edit planning

No parser may normalize away information that affects linting or fix generation.

## 4. Extensibility and State

### 4.1 Explicit Dependencies

Rules, reporters, and use cases declare dependencies through constructor arguments or
protocols. Hidden module-level lookups are prohibited.

### 4.2 Plugin Registration

Third-party extensions register through explicit providers resolved at bootstrap. The
loading mechanism must be deterministic and observable in tests.

### 4.3 No Import-Time Work

Importing a module must not mutate global registries, discover plugins, or read the
filesystem.

### 4.4 No Hidden Singletons

Mutable module-level registries are prohibited. Shared services such as rule catalogs
must be explicit objects created by the composition root and passed to consumers.

## 5. Transformations and Fixes

### 5.1 Edits as Data

Automatic fixes are represented as explicit edit plans. Rules do not mutate source
text directly.

### 5.2 Conflict Detection

If edits overlap or cannot be composed deterministically, the system must reject the
automatic fix rather than guessing.

### 5.3 Validation After Edit Planning

Every accepted fix plan must be validated by reparsing the edited source and rerunning
the affected analysis on the changed targets.

## 6. Error Handling and Diagnostics

### 6.1 Errors vs Diagnostics

Lint diagnostics describe user code. Operational errors describe tool failures. These
are different channels and must not be conflated.

### 6.2 Partial Failure Behavior

Per-file failures should degrade gracefully when possible. Fatal startup errors stop
the run; per-file analysis errors are recorded and surfaced without discarding valid
results from other files.

### 6.3 Exception Hierarchy

The application defines a closed exception hierarchy rooted at a single base error
type. Each major failure class has its own exception type. Bare `Exception` and
string-based error signaling are prohibited.

## 7. Testing

### 7.1 Domain Tests

Domain tests run with pure values only. No filesystem fixtures are required to test
parsing, rule evaluation, or fix planning.

### 7.2 Contract Tests

Each infrastructure implementation must satisfy protocol-level contract tests, not just
end-to-end smoke tests.

### 7.3 Idempotency and Round-Trip

Fixes must be tested for:

- idempotency
- preservation of syntax validity
- preservation of docstring structure where required
- rerun cleanliness for the rules that produced the fix
