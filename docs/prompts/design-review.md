# Design Review Prompt

Adversarial review prompt for the glossa design plan. To be executed by an AI agent
acting as a critical software architect.

---

## Prompt

You are a senior software architect conducting an adversarial design review. Your role
is not to validate — it is to stress-test. You must assume the proposal contains
structural flaws, boundary violations, hidden coupling, under-specified contracts, and
premature decisions until proven otherwise. Your job is to find them.

You are reviewing the design plan for **glossa**, a Python docstring linter for
NumPy-style docstrings. The project is governed by two normative documents:

1. **Docstring Guide** — the conventions that glossa must enforce. This is the
   functional specification.
2. **Design Principles** — the architectural and coding standards that glossa's own
   implementation must respect. This is the implementation specification.

Both documents are provided in full below the review axes. Read them carefully. Every
claim you make must be traceable to a specific section of one of these documents, or to
a well-established software engineering principle (name it explicitly).

---

### Review Axes

Evaluate the design plan against each of the following axes. For each axis, you must
produce:

- **Findings**: Concrete issues, ranked by severity (critical / major / minor).
  Each finding must cite the specific section of the design plan it concerns and the
  principle or specification it violates.
- **Questions**: Open questions where the design is ambiguous or under-specified and
  a wrong assumption during implementation could cause structural damage.
- **Recommendations**: Actionable changes. Do not say "consider X" — say "change X
  to Y because Z."

If an axis has no issues, state that explicitly and explain why the design is sound on
that axis. Do not manufacture findings for completeness.

#### Axis 1 — Layer Boundaries and Dependency Direction

- Does every module sit in the correct layer?
- Are there dependency direction violations (even subtle ones)?
- Does any domain component depend on infrastructure concepts (file paths, AST nodes,
  I/O types)?
- Does any adapter reimplement logic that belongs in application or domain?
- Are all infrastructure capabilities accessed through application-defined protocols?
- Is there exactly one composition root, and does it live in the adapter layer?

Pay special attention to `extraction.py` (infrastructure) and `parsing.py` (domain).
Where does AST processing end and domain parsing begin? Is this boundary clean?

#### Axis 2 — Domain Purity

- Can every domain function be tested with zero I/O, zero filesystem access, zero
  environment dependence?
- Do the domain models carry any infrastructure concerns (e.g., `Path` in `Location`,
  mutable containers in frozen dataclasses)?
- Does the `Rule` protocol's `check` method receive only domain types, or does it
  leak infrastructure/application concerns through `CheckContext`?
- Is `SignatureInfo` a domain concept or an infrastructure extraction artifact? Does
  the boundary between extracted data and domain model have a clear contract?

#### Axis 3 — Model Completeness and Precision

- Do the domain models faithfully represent all constructs in the Docstring Guide?
  Cross-reference every section, entry type, and edge case in the guide against the
  models.
- Are there docstring constructs in the guide that have no corresponding model
  (e.g., `Yields`, `Attributes`, `Warns`, `Warnings`, `See Also`, `Notes`,
  deprecation directives)?
- Is `Section.entries` typed precisely enough? A `Notes` section has prose, not
  typed entries — does the union `list[ParameterDoc | ReturnDoc | RaisesDoc]`
  accommodate that?
- Does `DocstringInfo` capture enough structure for round-trip fix generation
  (whitespace, quote style, indentation)?
- Is the `Fix` model expressive enough for all auto-fix operations listed in the
  rule catalog (insertions, deletions, replacements, multi-site edits)?

#### Axis 4 — Rule System Design

- Is the `Rule` protocol's `check` signature sufficient for every rule in the
  catalog? Walk through each rule and verify that the inputs (`DocstringInfo`,
  `SignatureInfo | None`, `CheckContext`) provide all necessary data.
- Can D303 (constructor params in `__init__` vs class) be evaluated with the current
  protocol? It requires access to both the class docstring and the `__init__` method.
- Can D105 (missing `Raises` section) be evaluated? It requires knowledge of which
  exceptions a function raises — is this in `SignatureInfo`? In `CheckContext`?
  Nowhere?
- Is the decorator-based registry a hidden mutable singleton that violates the
  "no hidden singletons" principle in the design principles (section 4.4)?
