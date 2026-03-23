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
        coverage=("D300", "D301", "D305", "D503"),
    ),
    TraceEntry(
        guide_clause="1.2 Imperative mood and impersonal voice",
        status="enforced",
        coverage=("D200", "D203", "D204"),
    ),
    TraceEntry(
        guide_clause="1.3 Types in typed sections",
        status="enforced",
        coverage=("D400", "D401", "D402", "D403", "D404", "D405"),
    ),
    TraceEntry(
        guide_clause="1.4 Public docstring required",
        status="enforced",
        coverage=("D100", "D101", "D102"),
    ),
    TraceEntry(
        guide_clause="1.4 Constructor params on class",
        status="enforced",
        coverage=("D103", "D110"),
    ),
    TraceEntry(
        guide_clause="1.4 Private/test/special policy",
        status="enforced_via_config",
        coverage=("D102", "D501"),
    ),
    TraceEntry(
        guide_clause="1.4 Trivial property optional",
        status="enforced_via_config",
        coverage=("D102", "D104"),
    ),
    TraceEntry(
        guide_clause="2.2 Module inventory",
        status="enforced",
        coverage=("D108",),
    ),
    TraceEntry(
        guide_clause="2.2 Module See Also",
        status="out_of_scope",
        coverage=("editorial judgment",),
    ),
    TraceEntry(
        guide_clause="2.2 No Examples in non-entry-point",
        status="enforced",
        coverage=("D306",),
    ),
    TraceEntry(
        guide_clause="3.2 Attributes section",
        status="enforced",
        coverage=("D109", "D405"),
    ),
    TraceEntry(
        guide_clause="3.2 Class Examples",
        status="out_of_scope",
        coverage=("editorial judgment",),
    ),
    TraceEntry(
        guide_clause="4.2 Summary period and blank line",
        status="enforced",
        coverage=("D201", "D202"),
    ),
    TraceEntry(
        guide_clause="4.2 Parameters required",
        status="enforced",
        coverage=("D103", "D302", "D303"),
    ),
    TraceEntry(
        guide_clause="4.2 Returns required",
        status="enforced",
        coverage=("D104", "D402", "D403", "D502"),
    ),
    TraceEntry(
        guide_clause="4.2 Raises for public exceptions",
        status="enforced",
        coverage=("D106",),
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
        coverage=("D111", "D304"),
    ),
    TraceEntry(
        guide_clause="4.2 Warns",
        status="enforced",
        coverage=("D107",),
    ),
    TraceEntry(
        guide_clause="4.2 Warnings prose section",
        status="enforced",
        coverage=("D305", "D503"),
    ),
    TraceEntry(
        guide_clause="5.2 Simple properties",
        status="enforced",
        coverage=("D200", "D104"),
    ),
    TraceEntry(
        guide_clause="6 Inline comments",
        status="out_of_scope",
        coverage=("non-docstring analysis",),
    ),
    TraceEntry(
        guide_clause="7 Empty docstrings",
        status="enforced",
        coverage=("D500",),
    ),
    TraceEntry(
        guide_clause="7 Trivial dunder docstrings",
        status="enforced",
        coverage=("D501",),
    ),
    TraceEntry(
        guide_clause="7 RST directives vs NumPy sections",
        status="enforced",
        coverage=("D305", "D503"),
    ),
    TraceEntry(
        guide_clause="7 Markdown in docstrings",
        status="enforced",
        coverage=("D205",),
    ),
    TraceEntry(
        guide_clause="7 First-person voice",
        status="enforced",
        coverage=("D203",),
    ),
    TraceEntry(
        guide_clause="7 Redundant Returns None",
        status="enforced",
        coverage=("D502",),
    ),
)


def rules_for_clause(clause: str) -> tuple[str, ...]:
    """Return the rule codes for a given guide clause.

    Parameters
    ----------
    clause : str
        The guide clause string to look up.

    Returns
    -------
    tuple[str, ...]
        The rule codes associated with the clause, or an empty tuple if the
        clause is not found or is out of scope.
    """
    for entry in TRACEABILITY_MATRIX:
        if entry.guide_clause == clause:
            if entry.status == "out_of_scope":
                return ()
            return entry.coverage
    return ()


def clause_for_rule(code: str) -> tuple[str, ...]:
    """Return all guide clauses that a given rule code covers.

    Parameters
    ----------
    code : str
        The rule code to look up (e.g. "D300").

    Returns
    -------
    tuple[str, ...]
        The guide clause strings whose coverage includes the given rule code.
    """
    return tuple(
        entry.guide_clause
        for entry in TRACEABILITY_MATRIX
        if code in entry.coverage
    )
