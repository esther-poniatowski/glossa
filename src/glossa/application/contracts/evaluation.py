"""Types for rule evaluation, diagnostics, and fix planning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, Mapping

from glossa.application.contracts.core import (
    Severity,
    SourceRef,
    TargetKind,
    TextSpan,
    Visibility,
)
from glossa.application.contracts.extraction import (
    AttributeFact,
    ExceptionFact,
    ExtractedDocstring,
    ModuleSymbolFact,
    SignatureFacts,
    WarningFact,
)

if TYPE_CHECKING:
    from glossa.domain.models import DocstringSpan, ParsedDocstring


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
    ref: SourceRef
    kind: TargetKind
    visibility: Visibility
    is_test_target: bool
    docstring: ParsedDocstring | None
    raw_docstring: ExtractedDocstring | None
    signature: SignatureFacts | None
    exceptions: tuple[ExceptionFact, ...]
    warnings: tuple[WarningFact, ...]
    attributes: tuple[AttributeFact, ...]
    module_symbols: tuple[ModuleSymbolFact, ...]
    decorators: tuple[str, ...]
    related: ResolvedRelatedTargets


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
    code: str
    message: str
    severity: Severity
    target: SourceRef
    span: DocstringSpan | TextSpan | None
    fix: FixPlan | None = None
