# ADR 0001: Architectural Alignment with Reference Python Analysis Tools

**Status**: Accepted

**Date**: 2026-04-06

---

## Context

Glossa is a rule-driven Python docstring linter and auto-fixer. Before committing to
further architectural investment (caching, parallelism, plugin surface changes), the
current design was compared against five established Python analysis tools: mypy, pylint,
pyright, Ruff, and Black. The comparison follows the six-dimension framework documented in
the cross-project architectural synthesis (see References).

The goal is to determine whether glossa's architecture is well-matched to its problem
constraints, and to identify concrete gaps where adopting a proven strategy from the
reference tools would yield measurable improvement.

This comparison is architectural rather than category-nearest. Glossa analyzes docstrings
embedded inside Python source files, not Python source as its primary artifact. "Aligned"
below therefore means "driven by the same underlying constraint at the relevant layer,"
not "internally identical to a full-source linter, type checker, or formatter."

---

## Classification

Glossa is best described as a rule-driven analyzer over **extracted docstring targets**.
At the evaluation layer it is closest to **Family A: rule-driven analyzers with partial
semantics**. It emits diagnostics from a rule set over per-file targets, building enough
semantic context (signatures, exception facts, related targets) to evaluate its rules,
without attempting a global type model or whole-program interpretation. Python ASTs are
supporting infrastructure for extraction, not the domain's primary source representation.

Its fix mode introduces a secondary **Family B** dimension (source-to-source
transformation), though the rewriting scope is much narrower than Black or Ruff
formatter: glossa rewrites only docstring spans within a single file.

---

## Dimension-by-Dimension Assessment

### 1. Evaluation Scheduling

**Current strategy**: File-local bounded-pass analysis (single eager pass per file after
extraction and docstring parsing).

**Reference alignment**: Same family as pylint and Ruff's linter. Mypy and pyright use
staged eager analysis or lazy subcomputations because they maintain globally coherent
type state across modules and scopes. Glossa's rules check docstring structure, coverage,
and type consistency against the function signature. The current design plan keeps
cross-target access limited to related snapshots assembled within the same file
(`parent`, `constructor`, `property_getter`) and explicitly leaves API-topology-driven
inference out of scope.

**Assessment**: Correct for the current rule catalog and non-goals. Bounded-pass
scheduling matches the file-local semantics that glossa actually evaluates. If future
rules require cross-file doc inheritance, symbol re-export reasoning, or API-topology
checks, this decision must be revisited rather than treated as permanent.

### 2. Source Representation

**Current strategy**: Dual model -- a semantic model (`ParsedDocstring`, `TypedSection`,
`Summary`) for rule evaluation, and a lossless model (`DocstringSpan`, `DocstringSyntax`
with byte offsets, quote style, indentation) for edit planning.

**Reference alignment**: Comparable in principle to rewriting tools that maintain both a
semantic view and a lossless editing view, but narrower than Ruff formatter or Black.
Glossa preserves trivia only for extracted docstring spans, while Python-file structure
remains the responsibility of AST extraction. Pure analyzers (mypy, pyright, Ruff
linter) discard edit trivia because they do not need it.

**Assessment**: Well-chosen. The dual model avoids CST overhead while retaining the
precision needed for safe edits. The important alignment is the dual-view constraint, not
the specific implementation shape of Ruff formatter. The architectural invariant should
be stated explicitly: the semantic and lossless docstring views must stay synchronized via
shared docstring-local spans.

### 3. Analysis Composition

**Current strategy**: Explicit rule registry over pre-assembled lint targets. A
`RuleRegistry` holds built-in and plugin rules. The linting orchestrator extracts
targets, parses docstrings, resolves related snapshots and policy, then dispatches each
`LintTarget` to all applicable rules via guard clauses on `RuleMetadata`
(`applies_to`, `requires_docstring`, `requires_signature`). Each rule implements a
`Rule` protocol with an `evaluate()` method.

**Reference alignment**: Comparable to pylint's checker model and Ruff's rule registry at
the registry and selective-dispatch level, not at the traversal level. Glossa's rules do
not participate in a shared AST walk; they operate on already-assembled `LintTarget`
values. The shared infrastructure is extraction, parsing, related-target resolution, and
policy filtering. Glossa's 38 rules across 5 categories are almost entirely independent:
they read from `LintTarget` and `RuleContext` without writing shared mutable state.

**Assessment**: Correct pattern, but the original comparison overstated the similarity.
A shared semantic engine (mypy/pyright-style) would be over-engineering for separable
rules, and a cohesive algorithm (Black-style) does not apply to a diagnostic tool. The
relevant alignment is "registry plus shared precomputation," not "shared traversal
infrastructure."

### 4. Extensibility Boundary

**Current strategy**: Checker registration via a `RuleProvider` protocol discovered
through setuptools entry points.

**Reference alignment**: Maps to pylint's checker registration model -- the middle ground
between mypy's deep semantic plugins and the closed cores of pyright, Ruff, and Black.
The `RuleProvider` protocol is narrower than pylint's `register(linter)` hook: plugins
cannot inject custom traversal phases, formatters, or configuration parsers. This avoids
the coupling the synthesis identifies in pylint's plugin surface, where third-party code
can access and mutate the linter's internal state.

