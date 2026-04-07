# Design Plan

Architecture and implementation plan for glossa, a Python docstring linter and
auto-fixer for NumPy-style docstrings.

This document is normative for the implementation, supersedes the earlier draft,
and resolves the structural issues identified in the adversarial design review.

## 1. Scope

Glossa statically analyzes Python source files and reports docstring violations
against the conventions defined in the [Docstring Guide](guide/docstring-guide.md).
Glossa operates in two modes:

- **Lint**: report diagnostics.
- **Fix**: apply safe automatic corrections where a deterministic edit exists.

Both modes are available through a CLI and a Python API.

### 1.1 Normative Inputs

- **Functional specification**: [`docs/guide/docstring-guide.md`](guide/docstring-guide.md)
- **Implementation specification**: [`docs/design-principles.md`](design-principles.md)

### 1.2 Explicit Non-Goals

The guide contains conventions that are valuable but not reliably enforceable by a
static docstring linter. Glossa v1 explicitly does **not** attempt to:

- lint inline comments outside docstrings (guide section 6)
- judge semantic quality of prose beyond rule-specific heuristics
- execute doctest examples
- infer optional `See Also` links from API topology
- reason about behavior introduced only at runtime by dynamic decorators or metaclasses

Every guide convention is mapped in section 12 either to concrete rules or to one of
these explicit non-goals.

## 2. Architectural Layers

Glossa follows a four-layer architecture with strict dependency direction.

```text
Adapters -> Application -> Domain
                |
                -> Infrastructure (via application-defined protocols)
```

There is exactly one composition root: `glossa/adapters/bootstrap.py`.

### 2.1 Domain (`glossa/domain/`)

Pure logic. No filesystem access, no environment access, no logging, no `Path`,
no `ast.AST`, and no hidden mutable state.

| Module | Responsibility |
| ------ | -------------- |
| `models.py` | Immutable semantic and syntax-preserving docstring models |
| `parsing.py` | Parse raw docstring text into lossless and semantic structures |
| `rules/` | Rule implementations over pure lint targets |
| `fixes.py` | Pure edit planning, conflict detection, and fix validation helpers |
| `traceability.py` | Mapping between guide clauses and rules / out-of-scope items |

### 2.2 Application (`glossa/application/`)

Use-case orchestration. The application layer owns the contracts that infrastructure
must satisfy and assembles the pure inputs consumed by the domain.

| Module | Responsibility |
| ------ | -------------- |
| `contracts.py` | Immutable DTOs shared across layers |
| `protocols.py` | Discovery, extraction, config, editing, and plugin ports |
| `policy.py` | Rule selection, per-file overrides, inline suppressions |
| `linting.py` | Discover -> extract -> parse -> assemble targets -> run rules |
| `fixing.py` | Resolve fix conflicts -> apply edits -> validate output |
| `registry.py` | Explicit rule registry and plugin loading orchestration |

### 2.3 Infrastructure (`glossa/infrastructure/`)

Performs effects. Infrastructure implements application-defined protocols and stops
at explicit DTO boundaries.

| Module | Responsibility |
| ------ | -------------- |
| `discovery.py` | Walk configured paths and yield Python source files |
| `extraction.py` | Parse Python source with `ast` and emit immutable `ExtractedTarget` DTOs |
| `files.py` | Read source files and write edited output |
| `config.py` | Load raw configuration data from `pyproject.toml` and `.glossa.yaml` |
| `plugins.py` | Load third-party rule providers from entry points |

### 2.4 Adapters (`glossa/adapters/`)

Translate external inputs and outputs. Adapters may depend on concrete application
services but contain no business logic.

| Module | Responsibility |
| ------ | -------------- |
| `cli.py` | Typer-based CLI commands |
| `formatters.py` | Text and JSON reporters |
| `bootstrap.py` | Composition root that wires protocols, registry, and use cases |

### 2.5 Extraction vs Parsing Boundary

This boundary is strict:

