"""Tests for glossa.domain.fixes."""

from __future__ import annotations

import pytest

from glossa.application.contracts import DocstringEdit, EditKind, FixPlan, SourceRef
from glossa.domain.fixes import apply_edits_to_body, detect_conflicts, edits_overlap
from glossa.domain.models import DocstringSpan


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _span(start: int, end: int) -> DocstringSpan:
    return DocstringSpan(start_offset=start, end_offset=end)


def _edit(
    kind: EditKind,
    span: DocstringSpan | None,
    text: str = "",
    anchor: str = "",
) -> DocstringEdit:
    return DocstringEdit(kind=kind, span=span, anchor=anchor, text=text)


def _plan(*edits: DocstringEdit) -> FixPlan:
    ref = SourceRef(source_id="test.py", symbol_path=("foo",))
    return FixPlan(
        description="test plan",
        target=ref,
        edits=tuple(edits),
        affected_rules=("D100",),
    )


# ---------------------------------------------------------------------------
# edits_overlap
# ---------------------------------------------------------------------------


def test_edits_no_overlap() -> None:
    """Two edits with non-overlapping spans do not overlap."""
    a = _edit(EditKind.REPLACE, _span(0, 5))
    b = _edit(EditKind.REPLACE, _span(5, 10))
    assert edits_overlap(a, b) is False


def test_edits_overlap() -> None:
    """Two edits whose spans share at least one character position overlap."""
    a = _edit(EditKind.REPLACE, _span(0, 6))
    b = _edit(EditKind.REPLACE, _span(3, 9))
    assert edits_overlap(a, b) is True


def test_edits_none_span() -> None:
    """An edit with span=None never overlaps with anything."""
    a = _edit(EditKind.INSERT, None, text="hello")
    b = _edit(EditKind.REPLACE, _span(0, 10))
    assert edits_overlap(a, b) is False
    assert edits_overlap(b, a) is False
    assert edits_overlap(a, a) is False


# ---------------------------------------------------------------------------
# detect_conflicts
# ---------------------------------------------------------------------------


def test_detect_conflicts_no_conflicts() -> None:
    """All plans are accepted when none of their edits overlap."""
    plan_a = _plan(_edit(EditKind.REPLACE, _span(0, 5), text="X"))
    plan_b = _plan(_edit(EditKind.REPLACE, _span(5, 10), text="Y"))

    accepted, rejected = detect_conflicts((plan_a, plan_b))

    assert accepted == (plan_a, plan_b)
    assert rejected == ()


def test_detect_conflicts_with_overlap() -> None:
    """A later plan is rejected if any of its edits overlap with an accepted plan."""
    plan_a = _plan(_edit(EditKind.REPLACE, _span(0, 10), text="X"))
    plan_b = _plan(_edit(EditKind.REPLACE, _span(3, 8), text="Y"))

    accepted, rejected = detect_conflicts((plan_a, plan_b))

    assert accepted == (plan_a,)
    assert rejected == (plan_b,)


# ---------------------------------------------------------------------------
# apply_edits_to_body
# ---------------------------------------------------------------------------


def test_apply_replace() -> None:
    """REPLACE edit substitutes the target character range with new text."""
    body = "Hello, world!"
    # Replace "world" (offsets 7-12)
    edit = _edit(EditKind.REPLACE, _span(7, 12), text="Python")
    result = apply_edits_to_body(body, (edit,))
    assert result == "Hello, Python!"


def test_apply_delete() -> None:
    """DELETE edit removes the target character range without inserting anything."""
    body = "Hello, world!"
    # Delete ", world" (offsets 5-12)
    edit = _edit(EditKind.DELETE, _span(5, 12))
    result = apply_edits_to_body(body, (edit,))
    assert result == "Hello!"


def test_apply_insert() -> None:
    """INSERT edit at a zero-width span position inserts text without removing anything."""
    body = "Hello world!"
    # Insert ", " between "Hello" and " world" at offset 5 (zero-width span)
    edit = _edit(EditKind.INSERT, _span(5, 5), text=",")
    result = apply_edits_to_body(body, (edit,))
    assert result == "Hello, world!"
