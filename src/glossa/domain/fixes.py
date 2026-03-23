"""Pure overlap detection for edit planning.

This module lives in the domain layer: no I/O, no filesystem access, no ast.
"""

from __future__ import annotations


def intervals_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    """Return True if two half-open intervals [a_start, a_end) and [b_start, b_end) overlap.

    Parameters
    ----------
    a_start : int
        Start of the first interval.
    a_end : int
        End of the first interval (exclusive).
    b_start : int
        Start of the second interval.
    b_end : int
        End of the second interval (exclusive).

    Returns
    -------
    bool
        ``True`` if the intervals share at least one position.
    """
    return a_start < b_end and b_start < a_end
