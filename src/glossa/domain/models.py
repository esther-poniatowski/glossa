"""Immutable semantic and syntax-preserving docstring models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


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


@dataclass(frozen=True)
class TypedSection:
    kind: TypedSectionKind
    title_span: DocstringSpan
    underline_span: DocstringSpan
    entries: tuple[TypedEntry, ...]
    span: DocstringSpan


@dataclass(frozen=True)
class ProseSection:
    kind: ProseSectionKind
    title_span: DocstringSpan
    underline_span: DocstringSpan
    body_lines: tuple[str, ...]
    span: DocstringSpan


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


@dataclass(frozen=True)
class DeprecationDirective:
    version: str | None
    body_lines: tuple[str, ...]
    span: DocstringSpan


@dataclass(frozen=True)
class UnknownSection:
    title: str
    body_lines: tuple[str, ...]
    span: DocstringSpan


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
