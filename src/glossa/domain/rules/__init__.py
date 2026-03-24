"""Rule system for docstring linting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

from glossa.application.contracts import (
    Diagnostic,
    FixPlan,
    LintTarget,
    RulePolicy,
    Severity,
    TargetKind,
    TextSpan,
)

if TYPE_CHECKING:
    from glossa.domain.models import DocstringSpan


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


def make_diagnostic(
    rule: Rule,
    target: LintTarget,
    context: RuleContext,
    message: str,
    span: DocstringSpan | TextSpan | None = None,
    fix: FixPlan | None = None,
) -> Diagnostic:
    """Build a Diagnostic with code, severity, and target derived from context.

    This enforces the invariants that ``code`` always matches the rule's
    metadata, ``severity`` always comes from the resolved policy, and
    ``target`` always comes from the lint target's ``ref``.
    """
    return Diagnostic(
        code=rule.metadata.code,
        message=message,
        severity=context.policy.severity,
        target=target.ref,
        span=span,
        fix=fix,
    )
