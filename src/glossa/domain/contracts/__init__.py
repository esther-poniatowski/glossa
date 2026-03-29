"""Cross-layer DTOs shared across glossa.

This package is owned by the domain layer. Infrastructure constructs
these DTOs; the application orchestrates them; the domain rules consume
them. All types are immutable and free of infrastructure-specific classes
such as ``Path`` or ``ast.AST``.

Sub-modules
-----------
core
    Foundational identification, classification, and severity types.
extraction
    DTOs produced by infrastructure extraction.
evaluation
    Rule evaluation, diagnostic, and fix-planning types.
"""

from glossa.domain.contracts.core import (
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
from glossa.domain.contracts.extraction import (
    AttributeFact,
    Confidence,
    ExceptionEvidence,
    ExceptionFact,
    ExtractedDocstring,
    ExtractedTarget,
    ModuleSymbolFact,
    ParameterFact,
    RelatedTargets,
    SignatureFacts,
    WarningFact,
)
from glossa.domain.contracts.evaluation import (
    Diagnostic,
    DocstringEdit,
    EditKind,
    FixPlan,
    LintTarget,
    RelatedTargetSnapshot,
    ResolvedRelatedTargets,
    RuleOptionDescriptor,
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
    "Confidence",
    "ExceptionEvidence",
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
    "RuleOptionDescriptor",
    "RulePolicy",
]
