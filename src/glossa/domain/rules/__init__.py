"""Rule system for docstring linting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

from glossa.core.contracts import RulePolicy, Severity, TargetKind

if TYPE_CHECKING:
    from glossa.core.contracts import Diagnostic, LintTarget


@dataclass(frozen=True)
class RuleMetadata:
    code: str
    description: str
    default_severity: Severity
    applies_to: frozenset[TargetKind]
    fixable: bool


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
