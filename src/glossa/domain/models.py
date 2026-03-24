"""Immutable semantic and syntax-preserving docstring models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal, Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# Lossless Docstring Model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DocstringSpan:
    start_offset: int
    end_offset: int


@dataclass(frozen=True)
class DocstringSyntax:
    raw_body: str
    quote: Literal['"""', "'''"]
    string_prefix: str
    indentation: str
    leading_blank_lines: int
    trailing_blank_lines: int


# ---------------------------------------------------------------------------
# Semantic Docstring Model
# ---------------------------------------------------------------------------


class TypedSectionKind(Enum):
    PARAMETERS = "Parameters"
    RETURNS = "Returns"
    YIELDS = "Yields"
    ATTRIBUTES = "Attributes"
    RAISES = "Raises"
    WARNS = "Warns"


class ProseSectionKind(Enum):
    NOTES = "Notes"
    WARNINGS = "Warnings"
    EXAMPLES = "Examples"


class InventorySectionKind(Enum):
    CLASSES = "Classes"
    FUNCTIONS = "Functions"


@dataclass(frozen=True)
class Summary:
    text: str
    span: DocstringSpan


@dataclass(frozen=True)
class TypedEntry:
    name: str | None
    type_text: str | None
    default_text: str | None
    description_lines: tuple[str, ...]
    span: DocstringSpan


# Canonical NumPy section ordering — shared by all consumers.
_SEE_ALSO_KEY = "SeeAlso"

_CANONICAL_POSITIONS: dict[object, int] = {
    TypedSectionKind.PARAMETERS: 0,
    TypedSectionKind.RETURNS: 1,
    TypedSectionKind.YIELDS: 2,
    TypedSectionKind.RAISES: 3,
    TypedSectionKind.WARNS: 4,
    TypedSectionKind.ATTRIBUTES: 5,
    ProseSectionKind.NOTES: 6,
    ProseSectionKind.WARNINGS: 7,
    _SEE_ALSO_KEY: 8,
    ProseSectionKind.EXAMPLES: 9,
    InventorySectionKind.CLASSES: 10,
    InventorySectionKind.FUNCTIONS: 11,
}


@runtime_checkable
class SectionProtocol(Protocol):
    """Shared interface for all docstring section types."""

    @property
    def section_title(self) -> str: ...

    @property
    def body_text_lines(self) -> tuple[str, ...]: ...

    @property
    def canonical_position(self) -> int | None: ...

    @property
    def span(self) -> DocstringSpan: ...


@runtime_checkable
class UnderlinedSectionProtocol(SectionProtocol, Protocol):
    """Section type that has a title underline."""

    @property
    def title_span(self) -> DocstringSpan: ...

    @property
    def underline_span(self) -> DocstringSpan: ...


@dataclass(frozen=True)
class TypedSection:
    kind: TypedSectionKind
    title_span: DocstringSpan
    underline_span: DocstringSpan
    entries: tuple[TypedEntry, ...]
    span: DocstringSpan

    @property
    def section_title(self) -> str:
        return self.kind.value

    @property
    def body_text_lines(self) -> tuple[str, ...]:
        lines: list[str] = []
        for entry in self.entries:
            lines.extend(entry.description_lines)
        return tuple(lines)

    @property
    def canonical_position(self) -> int | None:
        return _CANONICAL_POSITIONS.get(self.kind)


@dataclass(frozen=True)
class ProseSection:
    kind: ProseSectionKind
    title_span: DocstringSpan
    underline_span: DocstringSpan
    body_lines: tuple[str, ...]
    span: DocstringSpan

    @property
    def section_title(self) -> str:
        return self.kind.value

    @property
    def body_text_lines(self) -> tuple[str, ...]:
        return self.body_lines

    @property
    def canonical_position(self) -> int | None:
        return _CANONICAL_POSITIONS.get(self.kind)


