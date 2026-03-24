# Architectural Audit — Glossa

## 1. ARCHITECTURAL VERDICT

**Classification: serviceable but architecturally fragile.**

The codebase successfully implements a four-layer architecture with clean dependency direction, immutable DTOs, explicit protocol boundaries, and a single composition root. The domain layer is pure, the rule system is protocol-based and independently testable, and the fix engine includes proper conflict detection and validation. However, five structural defects introduce inconsistency, implicit contracts, dead extension paths, and duplicated logic that collectively erode the guarantees the architecture is designed to provide. The contracts layer deviates from the design plan by introducing an unspecified fifth architectural layer with an implied circular dependency on the domain. Rule invocations rely on an implicit caller-enforced precondition rather than structural safety. The configuration subsystem exhibits inconsistent pattern-matching semantics that amount to a behavioral bug. These defects do not prevent the system from working today, but they will cause failures under extension, alternative orchestration contexts, or user configuration that exercises the full advertised surface.

The codebase is fundamentally evolvable — the layering, immutability, and protocol design are structurally sound — but targeted remediation of the findings below is required before the architecture can support confident extension.

---

## 2. EXECUTIVE FINDINGS

| # | Title | Severity | Primary Dimension | Secondary Dimensions | Structural Impact | Consequence Over Time |
|---|-------|----------|-------------------|---------------------|-------------------|-----------------------|
| 1 | Per-file-ignores pattern matching is inconsistent with select/ignore | High | Predictability | Configurability | Configuration subsystem advertises wildcard patterns but per-file-ignores silently requires exact match | Users who configure `per_file_ignores` with wildcard patterns like `D1xx` will observe silent failures — rules not suppressed as expected |
| 2 | Contracts placed in unspecified `core` layer with implied circular domain dependency | High | Separation of Concerns | Modularity | Design plan specifies four layers; implementation introduces a fifth (`core/`) whose contracts reference domain types at type-check time | Layer boundary ambiguity propagates to every module that imports contracts; adding domain-aware contract types in `core` blurs the extraction/parsing boundary |
| 3 | Rules assume non-None docstring without structural guard | High | Robustness | Predictability | Multiple rules access `target.docstring.*` without null checks, relying on orchestration-enforced `requires_docstring` gating | Any caller invoking `rule.evaluate()` outside the linting orchestration loop will trigger `AttributeError`; the Rule protocol contract is weaker than it appears |
| 4 | Anchor field in `DocstringEdit` is structurally inert | Medium | Extensibility | Predictability | `DocstringEdit.anchor` is populated by every rule but never consumed by the fix engine; anchor-only edits are rejected at runtime | The fix system cannot support insertion-by-semantic-anchor (the design plan's intended extension path for complex edits); the contract field misleads both rule authors and future maintainers |
| 5 | Section node types lack formal shared protocol | Medium | Predictability | Modularity | Five section model types duck-type `section_title`, `body_text_lines`, `canonical_position` without a shared protocol or base | Rules and formatters must use `isinstance` dispatch to distinguish sections, and no static analysis tool can verify that all section types satisfy the implicit contract |
| 6 | Duplicated parameter filtering logic across three rule modules | Medium | Redundancy | Modularity | `self`/`cls` exclusion implemented independently in `presence.py`, `structure.py`, and `typed_entries.py` with incompatible shapes | Adding a new exclusion (e.g., for `*args`/`**kwargs` in specific contexts) requires parallel edits in three locations; divergence risk increases with each rule addition |
| 7 | `_check_typed_entries` uses boolean-mode dual dispatch with unused parameters | Medium | Flexibility | Predictability | One function serves both "check missing type" and "check mismatch type" via boolean flags; callers always set one flag true and pass dummy values for the other path | The function's contract is overloaded and underspecified — `mismatch_message_fn=None` when `check_mismatch=False` means a call-site error produces a runtime crash rather than a type error |
| 8 | Rule factories use stringly-typed attribute access | Medium | Predictability | Robustness | `_make_missing_section_rule` and `_make_missing_fact_section_rule` use `getattr(target.signature, signature_field)` and `getattr(target, fact_attr)` | String-based field access bypasses static analysis, autocomplete, and rename refactoring; a typo in a factory call produces a silent `AttributeError` at rule evaluation time |

---

## 3. DETAILED FINDINGS

## Per-file-ignores Pattern Matching Is Inconsistent With Select/Ignore

- **Severity:** High
- **Primary dimension:** Predictability
- **Secondary dimensions:** Configurability
- **Location:** `src/glossa/application/policy.py:120-124`
- **Symptom:** `rules.select` and `rules.ignore` use `matches_pattern()` (which supports wildcard patterns like `D1xx`), but `per_file_ignores` compares rule codes with `rule_code in ignored_codes` — an exact string match.
- **Violation:** The same configuration model (`RuleSelection`) contains three fields that accept rule code patterns, but two of them resolve wildcards while the third silently requires exact codes.
- **Principle:** Predictability — a configuration contract must behave uniformly across all fields that accept the same value domain.
- **Root cause:** `per_file_ignores` code matching was implemented as a direct `in` check without routing through `matches_pattern()`, creating an asymmetry invisible at the configuration boundary.
- **Blast radius:** Any user configuring `per_file_ignores` with wildcard patterns (e.g., `"tests/**.py": ["D1xx"]`) will observe that rules are not suppressed. The bug is silent — no error is raised.
- **Future break scenario:** A user migrates rules from `ignore` (which works with `D1xx`) to `per_file_ignores` (which doesn't) and discovers that suppression silently stopped working.
- **Impact:** Configuration subsystem's advertised behavior is incorrect for one of its three rule-pattern fields.
- **Evidence:**

  `policy.py:116` — select/ignore path uses `matches_pattern`:
  ```python
  selected = any(matches_pattern(rule_code, pattern) for pattern in rules.select)
  ```

  `policy.py:120-123` — per_file_ignores uses raw `in`:
  ```python
  for glob_pattern, ignored_codes in rules.per_file_ignores.items():
      if matches_file_pattern(source_id, glob_pattern):
          if rule_code in ignored_codes:
  ```

- **Remediation:** Route per-file-ignores code matching through `matches_pattern()`:
  ```python
  if any(matches_pattern(rule_code, code) for code in ignored_codes):
  ```
- **Why this remediation is the correct abstraction level:** The fix requires no new abstractions — only consistent use of the existing `matches_pattern` function that already handles the wildcard semantics. The inconsistency is a local oversight, not a design gap.
- **Migration priority:** immediately

---

## Contracts Placed in Unspecified `core` Layer With Implied Circular Domain Dependency

- **Severity:** High
- **Primary dimension:** Separation of Concerns
- **Secondary dimensions:** Modularity
- **Location:** `src/glossa/core/contracts.py:10-11`, `src/glossa/core/__init__.py`
- **Symptom:** The design plan specifies contracts live in `application/contracts.py`. The implementation places them in `core/contracts.py`, a layer not described in the design plan or design principles.
- **Violation:** `core/contracts.py` imports domain types under `TYPE_CHECKING`:
  ```python
  if TYPE_CHECKING:
      from glossa.domain.models import DocstringSpan, ParsedDocstring
  ```
  Meanwhile, domain modules (`domain/rules/*.py`, `domain/models.py`) import from `glossa.core.contracts`. This creates a conceptual bidirectional dependency between `core` and `domain`.
- **Principle:** Separation of Concerns — each layer must have a clear owner and unidirectional dependency flow.
- **Root cause:** Contracts that serve different boundaries (infrastructure→application and application→domain) were collapsed into a single module in an unspecified layer. `LintTarget` (which requires `ParsedDocstring`, a domain type) and `ExtractedTarget` (which is infrastructure-facing) coexist in the same module, collapsing the extraction/parsing boundary the design plan carefully defines.
- **Blast radius:** Every source file in the codebase imports from `glossa.core.contracts`. The implied circular dependency means that any change to the domain model's `ParsedDocstring` or `DocstringSpan` structurally affects the contracts layer, which in turn affects infrastructure, the opposite of the intended dependency direction.
- **Future break scenario:** Adding a new domain model type that contracts need to reference widens the `TYPE_CHECKING` import set, further entangling the layers. A developer unfamiliar with the codebase will reasonably assume `core` is the innermost layer (it's named `core`) and add domain logic there.
- **Impact:** The four-layer architecture's guarantees are weakened by a fifth, unspecified layer that holds both infrastructure-facing and domain-aware types.
- **Evidence:**

  `core/contracts.py:10-11`:
  ```python
  if TYPE_CHECKING:
      from glossa.domain.models import DocstringSpan, ParsedDocstring
  ```

  `domain/rules/__init__.py:8-16` imports from `core`:
  ```python
  from glossa.core.contracts import (Diagnostic, FixPlan, LintTarget, ...)
  ```

- **Remediation:** Split the contracts module along the extraction/parsing boundary as the design plan specifies: (1) move infrastructure-facing DTOs (`ExtractedTarget`, `ExtractedDocstring`, `ParameterFact`, etc.) to `application/contracts.py`; (2) move domain-consuming types (`LintTarget`, `Diagnostic`, `FixPlan`) that reference `ParsedDocstring` to a separate application module or keep them in contracts with the import now pointing inward correctly; (3) remove the `core/` package. Shared value objects (`SourceRef`, `TextPosition`, `TargetKind`, etc.) that have no domain dependency can remain in an application-level shared module.
- **Why this remediation is the correct abstraction level:** This is a boundary realignment, not an abstraction change. The contracts already exist; they need to be placed on the correct side of the extraction/parsing divide.
- **Migration priority:** before adding features

---

## Rules Assume Non-None Docstring Without Structural Guard

- **Severity:** High
- **Primary dimension:** Robustness
- **Secondary dimensions:** Predictability
- **Location:** `src/glossa/domain/rules/presence.py:102,142`, `src/glossa/domain/rules/prose.py:79,117,191`, `src/glossa/domain/rules/structure.py:93,148`, `src/glossa/domain/rules/anti_patterns.py:104,145,206`
- **Symptom:** The majority of rule `evaluate()` methods access `target.docstring.summary`, `target.docstring.syntax`, `target.docstring.sections`, `target.docstring.has_typed_section()`, etc. without checking whether `target.docstring` is `None`. The linting orchestration in `linting.py:87-88` filters out targets with `None` docstrings before dispatching to rules with `requires_docstring=True`, but this invariant is invisible to the rule contract.
- **Violation:** The `Rule` protocol's `evaluate(target: LintTarget, context: RuleContext)` signature does not encode that `target.docstring` is guaranteed non-None. The safety guarantee exists only as an implicit orchestration-layer convention.
- **Principle:** Robustness — preconditions must be structurally enforceable, not dependent on caller discipline.
- **Root cause:** The `requires_docstring` flag on `RuleMetadata` is a hint to the orchestrator, not a structural guarantee. The `LintTarget` type always declares `docstring: ParsedDocstring | None`, so every rule implementation must either trust the orchestrator or add its own guard. Currently, most trust the orchestrator silently.
- **Blast radius:** 20+ rule `evaluate()` methods across 5 modules. Any direct call to `rule.evaluate()` outside the `analyze_file` loop — such as in tests, REPL exploration, future alternative orchestrators, or IDE integration — will crash with `AttributeError: 'NoneType' object has no attribute 'summary'`.
- **Future break scenario:** A contributor writes a test calling `D201().evaluate(target, context)` with a `LintTarget` where `docstring=None`, which is a perfectly valid `LintTarget` value. The test crashes, and the contributor assumes the rule is broken.
- **Impact:** The Rule protocol's contract is weaker than the implementation assumes — it is safe to call only through one specific caller.
- **Evidence:**

  `presence.py:102` (inside `_make_missing_section_rule`):
  ```python
  if not target.docstring.has_typed_section(section_kind):
  ```

  `prose.py:79` (D200):
  ```python
  summary = target.docstring.summary
  ```

  `structure.py:93` (D300):
  ```python
  docstring = target.docstring
  raw_body = docstring.syntax.raw_body
  ```

- **Remediation:** Introduce a `DocstringLintTarget` narrowed type (a frozen dataclass with `docstring: ParsedDocstring` non-optional) and have rules that require a docstring accept `DocstringLintTarget` instead of `LintTarget`. The orchestrator constructs `DocstringLintTarget` from `LintTarget` only when the docstring is present and passes that to rules with `requires_docstring=True`. Alternatively, if introducing a new type is too invasive at this stage, each rule that accesses `target.docstring` should add an explicit early-return guard (`if target.docstring is None: return ()`). The guard approach is simpler but doesn't improve the type-level contract.
- **Why this remediation is the correct abstraction level:** A narrowed input type eliminates the class of error at the type boundary rather than relying on runtime checks scattered across 20+ methods. The guard approach is a valid stopgap if the type change is deferred.
- **Migration priority:** before adding features

---

## Anchor Field in `DocstringEdit` Is Structurally Inert

- **Severity:** Medium
- **Primary dimension:** Extensibility
- **Secondary dimensions:** Predictability
- **Location:** `src/glossa/core/contracts.py:193-197` (DocstringEdit), `src/glossa/application/fixing.py:183-186`
- **Symptom:** `DocstringEdit` has an `anchor: str` field that is populated by every rule that produces fix plans (e.g., `prose.py:133` sets `anchor=""`, `typed_entries.py:141` sets `anchor=f"{anchor_prefix}:{entry.name}"`). However, the fix engine in `fixing.py:183-185` explicitly rejects any edit where `span` is `None`, which is the condition under which `anchor` would be the primary locator:
  ```python
  if edit.span is None:
      raise ValueError(
          f"Unsupported anchor-based edit {edit.anchor!r}; "
          f"explicit docstring spans are required."
      )
  ```
- **Violation:** The contract declares a field and rules populate it, but no consumer reads it. The fix engine's rejection path makes anchor-based edits a dead code path.
- **Principle:** Extensibility — extension seams must be functional, not merely declared. A contract field that is always ignored is worse than its absence because it misleads authors into believing it is consumed.
- **Root cause:** The design plan (section 5) describes `anchor` as supporting semantic anchors like `"Parameters:after_header"` for insertion-based edits. The fix engine was implemented with span-based resolution only, leaving anchor resolution unimplemented.
- **Blast radius:** Every rule that produces a `FixPlan` populates `anchor` values that are discarded. Future rule authors will populate `anchor` expecting it to work, only to discover at runtime that span-only edits are supported.
- **Future break scenario:** A contributor implements an insertion rule (e.g., "add missing Parameters section") that cannot easily produce a `DocstringSpan` because the content doesn't yet exist. They populate `anchor="Parameters:after_summary"` with `span=None`, and the fix engine rejects the edit at runtime.
- **Impact:** The advertised extension path for complex edits (insertions, cross-section moves) is blocked.
- **Evidence:**

  `contracts.py:196` — anchor field always present:
  ```python
  anchor: str
  ```

  `fixing.py:183-186` — anchor-only edits rejected:
  ```python
  if edit.span is None:
      raise ValueError(...)
  ```

  `prose.py:133` — anchor populated but unused:
  ```python
  anchor="",
  ```

- **Remediation:** Either (a) implement anchor-based edit resolution in `_resolve_fix_plan` so the field serves its design purpose, or (b) remove the `anchor` field from `DocstringEdit` and document that all edits require explicit `DocstringSpan` values until anchor resolution is implemented. Option (a) is architecturally preferable but may be deferred; option (b) preserves honesty of the contract.
- **Why this remediation is the correct abstraction level:** This is a contract honesty issue — either the extension seam works or it should not be advertised. Removing a dead field is simpler than implementing anchor resolution, but the design plan's intent favors implementation.
- **Migration priority:** before adding features

---

## Section Node Types Lack Formal Shared Protocol

- **Severity:** Medium
- **Primary dimension:** Predictability
- **Secondary dimensions:** Modularity
- **Location:** `src/glossa/domain/models.py:88-228`
- **Symptom:** `TypedSection`, `ProseSection`, `InventorySection`, `SeeAlsoSection`, and `UnknownSection` all independently implement `section_title: str`, `body_text_lines: tuple[str, ...]`, and `canonical_position: int | None` as properties. The union type `SectionNode` groups them, but there is no protocol or abstract base class that formally declares the shared interface.
- **Violation:** Rules that iterate over `docstring.sections` must use `isinstance` checks to access type-specific fields (e.g., `entries` on `TypedSection`, `items` on `InventorySection`) and implicitly rely on the duck-typed common properties without any static guarantee.
- **Principle:** Predictability — when multiple types share an interface, that interface must be declared explicitly so that static analysis, autocomplete, and future contributors can verify compliance.
- **Root cause:** The five section types were created as independent frozen dataclasses. The common properties were added to each individually without extracting a shared protocol.
- **Blast radius:** `structure.py:D300` (line 97-98) must exclude `UnknownSection` from underline checks because `UnknownSection` lacks `underline_span` and `title_span` — a structural gap in the shared interface. `structure.py:D301` calls `section.canonical_position` on all sections without a type-level guarantee it exists.
- **Future break scenario:** A contributor adds a new section type (e.g., `ReferencesSection`) and omits one of the three common properties. No static check will catch the omission until a rule crashes at runtime.
- **Impact:** The section model's shared interface is implicit, making the `SectionNode` union weaker than it should be.
- **Evidence:**

  `models.py:97-98` — TypedSection implements `section_title`:
  ```python
  @property
  def section_title(self) -> str:
      return self.kind.value
  ```

  `models.py:179-180` — SeeAlsoSection independently implements same property:
  ```python
  @property
  def section_title(self) -> str:
      return "See Also"
  ```

  `structure.py:97-98` — D300 must exclude UnknownSection because it lacks `underline_span`:
  ```python
  if isinstance(section, UnknownSection):
      continue
  ```

- **Remediation:** Introduce a `SectionProtocol` (using `typing.Protocol`) declaring `section_title`, `body_text_lines`, and `canonical_position`. Optionally introduce a `UnderliningSection` protocol for types that have `title_span` and `underline_span`. Apply the protocol to all five section types. This preserves the frozen-dataclass design while making the shared interface explicit and statically verifiable.
- **Why this remediation is the correct abstraction level:** A protocol is the correct mechanism for declaring a structural interface across independent frozen dataclasses without introducing inheritance or mutability. It adds zero runtime cost.
- **Migration priority:** next refactor cycle

---

## Duplicated Parameter Filtering Logic Across Three Rule Modules

- **Severity:** Medium
- **Primary dimension:** Redundancy
- **Secondary dimensions:** Modularity
- **Location:** `src/glossa/domain/rules/presence.py:23-31`, `src/glossa/domain/rules/structure.py:31-68`, `src/glossa/domain/rules/typed_entries.py:25-49`
- **Symptom:** Three separate rule modules independently implement "filter `self` and `cls` from a target's parameter list," each with a different shape:
  - `presence.py:_documentable_params()` returns `list[str]` of names
  - `structure.py:_EXCLUDED_PARAM_NAMES` + `_signature_param_names()` returns `frozenset[str]` of names
  - `typed_entries.py:_get_signature_params()` returns `tuple[ParameterFact, ...]` of filtered objects

  Additionally, `structure.py` has a separate `_constructor_param_names()` helper, while `presence.py:D103` and `typed_entries.py:_get_signature_params()` independently implement constructor-fallback logic.
- **Violation:** The same invariant ("`self` and `cls` are not documentable parameters") is encoded three times with three different return types and two different constructor-fallback strategies.
- **Principle:** Redundancy — a domain invariant must be encoded once and shared.
- **Root cause:** Each rule module was implemented independently, and the common filtering logic was inlined into per-module helpers rather than extracted to a shared utility.
- **Blast radius:** If the exclusion list changes (e.g., to also exclude `*args` in certain contexts, or to handle `__class_getitem__` parameters), three locations must be updated in parallel. The constructor-fallback logic in `presence.py:D103` and `typed_entries.py:_get_signature_params()` already differs in shape.
- **Future break scenario:** A new rule needs to check documentable parameters and copy-pastes a fourth variant of the filter, introducing subtle divergence.
- **Impact:** Moderate duplication with divergence risk across the rule system's most common operation.
- **Evidence:**

  `presence.py:26-30`:
  ```python
  return [p.name for p in target.signature.parameters if p.name not in ("self", "cls")]
  ```

  `structure.py:31,52-56`:
  ```python
  _EXCLUDED_PARAM_NAMES = frozenset({"self", "cls"})
  ...
  return frozenset(p.name for p in target.signature.parameters if p.name not in _EXCLUDED_PARAM_NAMES)
  ```

  `typed_entries.py:31-34`:
  ```python
  _EXCLUDED = frozenset({"self", "cls"})
  def _filter(params): return tuple(p for p in params if p.name not in _EXCLUDED)
  ```

- **Remediation:** Extract a shared domain-level utility module (e.g., `domain/rules/_parameters.py`) providing:
  - `documentable_param_names(target: LintTarget) -> frozenset[str]` — names only, with constructor fallback
  - `documentable_params(target: LintTarget) -> tuple[ParameterFact, ...]` — full objects, with constructor fallback
  All three rule modules delegate to these functions.
- **Why this remediation is the correct abstraction level:** A shared utility function is the correct mechanism for absorbing repeated filtering with a stable invariant. It is simpler than a domain object or strategy — this is pure deterministic filtering.
- **Migration priority:** next refactor cycle

---

## `_check_typed_entries` Uses Boolean-Mode Dual Dispatch With Unused Parameters

- **Severity:** Medium
- **Primary dimension:** Flexibility
- **Secondary dimensions:** Predictability
- **Location:** `src/glossa/domain/rules/typed_entries.py:121-169`
- **Symptom:** `_check_typed_entries()` accepts `check_missing: bool` and `check_mismatch: bool` to select between two qualitatively different behaviors within a single function. When `check_missing=False`, `missing_message` is set to `""` and `missing_affected` to `()` — unused dummy values. When `check_mismatch=False`, `mismatch_message_fn` is set to `None` — a value that would crash if accidentally used.
- **Violation:** A function that performs two distinct checks based on boolean flags is an overloaded method with hidden modes. The `None`-valued `mismatch_message_fn` is a latent crash waiting to happen if a caller misconfigures the flags.
- **Principle:** Flexibility — distinct behaviors should be expressed through separate functions or composed strategies, not through mode-selecting boolean parameters with dummy values.
- **Root cause:** D400/D401, D402/D403, and D404 share the iteration-over-entries pattern but differ in whether they check for missing types or mismatched types. The shared logic was extracted into one function parameterized by booleans rather than composed from smaller pieces.
- **Blast radius:** Six callers in `typed_entries.py` (D400–D405). Each call site passes 13 parameters, making the function signature hard to read and error-prone.
- **Future break scenario:** A new check type (e.g., "entry description too short") is added by extending the boolean flags to three modes, further overloading the function.
- **Impact:** The function's contract is ambiguous — its behavior depends on a combination of boolean flags and nullable parameters that are only safe in specific combinations.
- **Evidence:**

  `typed_entries.py:243-246` — D400 passes `mismatch_message_fn=None`:
  ```python
  check_mismatch=False,
  missing_message="Parameter is missing a type in the docstring",
  mismatch_message_fn=None,
  ```

  `typed_entries.py:276-277` — D401 passes `missing_message=""`:
  ```python
  check_missing=False,
  ...
  missing_message="",
  ```

- **Remediation:** Split `_check_typed_entries` into two focused functions: `_check_missing_types(...)` and `_check_mismatched_types(...)`. Each accepts only the parameters it needs. D404, which checks both, calls both. The shared entry-iteration logic can be a small helper that both functions invoke, or the iteration can be inlined — it is only 10 lines.
- **Why this remediation is the correct abstraction level:** Splitting a boolean-mode function into two named functions is a direct decomposition — no new abstractions, patterns, or indirections are needed. The resulting functions are narrower, fully typed, and independently understandable.
- **Migration priority:** next refactor cycle

---

## Rule Factories Use Stringly-Typed Attribute Access

- **Severity:** Medium
- **Primary dimension:** Predictability
- **Secondary dimensions:** Robustness
- **Location:** `src/glossa/domain/rules/presence.py:95,133`
- **Symptom:** `_make_missing_section_rule` uses `getattr(target.signature, signature_field)` where `signature_field` is a string like `"returns_value"`. `_make_missing_fact_section_rule` uses `getattr(target, fact_attr)` where `fact_attr` is a string like `"exceptions"`. Both bypass static type checking.
- **Violation:** String-based attribute access on typed domain objects converts a compile-time-verifiable field reference into a runtime lookup. A typo in the factory call (e.g., `signature_field="return_value"` instead of `"returns_value"`) produces an `AttributeError` at rule evaluation time, not at definition time.
- **Principle:** Predictability — field access on typed objects should use direct attribute references or typed accessor functions, not stringly-typed dispatch.
- **Root cause:** The factories were designed to be maximally generic over which field to check, using string parameters instead of callables or typed accessor functions.
- **Blast radius:** Four factory-produced rules (D104, D105, D106, D107). A misspelled field name would surface only when a specific rule evaluates a target with a non-None signature — a condition that may not occur in basic tests.
- **Future break scenario:** A field on `SignatureFacts` is renamed (e.g., `returns_value` → `has_return`). Static analysis catches all direct references but misses the string-based `getattr` calls, leaving D104 silently broken.
- **Impact:** Four rules are insulated from static analysis and rename refactoring.
- **Evidence:**

  `presence.py:95`:
  ```python
  if not getattr(target.signature, signature_field):
  ```

  `presence.py:133`:
  ```python
  facts = getattr(target, fact_attr)
  ```

- **Remediation:** Replace the string parameters with typed callable accessors. For `_make_missing_section_rule`, accept `signature_predicate: Callable[[SignatureFacts], bool]` and call it as `signature_predicate(target.signature)`. For `_make_missing_fact_section_rule`, accept `fact_accessor: Callable[[LintTarget], tuple[...]]`. Callers pass lambdas: `signature_predicate=lambda s: s.returns_value`, `fact_accessor=lambda t: t.exceptions`. This preserves the factory pattern while making field access statically verifiable.
- **Why this remediation is the correct abstraction level:** A callable parameter is the correct replacement for stringly-typed dispatch when the variation is "which field to read." It introduces no new types or indirections — only a typed function parameter replacing a string parameter.
- **Migration priority:** opportunistically
