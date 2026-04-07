# Core Application Contracts

All cross-layer contracts are immutable and free of infrastructure-specific types.
These data structures form the communication protocol between glossa's architectural
layers.

## Shared Value Objects

```python
@dataclass(frozen=True)
class SourceRef:
    source_id: str            # project-relative POSIX path string
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
```

## Extracted Data From Infrastructure

`ExtractedTarget` is the sole output of infrastructure extraction. The application layer
owns the type even though infrastructure constructs instances.

```python
@dataclass(frozen=True)
class ExtractedDocstring:
    body: str
    quote: Literal['"""', "'''"]
    string_prefix: str              # e.g. "", "r"
    indentation: str
    body_span: TextSpan             # body span within source file
    literal_span: TextSpan          # full string literal span within source file

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
```

## Pure Lint Input

The application layer resolves related targets, parses docstrings, and produces the
pure value consumed by rules:

```python
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
    related: Mapping[str, "RelatedTargetSnapshot"]

@dataclass(frozen=True)
class RelatedTargetSnapshot:
    ref: SourceRef
    kind: TargetKind
    docstring: ParsedDocstring | None
    raw_docstring: ExtractedDocstring | None
    signature: SignatureFacts | None
```

Rules see only `LintTarget` plus resolved policy. They never reach into source files
or AST nodes.