- **Infrastructure extraction ends** when `extraction.py` emits immutable
  `ExtractedTarget` DTOs. These DTOs may contain raw docstring text, docstring-local
  formatting metadata, signature facts, control-flow facts, and source spans.
- **Domain parsing begins** when `parsing.py` receives only raw docstring text and
  docstring-local metadata from an `ExtractedDocstring` DTO. No `ast.AST`, `Path`, or
  file handles cross into the domain.

AST processing never appears in rules. Rules operate only on pure `LintTarget`
instances assembled by the application layer.

## 3. Core Application Contracts

All cross-layer contracts are immutable and free of infrastructure-specific types.

### 3.1 Shared Value Objects

```python
@dataclass(frozen=True)
class SourceRef:
    source_id: str            # project-relative POSIX path string
    symbol_path: tuple[str, ...]

@dataclass(frozen=True)
class TextPosition:
    line: int
    column: int

@dataclass(frozen=True)
class TextSpan:
    start: TextPosition
    end: TextPosition

class TargetKind(Enum):
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    PROPERTY = "property"

class Visibility(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"
```

### 3.2 Extracted Data From Infrastructure

`ExtractedTarget` is the sole output of infrastructure extraction. It is owned by the
application layer even though infrastructure constructs it.

```python
@dataclass(frozen=True)
class ExtractedDocstring:
    body: str
    quote: Literal['"""', "'''"]
    string_prefix: str              # e.g. "", "r"
    indentation: str
    body_span: TextSpan             # body span within source file
    literal_span: TextSpan          # full string literal span within source file

@dataclass(frozen=True)
class ParameterFact:
    name: str
    annotation: str | None
    default: str | None
    kind: Literal[
        "positional_only",
        "positional_or_keyword",
        "var_positional",
        "keyword_only",
        "var_keyword",
    ]

@dataclass(frozen=True)
class SignatureFacts:
    parameters: tuple[ParameterFact, ...]
    return_annotation: str | None
    returns_value: bool
    yields_value: bool

@dataclass(frozen=True)
class ExceptionFact:
    type_name: str
    evidence: Literal["raise", "reraise", "documented_contract"]
    confidence: Literal["high", "medium", "low"]

@dataclass(frozen=True)
class WarningFact:
    type_name: str
    confidence: Literal["high", "medium", "low"]

@dataclass(frozen=True)
class AttributeFact:
    name: str
    annotation: str | None
    defined_in_init: bool
    is_public: bool

@dataclass(frozen=True)
class ModuleSymbolFact:
    name: str
    kind: Literal["class", "function"]
    is_public: bool

@dataclass(frozen=True)
class RelatedTargets:
    parent: SourceRef | None = None
    constructor: SourceRef | None = None
    property_getter: SourceRef | None = None

@dataclass(frozen=True)
class ExtractedTarget:
    ref: SourceRef
    kind: TargetKind
    visibility: Visibility
    is_test_target: bool
    docstring: ExtractedDocstring | None
    signature: SignatureFacts | None
    exceptions: tuple[ExceptionFact, ...]
    warnings: tuple[WarningFact, ...]
    attributes: tuple[AttributeFact, ...]
    module_symbols: tuple[ModuleSymbolFact, ...]
    decorators: tuple[str, ...]
    related: RelatedTargets
```

### 3.3 Pure Lint Input

The application layer resolves related targets, parses docstrings, and produces the
pure value consumed by rules:

```python
@dataclass(frozen=True)
class LintTarget:
    ref: SourceRef
    kind: TargetKind
    visibility: Visibility
    is_test_target: bool
    docstring: ParsedDocstring | None
    raw_docstring: ExtractedDocstring | None
    signature: SignatureFacts | None
    exceptions: tuple[ExceptionFact, ...]
    warnings: tuple[WarningFact, ...]
    attributes: tuple[AttributeFact, ...]
    module_symbols: tuple[ModuleSymbolFact, ...]
    related: Mapping[str, "RelatedTargetSnapshot"]

@dataclass(frozen=True)
class RelatedTargetSnapshot:
    ref: SourceRef
    kind: TargetKind
    docstring: ParsedDocstring | None
    raw_docstring: ExtractedDocstring | None
    signature: SignatureFacts | None
```

