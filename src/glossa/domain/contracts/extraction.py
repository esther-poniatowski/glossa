"""DTOs produced by infrastructure extraction and consumed by the application layer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from glossa.domain.contracts.core import (
    SourceRef,
    TargetKind,
    TextSpan,
    Visibility,
)


class Confidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExceptionEvidence(Enum):
    RAISE = "raise"
    RERAISE = "reraise"
    DOCUMENTED_CONTRACT = "documented_contract"


@dataclass(frozen=True)
class ExtractedDocstring:
    body: str
    quote: Literal['"""', "'''"]
    string_prefix: str
    indentation: str
    body_span: TextSpan
    literal_span: TextSpan


@dataclass(frozen=True)
class ParameterFact:
    name: str
    annotation: str | None
    default: str | None
    kind: Literal[
        "positional_only",
        "positional_or_keyword",
        "var_positional",
        "keyword_only",
        "var_keyword",
    ]


@dataclass(frozen=True)
class SignatureFacts:
    parameters: tuple[ParameterFact, ...]
    return_annotation: str | None
    returns_value: bool
    yields_value: bool


@dataclass(frozen=True)
class ExceptionFact:
    type_name: str
    evidence: ExceptionEvidence
    confidence: Confidence


@dataclass(frozen=True)
class WarningFact:
    type_name: str
    confidence: Confidence


@dataclass(frozen=True)
class AttributeFact:
    name: str
    annotation: str | None
    defined_in_init: bool
    is_public: bool


@dataclass(frozen=True)
class ModuleSymbolFact:
    name: str
    kind: Literal["class", "function"]
    is_public: bool


@dataclass(frozen=True)
class RelatedTargets:
    parent: SourceRef | None = None
    constructor: SourceRef | None = None
    property_getter: SourceRef | None = None


@dataclass(frozen=True)
class ExtractedTarget:
    ref: SourceRef
    kind: TargetKind
    visibility: Visibility
    is_test_target: bool
    docstring: ExtractedDocstring | None
    signature: SignatureFacts | None
    exceptions: tuple[ExceptionFact, ...]
    warnings: tuple[WarningFact, ...]
    attributes: tuple[AttributeFact, ...]
    module_symbols: tuple[ModuleSymbolFact, ...]
    decorators: tuple[str, ...]
    related: RelatedTargets
    suppression_lines: tuple[str, ...] = ()
