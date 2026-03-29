"""Rule system for docstring linting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

from glossa.domain.contracts import (
    Diagnostic,
    ExtractedDocstring,
    FixPlan,
    LintTarget,
    RuleOptionDescriptor,
    RulePolicy,
    Severity,
    TargetKind,
    TextPosition,
    TextSpan,
)
from glossa.domain.models import DocstringSpan

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class RuleMetadata:
    code: str
    description: str
    default_severity: Severity
    applies_to: frozenset[TargetKind]
    fixable: bool
    requires_docstring: bool = True
    requires_signature: bool = False
    option_schema: tuple[RuleOptionDescriptor, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RuleContext:
    policy: RulePolicy
    section_order: tuple[str, ...] = field(default_factory=tuple)


class Rule(Protocol):
    metadata: RuleMetadata

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        ...


# ---------------------------------------------------------------------------
# DocstringSpan → TextSpan conversion
# ---------------------------------------------------------------------------


def _docstring_offset_to_text_position(
    body: str,
    offset: int,
    body_start: TextPosition,
) -> TextPosition:
    text_before = body[:offset]
    newlines = text_before.count("\n")
    if newlines == 0:
        return TextPosition(
            line=body_start.line,
            column=body_start.column + offset,
        )
    last_newline = text_before.rfind("\n")
    col = offset - last_newline - 1
    return TextPosition(line=body_start.line + newlines, column=col)


def _docstring_span_to_text_span(
    span: DocstringSpan,
    raw_doc: ExtractedDocstring,
) -> TextSpan:
    body = raw_doc.body
    start = _docstring_offset_to_text_position(body, span.start_offset, raw_doc.body_span.start)
    end = _docstring_offset_to_text_position(body, span.end_offset, raw_doc.body_span.start)
    return TextSpan(start=start, end=end)


# ---------------------------------------------------------------------------
# Diagnostic factory
# ---------------------------------------------------------------------------


def make_diagnostic(
    rule: Rule,
    target: LintTarget,
    context: RuleContext,
    message: str,
    span: DocstringSpan | TextSpan | None = None,
    fix: FixPlan | None = None,
) -> Diagnostic:
    """Build a Diagnostic with invariants enforced.

    Converts any ``DocstringSpan`` to a file-level ``TextSpan`` using the
    target's raw docstring body span.  ``Diagnostic.span`` is always
    ``TextSpan | None``.
    """
    normalized: TextSpan | None
    if isinstance(span, DocstringSpan):
        raw_doc = target.extracted.docstring
        if raw_doc is not None:
            normalized = _docstring_span_to_text_span(span, raw_doc)
        else:
            normalized = None
    else:
        normalized = span

    return Diagnostic(
        code=rule.metadata.code,
        message=message,
        severity=context.policy.severity,
        target=target.ref,
        span=normalized,
        fix=fix,
    )
