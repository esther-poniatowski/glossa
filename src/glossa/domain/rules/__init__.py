"""Rule system for docstring linting."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

from glossa.core.contracts import RulePolicy, Severity, TargetKind


# ---------------------------------------------------------------------------
# Shared RST directive scanner
# ---------------------------------------------------------------------------

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

if TYPE_CHECKING:
    from glossa.core.contracts import Diagnostic, LintTarget


@dataclass(frozen=True)
class RuleMetadata:
    code: str
    description: str
    default_severity: Severity
    applies_to: frozenset[TargetKind]
    fixable: bool
    requires_docstring: bool = True
    requires_signature: bool = False


@dataclass(frozen=True)
class RuleContext:
    policy: RulePolicy
    style: Literal["numpy"] = "numpy"


class Rule(Protocol):
    metadata: RuleMetadata

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        ...
