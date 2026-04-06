"""Types for rule evaluation, diagnostics, and fix planning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, Callable, Mapping

from glossa.domain.contracts.core import (
    Severity,
    SourceRef,
    TargetKind,
    TextSpan,
    Visibility,
)
from glossa.domain.contracts.extraction import (
    AttributeFact,
    ExceptionFact,
    ExtractedDocstring,
    ExtractedTarget,
    ModuleSymbolFact,
    SignatureFacts,
    WarningFact,
)

if TYPE_CHECKING:
    from glossa.domain.models import DocstringSpan, ParsedDocstring


@dataclass(frozen=True)
class RuleOptionDescriptor:
    """Declares one option that a rule accepts."""

    key: str
    default: object
    validator: Callable[[object, str], object]


@dataclass(frozen=True)
class RelatedTargetSnapshot:
    ref: SourceRef
    kind: TargetKind
    docstring: ParsedDocstring | None
    raw_docstring: ExtractedDocstring | None
    signature: SignatureFacts | None


@dataclass(frozen=True)
class ResolvedRelatedTargets:
    parent: RelatedTargetSnapshot | None = None
    constructor: RelatedTargetSnapshot | None = None
    property_getter: RelatedTargetSnapshot | None = None


@dataclass(frozen=True)
class LintTarget:
    """Enriched target for rule evaluation.

    Wraps an ``ExtractedTarget`` with a parsed docstring and resolved
    related-target snapshots.  Explicitly typed properties forward known
    fields for static type safety.  ``__getattr__`` provides a safety net
    so that new ``ExtractedTarget`` fields are automatically available
    without requiring manual forwarding.
    """

    extracted: ExtractedTarget
    docstring: ParsedDocstring | None
    related: ResolvedRelatedTargets

    def __getattr__(self, name: str) -> object:
        """Delegate unknown attribute access to the underlying ExtractedTarget."""
        return getattr(self.extracted, name)

    @property
    def ref(self) -> SourceRef:
        return self.extracted.ref

    @property
    def kind(self) -> TargetKind:
        return self.extracted.kind

    @property
    def visibility(self) -> Visibility:
        return self.extracted.visibility

    @property
    def is_test_target(self) -> bool:
        return self.extracted.is_test_target

    @property
    def raw_docstring(self) -> ExtractedDocstring | None:
        return self.extracted.docstring

    @property
    def signature(self) -> SignatureFacts | None:
        return self.extracted.signature

    @property
    def exceptions(self) -> tuple[ExceptionFact, ...]:
        return self.extracted.exceptions

    @property
    def warnings(self) -> tuple[WarningFact, ...]:
        return self.extracted.warnings

    @property
    def attributes(self) -> tuple[AttributeFact, ...]:
        return self.extracted.attributes

    @property
    def module_symbols(self) -> tuple[ModuleSymbolFact, ...]:
        return self.extracted.module_symbols

    @property
    def decorators(self) -> tuple[str, ...]:
        return self.extracted.decorators


@dataclass(frozen=True)
class RulePolicy:
    enabled: bool
    severity: Severity
    options: Mapping[str, object] = MappingProxyType({})


class EditKind(Enum):
    INSERT = "insert"
    REPLACE = "replace"
    DELETE = "delete"


@dataclass(frozen=True)
class DocstringEdit:
    kind: EditKind
    span: DocstringSpan | None
    text: str


@dataclass(frozen=True)
class FixPlan:
    description: str
    target: SourceRef
    edits: tuple[DocstringEdit, ...]
    affected_rules: tuple[str, ...]


@dataclass(frozen=True)
class Diagnostic:
    rule: str
    message: str
    severity: Severity
    target: SourceRef
    span: TextSpan | None
    fix: FixPlan | None = None