Rules see only `LintTarget` plus resolved policy. They never reach into source files
or AST nodes.

## 4. Domain Models

The domain keeps both:

- a **lossless syntax-preserving model** for safe edit planning
- a **semantic model** for rule evaluation

Both views are immutable and share docstring-local spans. Duplicate or malformed
sections are preserved rather than normalized away.

### 4.1 Lossless Docstring Model

```python
@dataclass(frozen=True)
class DocstringSpan:
    start_offset: int
    end_offset: int

@dataclass(frozen=True)
class DocstringSyntax:
    raw_body: str
    quote: Literal['"""', "'''"]
    string_prefix: str
    indentation: str
    leading_blank_lines: int
    trailing_blank_lines: int
```

`DocstringSpan` values are relative to `raw_body`, not to filesystem coordinates. This
keeps the domain pure while still supporting precise edits.

### 4.2 Semantic Docstring Model

```python
class TypedSectionKind(Enum):
    PARAMETERS = "Parameters"
    RETURNS = "Returns"
    YIELDS = "Yields"
    ATTRIBUTES = "Attributes"
    RAISES = "Raises"
    WARNS = "Warns"

class ProseSectionKind(Enum):
    NOTES = "Notes"
    WARNINGS = "Warnings"
    EXAMPLES = "Examples"

class InventorySectionKind(Enum):
    CLASSES = "Classes"
    FUNCTIONS = "Functions"

@dataclass(frozen=True)
class Summary:
    text: str
    span: DocstringSpan

@dataclass(frozen=True)
class TypedEntry:
    name: str | None            # None for Returns/Yields entries
    type_text: str | None
    default_text: str | None
    description_lines: tuple[str, ...]
    span: DocstringSpan

@dataclass(frozen=True)
class TypedSection:
    kind: TypedSectionKind
    title_span: DocstringSpan
    underline_span: DocstringSpan
    entries: tuple[TypedEntry, ...]
    span: DocstringSpan

@dataclass(frozen=True)
class ProseSection:
    kind: ProseSectionKind
    title_span: DocstringSpan
    underline_span: DocstringSpan
    body_lines: tuple[str, ...]
    span: DocstringSpan

@dataclass(frozen=True)
class InventoryItem:
    name: str
    description_lines: tuple[str, ...]
    span: DocstringSpan

@dataclass(frozen=True)
class InventorySection:
    kind: InventorySectionKind
    title_span: DocstringSpan
    underline_span: DocstringSpan
    items: tuple[InventoryItem, ...]
    span: DocstringSpan

@dataclass(frozen=True)
class SeeAlsoItem:
    name: str
    description_lines: tuple[str, ...]
    span: DocstringSpan

@dataclass(frozen=True)
class SeeAlsoSection:
    title_span: DocstringSpan
    underline_span: DocstringSpan
    items: tuple[SeeAlsoItem, ...]
    span: DocstringSpan

@dataclass(frozen=True)
class DeprecationDirective:
    version: str | None
    body_lines: tuple[str, ...]
    span: DocstringSpan

@dataclass(frozen=True)
class UnknownSection:
    title: str
    body_lines: tuple[str, ...]
    span: DocstringSpan

@dataclass(frozen=True)
class ParseIssue:
    kind: str
    message: str
    span: DocstringSpan | None

SectionNode = TypedSection | ProseSection | InventorySection | SeeAlsoSection | UnknownSection

@dataclass(frozen=True)
class ParsedDocstring:
    syntax: DocstringSyntax
    summary: Summary | None
    deprecation: DeprecationDirective | None
    extended_description_lines: tuple[str, ...]
    sections: tuple[SectionNode, ...]
    parse_issues: tuple[ParseIssue, ...]
```

### 4.3 Model Invariants

