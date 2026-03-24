"""Cross-layer DTOs shared across glossa.

This package is owned by the application layer. Infrastructure constructs
these DTOs; the domain consumes them. All types are immutable and free
of infrastructure-specific classes such as ``Path`` or ``ast.AST``.

Sub-modules
-----------
core
    Foundational identification, classification, and severity types.
extraction
    DTOs produced by infrastructure extraction.
evaluation
    Rule evaluation, diagnostic, and fix-planning types.
"""

from glossa.application.contracts.core import (
    ALL_TARGET_KINDS,
    CALLABLE_AND_CLASS_KINDS,
    CALLABLE_TARGET_KINDS,
    NON_PROPERTY_KINDS,
    Severity,
    SourceRef,
    TargetKind,
    TextPosition,
    TextSpan,
    Visibility,
)
from glossa.application.contracts.extraction import (
    AttributeFact,
    ExceptionFact,
    ExtractedDocstring,
    ExtractedTarget,
    ModuleSymbolFact,
    ParameterFact,
    RelatedTargets,
    SignatureFacts,
    WarningFact,
)
from glossa.application.contracts.evaluation import (
    Diagnostic,
    DocstringEdit,
    EditKind,
    FixPlan,
    LintTarget,
    RelatedTargetSnapshot,
    ResolvedRelatedTargets,
    RulePolicy,
)

__all__ = [
    "ALL_TARGET_KINDS",
    "CALLABLE_AND_CLASS_KINDS",
    "CALLABLE_TARGET_KINDS",
    "NON_PROPERTY_KINDS",
    "Severity",
    "SourceRef",
    "TargetKind",
    "TextPosition",
    "TextSpan",
    "Visibility",
    "AttributeFact",
    "ExceptionFact",
    "ExtractedDocstring",
    "ExtractedTarget",
    "ModuleSymbolFact",
    "ParameterFact",
    "RelatedTargets",
    "SignatureFacts",
    "WarningFact",
    "Diagnostic",
    "DocstringEdit",
    "EditKind",
    "FixPlan",
    "LintTarget",
    "RelatedTargetSnapshot",
    "ResolvedRelatedTargets",
    "RulePolicy",
]
