"""Foundational identification, classification, and severity types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    CONVENTION = "convention"