- All containers are tuples or immutable mappings.
- Section order is preserved exactly as written.
- Duplicate sections are preserved as separate nodes.
- Unknown headers are preserved as `UnknownSection`.
- Malformed but recoverable content becomes `ParseIssue`, not silent normalization.

## 5. Diagnostics and Fixes

Diagnostics are pure values. Fixes are grouped, validated edit plans rather than
single line replacements.

```python
class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    CONVENTION = "convention"

@dataclass(frozen=True)
class Diagnostic:
    rule: str
    message: str
    severity: Severity
    target: SourceRef
    span: DocstringSpan | TextSpan | None
    fix: "FixPlan | None" = None

class EditKind(Enum):
    INSERT = "insert"
    REPLACE = "replace"
    DELETE = "delete"

@dataclass(frozen=True)
class DocstringEdit:
    kind: EditKind
    span: DocstringSpan | None
    anchor: str                  # semantic anchor such as "Parameters:after_header"
    text: str

@dataclass(frozen=True)
class FixPlan:
    description: str
    target: SourceRef
    edits: tuple[DocstringEdit, ...]
    affected_rules: tuple[str, ...]
```

### 5.1 Fix Safety Rules

- Edits are grouped per target docstring.
- Overlapping edits are never auto-merged silently.
- If two fix plans for the same target overlap or have incompatible anchors, the
  application marks them as conflicting and skips auto-application for that target.
- Each accepted fix plan is validated by reparsing the edited Python source,
  re-extracting the changed target, reparsing the docstring, and rerunning the rules
  that produced the fix.
- If validation fails, the file is left unchanged and an operational error is reported.

This strategy supports insertions, deletions, replacements, and multi-site edits while
preserving quote style, string prefix, indentation, and surrounding whitespace.

## 6. Rule System

### 6.1 Rule Contract

```python
@dataclass(frozen=True)
class RuleMetadata:
    name: str
    group: str
    description: str
    default_severity: Severity
    applies_to: frozenset[TargetKind]
    fixable: bool

@dataclass(frozen=True)
class RuleContext:
    policy: RulePolicy
    section_order: tuple[str, ...] = ()

class Rule(Protocol):
    metadata: RuleMetadata

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]: ...
```

`RuleContext` is intentionally narrow. It contains resolved policy only. It does not
contain AST nodes, file handles, `Path`, or ad hoc parent objects.

### 6.2 Dispatch Model

Rule dispatch is an application responsibility:

1. discover targets
2. assemble `LintTarget` snapshots with related entities
3. filter rules by `metadata.applies_to`
4. evaluate each rule independently

Rules never dispatch themselves by scope. Cross-target checks are supported through
`target.related`, not through infrastructure leakage.

### 6.3 Registry and Extensibility

Rules are provided through an explicit registry object assembled in the composition
root. There is no module-level mutable singleton and no import-order registration.

```python
class RuleProvider(Protocol):
    def load_rules(self) -> tuple[Rule, ...]: ...

@dataclass(frozen=True)
class RuleRegistry:
    builtins: tuple[Rule, ...]
    plugins: tuple[Rule, ...]

    def all_rules(self) -> tuple[Rule, ...]: ...
```

Third-party packages extend glossa through Python entry points under the
`glossa.rules` group. The plugin loader resolves them during bootstrap and injects the
result into `RuleRegistry`.

### 6.4 Rule Independence

Rules do not consume other rules' outputs. Any shared analysis needed by multiple
rules must be computed once in extraction or target assembly and exposed as explicit
facts on `LintTarget`.

### 6.5 Rule Catalog

#### Presence and Coverage (`presence`)