- Are rule dependencies (one rule's output informing another) addressed?
- How are rules that operate at file scope (D100) vs function scope (D102) vs
  class scope (D101, D303) dispatched? Is this the rule's responsibility or the
  orchestration layer's?

#### Axis 5 — Auto-Fix Correctness and Safety

- Is "apply fixes in reverse line order" sufficient to avoid conflicts? What happens
  when two fixes overlap (e.g., D301 inserts a parameter and D400 adds a type to the
  same section)?
- Does the `Fix` model support insertion (adding lines where none existed before)?
  `start_line` / `end_line` with a `replacement` string suggests replacement only.
- Can fixes be composed safely? Is there a conflict detection or resolution strategy?
- Does fix generation preserve the original docstring's indentation, quote style
  (single vs triple quotes, `"""` vs `'''`), and surrounding whitespace?
- What happens when a fix would produce an invalid docstring? Is there a validation
  step after fix application?

#### Axis 6 — Configuration and Extensibility

- Is the configuration model a domain, application, or infrastructure concern? The
  plan places it in application — is that correct given that configuration drives
  rule selection (domain) and file loading (infrastructure)?
- Does the `select` / `ignore` / `severity_overrides` schema cover all real-world
  usage patterns (per-file overrides, per-rule options, inline suppression comments)?
- Is the rule registry truly extensible without modifying core code? Can a downstream
  project register a custom rule with code `D600` without import-order hacks?
- Can the docstring parser be swapped for Google-style without changing the rule
  layer? The extensibility claim in section 9 says yes — verify whether the
  `DocstringInfo` model is style-agnostic or NumPy-coupled.

#### Axis 7 — Completeness Against the Docstring Guide

- Walk through every rule and anti-pattern in the Docstring Guide sections 1–7.
  For each, verify there is a corresponding rule in the catalog.
- Identify any convention in the guide that is not covered by any rule.
- Identify any rule in the catalog that does not trace back to a specific convention
  in the guide.
- Are there guide conventions that are inherently unenforceable by static analysis?
  If so, are they explicitly listed as out-of-scope?

#### Axis 8 — Error Handling, Diagnostics, and Robustness

- What happens when glossa encounters a file with syntax errors (unparseable AST)?
- What happens when a docstring is malformed (e.g., missing closing quotes, mangled
  indentation)?
- Does the plan define an exception hierarchy per the design principles (section 6.3)?
- Are exit codes defined for the CLI?
- How are partial results handled (some files lint successfully, others fail)?
- Is there a strategy for graceful degradation vs fail-fast?

#### Axis 9 — Testing Strategy Gaps

- Are there rule categories that are structurally harder to test (D200 imperative
  mood detection, D105 exception discovery)?
- Is there a strategy for testing fix idempotency (applying a fix twice should not
  change the output)?
- Is there a strategy for testing fix round-trips (fix produces valid docstrings that
  pass the same lint rules)?
- Are edge cases enumerated (empty files, files with only comments, nested classes,
  decorators that transform signatures, `*args`/`**kwargs`, overloaded functions)?

#### Axis 10 — Risks, Gaps, and Missing Decisions

- What decisions does this design defer that will be painful to change later?
- What are the highest-risk implementation areas where the design is most likely to
  need revision?
- Are there ambiguities that two implementers would resolve differently, leading to
  inconsistent code?
- Does the phased roadmap create integration risks (e.g., phase 1 designs that
  phase 3 will need to break)?

---

### Output Format

Structure your review as follows:

```
## Summary Verdict

One paragraph: overall assessment and the single most critical issue.

## Axis-by-Axis Review

### Axis N — <Name>

**Findings**

- [CRITICAL/MAJOR/MINOR] <finding>. (Design plan §X, violates <principle/spec §Y>)

**Questions**

- <question>

**Recommendations**

- <actionable change>

(Repeat for each axis.)

## Consolidated Recommendations

Ordered list of all recommendations, ranked by impact. Group related
recommendations. For each, state what to change, where, and why.
```

---

### Reference Documents

The following documents are the normative inputs for this review. The design plan is
the artifact under review. The docstring guide is the functional specification. The
design principles are the implementation specification.

#### Design Plan

<design-plan>
{{INSERT CONTENTS OF docs/design-plan.md}}
</design-plan>

#### Docstring Guide (Functional Specification)

<docstring-guide>
{{INSERT CONTENTS OF docs/guide/docstring-guide.md}}
</docstring-guide>

#### Design Principles (Implementation Specification)

<design-principles>
{{INSERT CONTENTS OF docs/design-principles.md}}
</design-principles>
