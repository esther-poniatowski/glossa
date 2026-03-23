"""Pure edit planning, conflict detection, and fix validation helpers.

This module lives in the domain layer: no I/O, no filesystem access, no ast.
All functions are pure and operate only on in-memory value objects.
"""

from __future__ import annotations

from glossa.domain.models import DocstringSpan
from glossa.application.contracts import DocstringEdit, EditKind, FixPlan


# ---------------------------------------------------------------------------
# Overlap detection
# ---------------------------------------------------------------------------


def edits_overlap(a: DocstringEdit, b: DocstringEdit) -> bool:
    """Check if two edits touch overlapping spans.

    Two edits overlap when both carry a concrete span and those spans share at
    least one character position.  An edit with ``span=None`` (anchor-based
    INSERT) never overlaps with anything, because its insertion point is
    resolved at apply time and does not consume any existing range.

    Parameters
    ----------
    a : DocstringEdit
        The first edit to compare.
    b : DocstringEdit
        The second edit to compare.

    Returns
    -------
    bool
        ``True`` if the edits touch overlapping character ranges, ``False``
        otherwise.
    """
    if a.span is None or b.span is None:
        return False
    # Two half-open intervals [a.start, a.end) and [b.start, b.end) overlap
    # iff a.start < b.end and b.start < a.end.
    return a.span.start_offset < b.span.end_offset and b.span.start_offset < a.span.end_offset


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------


def detect_conflicts(
    plans: tuple[FixPlan, ...],
) -> tuple[tuple[FixPlan, ...], tuple[FixPlan, ...]]:
    """Partition fix plans into accepted and rejected based on edit overlap.

    Given a sequence of fix plans targeting the same docstring, return
    ``(accepted, rejected)`` where the first plan in *plans* always wins: any
    later plan whose edits overlap with an already-accepted plan's edits is
    moved to the rejected bucket.

    Parameters
    ----------
    plans : tuple[FixPlan, ...]
        Candidate fix plans in priority order (first plan has highest
        priority).

    Returns
    -------
    tuple[tuple[FixPlan, ...], tuple[FixPlan, ...]]
        A 2-tuple of ``(accepted, rejected)``.
    """
    accepted: list[FixPlan] = []
    rejected: list[FixPlan] = []

    for candidate in plans:
        conflicts = False
        for existing in accepted:
            for candidate_edit in candidate.edits:
                for existing_edit in existing.edits:
                    if edits_overlap(candidate_edit, existing_edit):
                        conflicts = True
                        break
                if conflicts:
                    break
            if conflicts:
                break

        if conflicts:
            rejected.append(candidate)
        else:
            accepted.append(candidate)

    return tuple(accepted), tuple(rejected)


# ---------------------------------------------------------------------------
# Edit application
# ---------------------------------------------------------------------------


def apply_edits_to_body(body: str, edits: tuple[DocstringEdit, ...]) -> str:
    """Apply non-overlapping edits to a raw docstring body.

    Edits are applied in reverse span order (highest offset first) so that
    earlier offsets remain valid after each substitution.

    Edit semantics
    --------------
    REPLACE
        Replace the character range ``[span.start_offset, span.end_offset)``
        with ``edit.text``.
    DELETE
        Remove the character range ``[span.start_offset, span.end_offset)``.
        Equivalent to REPLACE with an empty replacement string.
    INSERT (``span`` is not ``None``)
        Insert ``edit.text`` at ``span.start_offset``; ``span.end_offset``
        must equal ``span.start_offset`` (zero-width insertion point).
    INSERT (``span`` is ``None``)
        Anchor-based insertion.  Not implemented in v1 — the edit text is
        appended to the body.

    Parameters
    ----------
    body : str
        The raw docstring body to edit.
    edits : tuple[DocstringEdit, ...]
        Non-overlapping edits to apply.  The caller is responsible for
        ensuring there are no conflicts; behaviour is undefined if edits
        overlap.

    Returns
    -------
    str
        The edited docstring body.
    """
    # Separate anchor-based inserts (span=None) from span-based edits.
    anchor_inserts: list[DocstringEdit] = []
    span_edits: list[DocstringEdit] = []

    for edit in edits:
        if edit.span is None:
            anchor_inserts.append(edit)
        else:
            span_edits.append(edit)

    # Apply span-based edits back-to-front to preserve earlier offsets.
    span_edits.sort(key=lambda e: e.span.start_offset, reverse=True)  # type: ignore[union-attr]

    result = body
    for edit in span_edits:
        span: DocstringSpan = edit.span  # type: ignore[assignment]
        start = span.start_offset
        end = span.end_offset

        if edit.kind is EditKind.REPLACE:
            result = result[:start] + edit.text + result[end:]
        elif edit.kind is EditKind.DELETE:
            result = result[:start] + result[end:]
        elif edit.kind is EditKind.INSERT:
            # Zero-width span: insert at start_offset without removing anything.
            result = result[:start] + edit.text + result[start:]

    # v1: anchor-based inserts are simply appended in order.
    for edit in anchor_inserts:
        result = result + edit.text

    return result


# ---------------------------------------------------------------------------
# Fix validation
# ---------------------------------------------------------------------------


def validate_fix_result(
    original_body: str,
    edited_body: str,
    affected_rules: tuple[str, ...],
) -> tuple[bool, tuple[str, ...]]:
    """Validate the result of applying a fix by re-running affected rules.

    Parameters
    ----------
    original_body : str
        The docstring body before edits were applied.
    edited_body : str
        The docstring body after edits were applied.
    affected_rules : tuple[str, ...]
        Rule codes that should be re-checked against the edited body.

    Returns
    -------
    tuple[bool, tuple[str, ...]]
        A 2-tuple of ``(is_valid, remaining_violations)`` where
        ``remaining_violations`` holds the rule codes that still fire after
        the fix.  In the full implementation this would reparse the edited
        body and re-run each affected rule; the current stub always returns
        ``(True, ())``.
    """
    return (True, ())