| Rule | Description | Applies To | Fixable |
| ---- | ----------- | ---------- | ------- |
| missing-module-docstring | Missing public module docstring | module | No |
| missing-class-docstring | Missing public class docstring | class | No |
| missing-callable-docstring | Missing public callable docstring | function, method, property | No |
| missing-parameters-section | Missing Parameters section for documentable parameters | function, method, class | Yes |
| missing-returns-section | Missing Returns section where required | function, method, property | Yes |
| missing-yields-section | Missing Yields section for generators | function, method, property | Yes |
| missing-raises-section | Missing Raises section for public-contract exceptions | function, method, property | No |
| missing-warns-section | Missing Warns section for public warnings | function, method, property | No |
| missing-module-inventory | Missing module Classes/Functions inventory when required | module | Yes |
| missing-attributes-section | Missing Attributes section where class attributes need docs | class | No |
| params-in-init-not-class | Constructor parameters documented in __init__ instead of class | class | No |
| missing-deprecation-directive | Missing deprecation directive for deprecated public API | all | No |

#### Prose and Summary Format (`prose`)

| Rule | Description | Applies To | Fixable |
| ---- | ----------- | ---------- | ------- |
| non-imperative-summary | Summary not imperative where required | function, method, property | No |
| missing-period | Summary line missing terminal period | all | Yes |
| missing-blank-after-summary | Missing blank line after summary when body follows | all | Yes |
| first-person-voice | First-person voice in docstring | all | No |
| second-person-voice | Second-person voice in docstring | all | No |
| markdown-in-docstring | Markdown syntax where RST is required | all | No |

`non-imperative-summary` applies only to callables (function, method, property), not
to modules or classes.

#### Section Structure and Placement (`structure`)

| Rule | Description | Applies To | Fixable |
| ---- | ----------- | ---------- | ------- |
| malformed-underline | Section underline is malformed | all | Yes |
| section-order | Section order violates NumPy policy | all | No |
| undocumented-parameter | Parameter in signature but missing from docstring | function, method, class | Yes |
| extraneous-parameter | Parameter in docstring but not in signature | function, method, class | No |
| malformed-deprecation | Deprecation directive malformed or misplaced | all | No |
| rst-directive-instead-of-section | RST directive used where NumPy section exists | all | No |
| examples-in-non-entry-module | Examples in non-entry-point module (suppressed by default) | module | No |

#### Typed Entry Consistency (`typed-entries`)

| Rule | Description | Applies To | Fixable |
| ---- | ----------- | ---------- | ------- |
| missing-param-type | Parameter type missing from docstring | function, method, class | Yes |
| param-type-mismatch | Parameter type mismatches annotation | function, method, class | Yes |
| missing-return-type | Return type missing from docstring | function, method, property | Yes |
| return-type-mismatch | Return type mismatches annotation | function, method, property | Yes |
| yield-type-mismatch | Yield type missing or mismatched | function, method, property | Yes |
| missing-attribute-type | Attribute type missing | class | Yes |

#### Anti-Patterns (`anti-patterns`)

| Rule | Description | Applies To | Fixable |
| ---- | ----------- | ---------- | ------- |
| empty-docstring | Empty docstring body | all | No |
| trivial-dunder-docstring | Trivial dunder method docstring | method | No |
| redundant-returns-none | Redundant Returns None section | function, method, property | Yes |
| rst-note-warning-directive | RST note/warning directive instead of NumPy section | all | No |

## 7. Configuration

Configuration is split by concern. Loading raw config is infrastructure work;
resolving policy is application work.

### 7.1 Configuration Models

```python
@dataclass(frozen=True)
class RuleSelection:
    select: tuple[str, ...]
    ignore: tuple[str, ...]
    severity_overrides: Mapping[str, Severity]
    per_file_ignores: Mapping[str, tuple[str, ...]]
    rule_options: Mapping[str, Mapping[str, object]]
    section_order: tuple[str, ...]

@dataclass(frozen=True)
class ParsingOptions:
    section_aliases: Mapping[str, str]

@dataclass(frozen=True)
class SuppressionPolicy:
    inline_enabled: bool
    directive_prefix: str       # default: "glossa: ignore="

@dataclass(frozen=True)
class FixPolicy:
    enabled: bool
    apply: Literal["never", "safe", "unsafe"]
    validate_after_apply: bool

@dataclass(frozen=True)
class OutputOptions:
    format: Literal["text", "json"]
    color: bool
    show_source: bool

@dataclass(frozen=True)
class GlossaConfig:
    rules: RuleSelection
    suppressions: SuppressionPolicy
    fix: FixPolicy
    output: OutputOptions
    parsing: ParsingOptions
```

