from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class TraceEntry:
    guide_clause: str
    status: Literal["enforced", "enforced_via_config", "out_of_scope"]
    coverage: tuple[str, ...]


TRACEABILITY_MATRIX: tuple[TraceEntry, ...] = (
    TraceEntry(
        guide_clause="1.1 NumPy style required",
        status="enforced",
        coverage=("malformed-underline", "section-order", "rst-directive-instead-of-section", "rst-note-warning-directive"),
    ),
    TraceEntry(
        guide_clause="1.2 Imperative mood and impersonal voice",
        status="enforced",
        coverage=("non-imperative-summary", "first-person-voice", "second-person-voice"),
    ),
    TraceEntry(
        guide_clause="1.3 Types in typed sections",
        status="enforced",
        coverage=("missing-param-type", "param-type-mismatch", "missing-return-type", "return-type-mismatch", "yield-type-mismatch", "missing-attribute-type"),
    ),
    TraceEntry(
        guide_clause="1.4 Public docstring required",
        status="enforced",
        coverage=("missing-module-docstring", "missing-class-docstring", "missing-callable-docstring"),
    ),
    TraceEntry(
        guide_clause="1.4 Constructor params on class",
        status="enforced",
        coverage=("missing-parameters-section", "params-in-init-not-class"),
    ),
    TraceEntry(
        guide_clause="1.4 Private/test/special policy",
        status="enforced_via_config",
        coverage=("missing-callable-docstring", "trivial-dunder-docstring"),
    ),
    TraceEntry(
        guide_clause="1.4 Trivial property optional",
        status="enforced_via_config",
        coverage=("missing-callable-docstring", "missing-returns-section"),
    ),
    TraceEntry(
        guide_clause="2.2 Module inventory",
        status="enforced",
        coverage=("missing-module-inventory",),
    ),
    TraceEntry(
        guide_clause="2.2 Module See Also",
        status="out_of_scope",
        coverage=("editorial judgment",),
    ),
    TraceEntry(
        guide_clause="2.2 No Examples in non-entry-point",
        status="enforced",
        coverage=("examples-in-non-entry-module",),
    ),
    TraceEntry(
        guide_clause="3.2 Attributes section",
        status="enforced",
        coverage=("missing-attributes-section", "missing-attribute-type"),
    ),
    TraceEntry(
        guide_clause="3.2 Class Examples",
        status="out_of_scope",
        coverage=("editorial judgment",),
    ),
    TraceEntry(
        guide_clause="4.2 Summary period and blank line",
        status="enforced",
        coverage=("missing-period", "missing-blank-after-summary"),
    ),
    TraceEntry(
        guide_clause="4.2 Parameters required",
        status="enforced",
        coverage=("missing-parameters-section", "undocumented-parameter", "extraneous-parameter"),
    ),
    TraceEntry(
        guide_clause="4.2 Returns required",
        status="enforced",
        coverage=("missing-returns-section", "missing-return-type", "return-type-mismatch", "redundant-returns-none"),
    ),
    TraceEntry(
        guide_clause="4.2 Raises for public exceptions",
        status="enforced",
        coverage=("missing-raises-section",),
    ),
    TraceEntry(
        guide_clause="4.2 See Also",
        status="out_of_scope",
        coverage=("editorial judgment",),
    ),
    TraceEntry(
        guide_clause="4.2 Examples",
        status="out_of_scope",
        coverage=("editorial judgment",),
    ),
    TraceEntry(
        guide_clause="4.2 Notes",
        status="out_of_scope",
        coverage=("editorial judgment",),
    ),
    TraceEntry(
        guide_clause="4.2 Deprecation directive",
        status="enforced",
        coverage=("missing-deprecation-directive", "malformed-deprecation"),
    ),
    TraceEntry(
        guide_clause="4.2 Warns",
        status="enforced",
        coverage=("missing-warns-section",),
    ),
    TraceEntry(
        guide_clause="4.2 Warnings prose section",
        status="enforced",
        coverage=("rst-directive-instead-of-section", "rst-note-warning-directive"),
    ),
    TraceEntry(
        guide_clause="5.2 Simple properties",
        status="enforced",
        coverage=("non-imperative-summary", "missing-returns-section"),
    ),
    TraceEntry(
        guide_clause="6 Inline comments",
        status="out_of_scope",
        coverage=("non-docstring analysis",),
    ),
    TraceEntry(
        guide_clause="7 Empty docstrings",
        status="enforced",
        coverage=("empty-docstring",),
    ),
    TraceEntry(
        guide_clause="7 Trivial dunder docstrings",
        status="enforced",
        coverage=("trivial-dunder-docstring",),
    ),
    TraceEntry(
        guide_clause="7 RST directives vs NumPy sections",
        status="enforced",
        coverage=("rst-directive-instead-of-section", "rst-note-warning-directive"),
    ),
    TraceEntry(
        guide_clause="7 Markdown in docstrings",
        status="enforced",
        coverage=("markdown-in-docstring",),
    ),
    TraceEntry(
        guide_clause="7 First-person voice",
        status="enforced",
        coverage=("first-person-voice",),
    ),
    TraceEntry(
        guide_clause="7 Redundant Returns None",
        status="enforced",
        coverage=("redundant-returns-none",),
    ),
)


def rules_for_clause(clause: str) -> tuple[str, ...]:
    """Return the rule names for a given guide clause."""
    for entry in TRACEABILITY_MATRIX:
        if entry.guide_clause == clause:
            if entry.status == "out_of_scope":
                return ()
            return entry.coverage
    return ()


def validate_matrix_codes(registered_names: frozenset[str]) -> tuple[str, ...]:
    """Return matrix rule names not present in *registered_names*."""
    matrix_names: set[str] = set()
    for entry in TRACEABILITY_MATRIX:
        if entry.status == "out_of_scope":
            continue
        for name in entry.coverage:
            matrix_names.add(name)
    return tuple(sorted(matrix_names - registered_names))


def clause_for_rule(name: str) -> tuple[str, ...]:
    """Return all guide clauses that a given rule name covers."""
    return tuple(
        entry.guide_clause
        for entry in TRACEABILITY_MATRIX
        if name in entry.coverage
    )
