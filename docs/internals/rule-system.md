# Rule System

This document covers the rule contract, dispatch model, registry, extensibility,
configuration design, and ambiguous policy resolution.

## Rule Contract

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

## Dispatch Model

Rule dispatch is an application responsibility:

1. discover targets
2. assemble `LintTarget` snapshots with related entities
3. filter rules by `metadata.applies_to`
4. evaluate each rule independently

Rules never dispatch themselves by scope. Cross-target checks are supported through
`target.related`, not through infrastructure leakage.

## Registry and Extensibility

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

## Rule Independence

Rules do not consume other rules' outputs. Any shared analysis needed by multiple
rules must be computed once in extraction or target assembly and exposed as explicit
facts on `LintTarget`.

## Configuration Models

Configuration is split by concern. Loading raw config is infrastructure work;
resolving policy is application work.

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

## Ambiguous Guide Policies

Guide phrases such as "non-trivial", "when useful", and "top-level API entry point"
must not be left implicit. They are resolved through named policy options such as:

- `missing-callable-docstring.include_test_functions`
- `missing-callable-docstring.include_private_helpers`
- `missing-returns-section.simple_property_requires_returns`
- `missing-raises-section.contract_exception_allowlist`
- `missing-module-inventory.inventory_threshold`
- `examples-in-non-entry-module.api_entry_modules`
- `trivial-dunder-docstring.trivial_dunder_allowlist`

## Extensibility

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