The resolved application config combines:

- built-in defaults
- `pyproject.toml` or `.glossa.yaml`
- per-file overrides
- inline suppressions
- CLI overrides

### 7.2 Ambiguous Guide Policies Become Explicit Options

Guide phrases such as "non-trivial", "when useful", and "top-level API entry point"
must not be left implicit. They are resolved through named policy options such as:

- `missing-callable-docstring.include_test_functions`
- `missing-callable-docstring.include_private_helpers`
- `missing-returns-section.simple_property_requires_returns`
- `missing-raises-section.contract_exception_allowlist`
- `missing-module-inventory.inventory_threshold`
- `examples-in-non-entry-module.api_entry_modules`
- `trivial-dunder-docstring.trivial_dunder_allowlist`

### 7.3 Configuration Schema

`pyproject.toml`:

```toml
[tool.glossa.rules]
select = ["presence", "prose", "structure", "typed-entries", "anti-patterns"]
ignore = ["markdown-in-docstring"]

[tool.glossa.rules.severity_overrides]
missing-period = "error"

[tool.glossa.rules.per_file_ignores]
"tests/**.py" = ["missing-callable-docstring"]

[tool.glossa.rules.rule_options.missing-returns-section]
simple_property_requires_returns = false

[tool.glossa.rules.rule_options.missing-module-inventory]
inventory_threshold = 2

[tool.glossa.suppressions]
inline_enabled = true
directive_prefix = "glossa: ignore="

[tool.glossa.fix]
enabled = true
apply = "safe"
validate_after_apply = true

[tool.glossa.output]
format = "text"
color = true
show_source = true

[tool.glossa.parsing.section_aliases]
Hint = "Notes"
```

`.glossa.yaml`:

```yaml
rules:
  select: ["presence", "prose", "structure", "typed-entries", "anti-patterns"]
  ignore: ["markdown-in-docstring"]
  severity_overrides:
    missing-period: error
  per_file_ignores:
    "tests/**.py": ["missing-callable-docstring"]
  rule_options:
    missing-returns-section:
      simple_property_requires_returns: false
    missing-module-inventory:
      inventory_threshold: 2

suppressions:
  inline_enabled: true
  directive_prefix: "glossa: ignore="

fix:
  enabled: true
  apply: safe
  validate_after_apply: true

output:
  format: text
  color: true
  show_source: true

parsing:
  section_aliases:
    Hint: Notes
```

### 7.4 Inline Suppression

Glossa supports single-line suppression directives attached to a target definition or
module header:

```python
def render(config: Config) -> str:  # glossa: ignore=non-imperative-summary,markdown-in-docstring
    """Returns the rendered text"""
```

Suppressions are applied in the application layer after extraction and before rule
dispatch. They do not mutate the domain model.

## 8. Error Handling and Robustness

### 8.1 Exception Hierarchy

Operational failures are not lint diagnostics. They are explicit tool errors:

```python
class GlossaError(Exception): ...
class ConfigurationError(GlossaError): ...
class DiscoveryError(GlossaError): ...
class ExtractionError(GlossaError): ...
class DocstringParseError(GlossaError): ...
class FixConflictError(GlossaError): ...
class ValidationError(GlossaError): ...
class FileWriteError(GlossaError): ...
class PluginLoadError(GlossaError): ...
```

### 8.2 Failure Semantics

- **Configuration and bootstrap failures** are fatal and stop the run immediately.
- **Per-file extraction or parse failures** are non-fatal by default. Glossa records
  an operational error for that file, continues processing other files, and returns a
  partial-failure exit code.
- **Rule execution failures** are treated as bugs and surfaced as operational errors.
- **Fix validation failures** leave the original file unchanged.