@dataclass(frozen=True)
class InventoryItem:
    name: str
    description_lines: tuple[str, ...]
    span: DocstringSpan


@dataclass(frozen=True)
class InventorySection:
    kind: InventorySectionKind
    title_span: DocstringSpan
    underline_span: DocstringSpan
    items: tuple[InventoryItem, ...]
    span: DocstringSpan

    @property
    def section_title(self) -> str:
        return self.kind.value

    @property
    def body_text_lines(self) -> tuple[str, ...]:
        lines: list[str] = []
        for item in self.items:
            lines.extend(item.description_lines)
        return tuple(lines)

    @property
    def canonical_position(self) -> int | None:
        return _CANONICAL_POSITIONS.get(self.kind)


@dataclass(frozen=True)
class SeeAlsoItem:
    name: str
    description_lines: tuple[str, ...]
    span: DocstringSpan


@dataclass(frozen=True)
class SeeAlsoSection:
    title_span: DocstringSpan
    underline_span: DocstringSpan
    items: tuple[SeeAlsoItem, ...]
    span: DocstringSpan

    @property
    def section_title(self) -> str:
        return "See Also"

    @property
    def body_text_lines(self) -> tuple[str, ...]:
        lines: list[str] = []
        for item in self.items:
            lines.extend(item.description_lines)
        return tuple(lines)

    @property
    def canonical_position(self) -> int | None:
        return _CANONICAL_POSITIONS.get(_SEE_ALSO_KEY)


@dataclass(frozen=True)
class DeprecationDirective:
    version: str | None
    body_lines: tuple[str, ...]
    span: DocstringSpan


@dataclass(frozen=True)
class UnknownSection:
    title: str
    title_span: DocstringSpan
    underline_span: DocstringSpan
    body_lines: tuple[str, ...]
    span: DocstringSpan

    @property
    def section_title(self) -> str:
        return self.title

    @property
    def body_text_lines(self) -> tuple[str, ...]:
        return self.body_lines

    @property
    def canonical_position(self) -> int | None:
        return None


@dataclass(frozen=True)
class ParseIssue:
    code: str
    message: str
    span: DocstringSpan | None


SectionNode = (
    TypedSection | ProseSection | InventorySection | SeeAlsoSection | UnknownSection
)


@dataclass(frozen=True)
class ParsedDocstring:
    syntax: DocstringSyntax
    summary: Summary | None
    deprecation: DeprecationDirective | None
    extended_description_lines: tuple[str, ...]
    sections: tuple[SectionNode, ...]
    parse_issues: tuple[ParseIssue, ...]

    def typed_section(self, kind: TypedSectionKind) -> TypedSection | None:
        for section in self.sections:
            if isinstance(section, TypedSection) and section.kind is kind:
                return section
        return None

    def has_typed_section(self, kind: TypedSectionKind) -> bool:
        return self.typed_section(kind) is not None

    def inventory_section(self, kind: InventorySectionKind) -> InventorySection | None:
        for section in self.sections:
            if isinstance(section, InventorySection) and section.kind is kind:
                return section
        return None

    def has_inventory_section(self, kind: InventorySectionKind) -> bool:
        return self.inventory_section(kind) is not None

    def see_also_section(self) -> SeeAlsoSection | None:
        for section in self.sections:
            if isinstance(section, SeeAlsoSection):
                return section
        return None

    def all_text_lines(self) -> tuple[str, ...]:
        parts: list[str] = []
        if self.summary is not None:
            parts.append(self.summary.text)
        parts.extend(self.extended_description_lines)
        for section in self.sections:
            parts.extend(section.body_text_lines)
        return tuple(parts)

    def prose_text_lines(self) -> tuple[str, ...]:
        parts: list[str] = []
        if self.summary is not None:
            parts.append(self.summary.text)
        parts.extend(self.extended_description_lines)
        for section in self.sections:
            if isinstance(section, ProseSection):
                parts.extend(section.body_lines)
        return tuple(parts)