**Assessment**: Right boundary for v1, but it should be described more precisely.
Glossa's extension surface is exactly "more rules over existing `LintTarget` facts."
Plugins cannot add new extraction phases, custom docstring parsers, reporters, or config
loaders. There is no type system requiring deep semantic hooks, and no product
constraint requiring a closed core, but the ADR should make those limitations explicit
rather than implying a more general plugin API.

### 5. Reuse and Invalidation

**Current strategy**: No cross-run caching. Every invocation re-discovers, re-extracts,
re-parses, and re-evaluates all files.

**Reference alignment**: Below all five reference tools. Even pylint caches astroid
parses within a run. Both Ruff and Black implement file-content-hash caching to skip
unchanged files entirely. Mypy and pyright go further with semantic invalidation.

**Assessment**: **Gap identified.** The synthesis generalizes: "optimize invalidation at
the same granularity as the expensive state you are trying to save." Glossa's expensive
asset is work per file, and its per-file analysis is already independent (no cross-file
state). File-level unchanged-file skipping is still the right strategy, but the
invalidation surface is broader than the original sketch:

- `content_hash` covers source changes, including inline suppression comments embedded in
  the file.
- `effective_policy_hash` must cover rule selection, severity overrides, rule options,
  per-file ignores, and suppression settings as resolved for the specific `source_id`.
- `tool_fingerprint` must cover glossa version plus loaded plugin identities/versions and
  any extractor/parser changes that affect diagnostics.

Fine-grained semantic invalidation (mypy-style) or evaluator caching (pyright-style)
would still be over-engineering because glossa has no cross-file dependency graph, but
the cache policy belongs in the application layer and the persisted cache store belongs
behind an application-owned infrastructure port.

### 6. Runtime Platform and Concurrency

**Current strategy**: Sequential Python, no parallelism.

**Reference alignment**: Every reference tool has file-level parallelism: pylint uses
multiprocessing, Black uses asyncio plus process pools, Ruff uses native Rust threads.

**Assessment**: **Secondary gap.** The architecture supports future file-level
parallelism because analysis is independent per file and rule evaluation is side-effect-
free, but the implementation cost is higher than a localized switch. The current service
loop reads files in-process and `AnalyzedFile` retains full `source_text` for later fix
planning, so process-based parallelism would introduce worker lifecycle and result-
serialization boundaries in addition to scheduling. This remains lower priority than
file caching, but only as a profiling-guided judgment: caching removes repeated work on
unchanged files, while parallelism only reduces the wall-clock cost of work that still
must run.

---

## Summary

| Dimension | Current strategy | Reference alignment | Status |
|---|---|---|---|
| Evaluation scheduling | File-local bounded-pass over extracted docstring targets | Pylint, Ruff linter at the per-file rule-evaluation level | Aligned for current scope |
| Source representation | Dual semantic + lossless docstring models | Same dual-view constraint as bounded rewriting tools | Aligned |
| Analysis composition | Rule registry + metadata-based dispatch over `LintTarget` | Registry pattern aligns; shared traversal does not | Aligned with qualification |
| Extensibility boundary | Rule-provider registration (entry points) | Pylint-like registration, intentionally narrower | Aligned with qualification |
| Reuse / invalidation | None | Below all references | Gap |
| Runtime / concurrency | Sequential Python | Below pylint, Ruff, Black | Secondary gap |

Within glossa's current scope, the architecture is broadly well-matched to the decisive
constraints: file-local semantics, separable rules, dual representation for analysis and
editing, and a scoped plugin boundary. The strongest supported gap is cross-run reuse.
The main correction to the original analysis is scope: glossa should be compared to the
reference tools at the level of constraint-driven structure, not as if it shared their
full-source traversal pipelines.

---

## Actionable Changes

### Priority 1: File-level unchanged-file skipping

The highest-impact addition. Glossa's existing file-independence makes file-level reuse
the right target, but the decision logic should be explicit:

- Add an application-owned cache protocol consulted during `GlossaService._analyze_paths`.
- Key entries by `{source_id, content_hash, effective_policy_hash, tool_fingerprint}`.
- Keep hit/miss policy in the application layer and persistence in infrastructure.

This preserves the layered architecture while capturing the full invalidation surface.

### Priority 2: Benchmark-gated file-level parallelism

Enabled by the same structural property (independent per-file analysis) but more invasive
than a localized service tweak. Revisit only after caching lands and cold-run profiling
shows that extraction and rule evaluation still dominate wall time on representative
repositories. If implemented, parallelize at the file-analysis boundary and account for
worker startup plus serialization of analysis results.

### Priority 3: Codify invariants in the design principles

Two architectural invariants surfaced by this analysis are stated inline above but not
yet recorded in the normative `docs/design-principles.md`. Add them there so they
constrain future development rather than remaining buried in a retrospective record:

- The semantic and lossless docstring views must stay synchronized via docstring-local
  spans (relates to §3.4 Lossless and Semantic Models).
- Plugins may contribute rules only; they do not extend extraction, parsing, reporting,
  or configuration loading (relates to §4.2 Plugin Registration).

---

## References

- External comparative synthesis and per-tool analyses covering mypy, pylint, pyright,
  Ruff, and Black were used during drafting, but they are not currently vendored in this
  repository. The comparisons above therefore record the architectural conclusions
  relevant to glossa rather than serving as a standalone evidence archive.
- Glossa design principles: `docs/design-principles.md`
- Glossa design plan: `docs/design-plan.md`