Malformed docstrings that can still be lexed become `ParseIssue` values and may also
trigger diagnostics. Only unrecoverable parser failures become `DocstringParseError`.

### 8.3 Exit Codes

| Exit Code | Meaning |
| --------- | ------- |
| `0` | Run completed successfully and found no diagnostics / no pending fixes |
| `1` | Run completed successfully and found diagnostics / available fixes |
| `2` | Usage or configuration error |
| `3` | Fatal operational error before analysis could complete |
| `4` | Partial failure: some files analyzed, some files failed operationally |

## 9. Processing Pipeline

```text
1. Bootstrap      Build the application services and explicit rule registry in adapters/bootstrap.py.
2. Load config    Read config files, merge CLI overrides, resolve rule policy.
3. Discover       Enumerate Python sources through DiscoveryPort.
4. Extract        Parse each file with ast and emit ExtractedTarget DTOs.
5. Parse          Convert raw docstrings into ParsedDocstring values.
6. Assemble       Build LintTarget snapshots with related entities.
7. Select rules   Filter by target kind, policy, suppressions, and severity overrides.
8. Evaluate       Run rules independently and collect diagnostics / fix plans.
9. Resolve fixes  Detect conflicts, reject unsafe fix groups, and build source edits.
10. Validate      Reparse source, re-extract changed targets, rerun affected rules.
11. Report        Emit diagnostics, operational errors, and fix results.
```

## 10. Dependencies

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
dependency must preserve the boundary rules in section 2.

## 11. Testing Strategy

Testing follows the layer boundaries and directly targets the risky rules.

### 11.1 Domain Tests

- parser unit tests over raw docstring strings
- lossless round-trip tests for quote style, indentation, and section ordering
- rule tests over pure `LintTarget` fixtures with no I/O
- heuristic corpus tests for non-imperative-summary mood detection
- confidence-threshold tests for missing-raises-section and missing-warns-section fact handling

### 11.2 Application Tests

- target assembly tests for related entities such as class + `__init__`
- policy resolution tests for per-file overrides and inline suppressions
- fix conflict detection tests
- fix idempotency tests: applying the same accepted fix twice yields identical output
- fix validation tests: edited output reparses and reruns cleanly for affected rules

### 11.3 Infrastructure Tests

- extraction tests for modules, classes, nested classes, properties, generators,
  decorators, overloads, `*args`, and `**kwargs`
- config loader tests for both file formats
- plugin loader contract tests

### 11.4 Adapter Tests

- CLI end-to-end tests for `lint`, `fix`, and `check`
- exit-code tests for clean, diagnostic, fatal, and partial-failure runs
- formatter tests for text and JSON output

### 11.5 Required Edge-Case Matrix

The test suite must include explicit coverage for:

- empty files
- comments-only files
- files with syntax errors
- malformed docstrings
- nested classes
- overloaded functions
- generators
- properties with short declarative summaries
- rich property docstrings with `Returns` / `Raises`
- decorators that preserve signatures
- decorators that obscure signatures
- `*args` / `**kwargs`
- duplicate sections
- unknown sections
- overlapping fix plans

## 12. Guide Traceability

Every guide convention must trace either to concrete rules or to explicit non-goals.

