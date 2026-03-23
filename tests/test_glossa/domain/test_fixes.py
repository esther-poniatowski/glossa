"""Tests for glossa.domain.fixes."""

from __future__ import annotations

from glossa.domain.fixes import intervals_overlap


# ---------------------------------------------------------------------------
# intervals_overlap
# ---------------------------------------------------------------------------


def test_no_overlap() -> None:
    """Two adjacent intervals do not overlap."""
    assert intervals_overlap(0, 5, 5, 10) is False


def test_overlap() -> None:
    """Two intervals that share at least one position overlap."""
    assert intervals_overlap(0, 6, 3, 9) is True


def test_contained() -> None:
    """An interval fully contained within another overlaps."""
    assert intervals_overlap(0, 10, 3, 7) is True


def test_zero_width_no_overlap() -> None:
    """A zero-width interval at a boundary does not overlap."""
    assert intervals_overlap(5, 5, 5, 10) is False


def test_symmetry() -> None:
    """Overlap is symmetric."""
    assert intervals_overlap(0, 6, 3, 9) is True
    assert intervals_overlap(3, 9, 0, 6) is True
