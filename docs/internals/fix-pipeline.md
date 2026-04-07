# Diagnostics and Fixes

Diagnostics are pure values. Fixes are grouped, validated edit plans rather than
single line replacements.

```python
class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    CONVENTION = "convention"

@dataclass(frozen=True)
class Diagnostic:
    rule: str
    message: str
    severity: Severity
    target: SourceRef
    span: DocstringSpan | TextSpan | None
    fix: "FixPlan | None" = None

class EditKind(Enum):
    INSERT = "insert"
    REPLACE = "replace"
    DELETE = "delete"

@dataclass(frozen=True)
class DocstringEdit:
    kind: EditKind
    span: DocstringSpan | None
    anchor: str                  # semantic anchor such as "Parameters:after_header"
    text: str

@dataclass(frozen=True)
class FixPlan:
    description: str
    target: SourceRef
    edits: tuple[DocstringEdit, ...]
    affected_rules: tuple[str, ...]
```

## Fix Safety Rules

- Edits are grouped per target docstring.
- Overlapping edits are never auto-merged silently.
- If two fix plans for the same target overlap or have incompatible anchors, the
  application marks them as conflicting and skips auto-application for that target.
- Each accepted fix plan is validated by reparsing the edited Python source,
  re-extracting the changed target, reparsing the docstring, and rerunning the rules
  that produced the fix.
- If validation fails, the file is left unchanged and an operational error is reported.

This strategy supports insertions, deletions, replacements, and multi-site edits while
preserving quote style, string prefix, indentation, and surrounding whitespace.