| Guide Clause | Status | Coverage |
| ------------ | ------ | -------- |
| 1.1 NumPy style required | Enforced | malformed-underline, section-order, rst-directive-instead-of-section, rst-note-warning-directive |
| 1.2 Imperative mood and impersonal voice | Enforced | non-imperative-summary, first-person-voice, second-person-voice |
| 1.3 Types in `Parameters` / `Returns` / `Yields` / `Attributes` | Enforced | missing-param-type, param-type-mismatch, missing-return-type, return-type-mismatch, yield-type-mismatch, missing-attribute-type |
| 1.4 Public modules/classes/functions require docstrings | Enforced | missing-module-docstring, missing-class-docstring, missing-callable-docstring |
| 1.4 Constructor params documented on class, not `__init__` | Enforced | missing-parameters-section, params-in-init-not-class |
| 1.4 Private helpers / tests / special methods policy | Enforced via config | missing-callable-docstring, trivial-dunder-docstring rule options |
| 1.4 Trivial property accessor optional | Enforced via config | missing-callable-docstring and missing-returns-section rule options |
| 2.2 Module inventory sections for large public modules | Enforced | missing-module-inventory |
| 2.2 Module `See Also` when useful | Out of scope | editorial judgment |
| 2.2 No `Examples` in non-entry-point modules | Enforced | examples-in-non-entry-module (suppressed by default) |
| 3.2 `Attributes` for public attributes needing docs | Enforced | missing-attributes-section, missing-attribute-type |
| 3.2 Class `Examples` when useful | Out of scope | editorial judgment |
| 4.2 Function summary period and blank line | Enforced | missing-period, missing-blank-after-summary |
| 4.2 `Parameters` required when parameters exist | Enforced | missing-parameters-section, undocumented-parameter, extraneous-parameter |
| 4.2 `Returns` required when returning a value | Enforced | missing-returns-section, missing-return-type, return-type-mismatch, redundant-returns-none |
| 4.2 `Raises` for public-contract exceptions | Enforced conservatively | missing-raises-section with confidence threshold |
| 4.2 `See Also` when useful | Out of scope | editorial judgment |
| 4.2 `Examples` when useful | Out of scope | editorial judgment |
| 4.2 `Notes` used sparingly | Out of scope | editorial judgment |
| 4.2 Deprecation directive placement | Enforced | missing-deprecation-directive, malformed-deprecation |
| 4.2 `Warns` for runtime warnings | Enforced conservatively | missing-warns-section |
| 4.2 `Warnings` prose section | Enforced structurally | rst-directive-instead-of-section, rst-note-warning-directive |
| 5.2 Simple properties may be declarative and omit `Returns` | Enforced | non-imperative-summary exempt; missing-returns-section controlled by property policy |
| 6 Inline comment guidance | Out of scope | non-docstring analysis |
| 7 Empty docstrings | Enforced | empty-docstring |
| 7 Trivial dunder docstrings | Enforced | trivial-dunder-docstring |
| 7 RST directives vs NumPy sections | Enforced | rst-directive-instead-of-section, rst-note-warning-directive |
| 7 Markdown in docstrings | Enforced | markdown-in-docstring |
| 7 First-person voice | Enforced | first-person-voice |
| 7 Redundant `Returns None` | Enforced | redundant-returns-none |

## 13. Extensibility

Glossa v1 is intentionally **NumPy-only**. The rule system is extensible, but style
extensibility is deferred until a separate ADR proves that a style-neutral semantic
model can support additional styles without weakening NumPy-specific checks.

Supported extension points:

- third-party rules via `glossa.rules` entry points
- additional reporters in the adapter layer
- alternative discovery implementations via `DiscoveryPort`

Not promised in v1:

- Google-style docstring support
- Sphinx-style parser swapping

## 14. Roadmap

### Phase 0 - Contracts and ADRs

- finalize `ExtractedTarget`, `LintTarget`, `ParsedDocstring`, and `FixPlan`
- freeze rule traceability matrix
- publish ADRs for exception discovery confidence and property policy

### Phase 1 - Extraction and Parsing Foundation

- implement discovery and extraction ports
- implement lossless docstring parser
- implement target assembly
- implement text reporter and baseline CLI wiring

### Phase 2 - Core Lint Rules

- implement presence, prose, and structure rules
- implement policy resolution, per-file overrides, and inline suppressions
- build fixture corpus for properties, constructors, and generators

### Phase 3 - Typed Rules and Safe Fix Engine

- implement remaining presence rules, typed-entries, and anti-patterns
- implement conflict detection and validation-backed fix application
- add `fix` and `check` CLI commands

### Phase 4 - Robustness and Ecosystem

- implement JSON output
- implement plugin loading and registry tests
- harden partial-failure reporting and operational diagnostics
