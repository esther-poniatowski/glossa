"""Shared RST directive scanning utilities for rule implementations."""

from __future__ import annotations

import re


def scan_rst_directives(
    lines: tuple[str, ...],
    directive_names: frozenset[str],
) -> list[str]:
    """Return directive names matched in *lines* from the given *directive_names* set."""
    pattern = re.compile(
        r"^\s*\.\.\s+(" + "|".join(re.escape(n) for n in directive_names) + r")\s*::",
        re.IGNORECASE,
    )
    found: list[str] = []
    for line in lines:
        m = pattern.match(line)
        if m:
            found.append(m.group(1).lower())
    return found
