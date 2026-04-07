# Domain Models

The domain keeps both a lossless syntax-preserving model for safe edit planning and
a semantic model for rule evaluation. Both views are immutable and share
docstring-local spans. Duplicate or malformed sections are preserved rather than
normalized away.

## Lossless Docstring Model

```python
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
```

`DocstringSpan` values are relative to `raw_body`, not to filesystem coordinates. This
keeps the domain pure while still supporting precise edits.

## Semantic Docstring Model

```python
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
    name: str | None            # None for Returns/Yields entries
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
    kind: str
    message: str
    span: DocstringSpan | None

SectionNode = TypedSection | ProseSection | InventorySection | SeeAlsoSection | UnknownSection

@dataclass(frozen=True)
class ParsedDocstring:
    syntax: DocstringSyntax
    summary: Summary | None
    deprecation: DeprecationDirective | None
    extended_description_lines: tuple[str, ...]
    sections: tuple[SectionNode, ...]
    parse_issues: tuple[ParseIssue, ...]
```

## Model Invariants

- All containers are tuples or immutable mappings.
- Section order is preserved exactly as written.
- Duplicate sections are preserved as separate nodes.
- Unknown headers are preserved as `UnknownSection`.
- Malformed but recoverable content becomes `ParseIssue`, not silent normalization.
