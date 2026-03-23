"""Rule system for docstring linting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from glossa.application.contracts import (
        Diagnostic,
        LintTarget,
        Severity,
        TargetKind,
    )
    from glossa.application.policy import ResolvedRulePolicy


@dataclass(frozen=True)
class RuleMetadata:
    code: str
    description: str
    default_severity: Severity
    applies_to: frozenset[TargetKind]
    fixable: bool


@dataclass(frozen=True)
class RuleContext:
    policy: ResolvedRulePolicy
    style: Literal["numpy"] = "numpy"


class Rule(Protocol):
    metadata: RuleMetadata

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        ...
