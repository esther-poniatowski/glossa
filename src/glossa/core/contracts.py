"""Layer-neutral DTOs shared across glossa."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal, Mapping

if TYPE_CHECKING:
    from glossa.domain.models import DocstringSpan, ParsedDocstring


@dataclass(frozen=True)
class SourceRef:
    source_id: str
    symbol_path: tuple[str, ...]


@dataclass(frozen=True)
class TextPosition:
    line: int
    column: int


@dataclass(frozen=True)
class TextSpan:
    start: TextPosition
    end: TextPosition


class TargetKind(Enum):
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    PROPERTY = "property"


class Visibility(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"


ALL_TARGET_KINDS: frozenset[TargetKind] = frozenset(TargetKind)
CALLABLE_TARGET_KINDS: frozenset[TargetKind] = frozenset(
    {TargetKind.FUNCTION, TargetKind.METHOD, TargetKind.PROPERTY}
)
NON_PROPERTY_KINDS: frozenset[TargetKind] = ALL_TARGET_KINDS - {TargetKind.PROPERTY}
CALLABLE_AND_CLASS_KINDS: frozenset[TargetKind] = frozenset(
    {TargetKind.FUNCTION, TargetKind.METHOD, TargetKind.CLASS}
)


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
    evidence: Literal["raise", "reraise", "documented_contract"]
    confidence: Literal["high", "medium", "low"]


@dataclass(frozen=True)
class WarningFact:
    type_name: str
    confidence: Literal["high", "medium", "low"]


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


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    CONVENTION = "convention"


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
    anchor: str
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
