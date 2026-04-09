"""Typed Entry Consistency rules for the glossa docstring linter."""

from __future__ import annotations

import re

from glossa.domain.contracts import (
    CALLABLE_AND_CLASS_KINDS,
    CALLABLE_TARGET_KINDS,
    Diagnostic,
    DocstringEdit,
    EditKind,
    FixPlan,
    LintTarget,
    Severity,
    TargetKind,
)
from glossa.domain.models import TypedEntry, TypedSection, TypedSectionKind
from glossa.domain.rules import RuleContext, RuleMetadata, make_diagnostic
from glossa.domain.rules._parameters import documentable_params

_GROUP = "typed-entries"


def _types_match(
    doc_type: str,
    annotation: str,
    default_text: str | None = None,
    *,
    class_name: str | None = None,
) -> bool:
    """Check whether a docstring type string matches a signature annotation."""
    doc = doc_type.strip()
    ann = annotation.strip()

    # Normalise ``Self`` to the enclosing class name so that, e.g.,
    # ``-> Self`` matches a docstring ``Returns DataComponent``, and
    # ``Self`` in both positions also matches.
    if class_name is not None:
        if ann == "Self":
            ann = class_name
        if doc == "Self":
            doc = class_name

    # Strip forward-reference quotes from annotations.  These may wrap
    # the entire string (``'Node'``) or appear internally
    # (``Optional[Type['Saver']]``).
    ann = ann.replace("'", "").replace('"', "")

    if doc == ann:
        return True

    # Normalize ``str or Path`` to ``str | Path``.
    doc_piped = re.sub(r"\bor\b", "|", doc)
    doc_piped = re.sub(r"\s*\|\s*", " | ", doc_piped).strip()
    ann_piped = re.sub(r"\s*\|\s*", " | ", ann).strip()
    if doc_piped == ann_piped:
        return True

    def _normalize_optional(t: str) -> str:
        if t.startswith("Optional[") and t.endswith("]"):
            inner = t[len("Optional["):-1].strip()
            return f"{inner} | None"
        return t

    def _normalize_union(t: str) -> str:
        if t.startswith("Union[") and t.endswith("]"):
            inner = t[len("Union["):-1]
            # Split on top-level commas, respecting bracket nesting.
            parts: list[str] = []
            depth = 0
            start = 0
            for i, ch in enumerate(inner):
                if ch in "([{":
                    depth += 1
                elif ch in ")]}":
                    depth = max(depth - 1, 0)
                elif ch == "," and depth == 0:
                    parts.append(inner[start:i].strip())
                    start = i + 1
            parts.append(inner[start:].strip())
            return " | ".join(parts)
        return t

    doc_norm = _normalize_union(_normalize_optional(doc_piped))
    ann_norm = _normalize_union(_normalize_optional(ann_piped))

    if doc_norm == ann_norm:
        return True

    # Handle ``, optional`` suffix: either still embedded in doc_type
    # (legacy) or split into the separate *default_text* field.
    is_optional = doc.endswith(", optional") or (
        default_text is not None and default_text.strip().lower() == "optional"
    )
    if is_optional:
        base = doc[: -len(", optional")].strip() if doc.endswith(", optional") else doc
        base_piped = re.sub(r"\bor\b", "|", base)
        base_piped = re.sub(r"\s*\|\s*", " | ", base_piped).strip()
        base_norm = _normalize_optional(base_piped)
        if base_norm == ann_norm:
            return True
        if ann_norm in (f"{base_norm} | None", f"{base_piped} | None"):
            return True
        if base_piped == ann_piped:
            return True

    # Accept docstring type that matches the non-None part of an Optional
    # annotation.  NumPy convention often documents only the base type when
    # a parameter has a ``None`` default.
    if ann_norm.endswith(" | None"):
        ann_base = ann_norm[: -len(" | None")].strip()
        if doc_norm == ann_base:
            return True

    return False


def _entry_with_type(entry: TypedEntry, type_text: str) -> str:
    """Render a TypedEntry header line with the given type substituted or added."""
    if entry.name is not None:
        return f"{entry.name} : {type_text}"
    return type_text


def _make_entry_fix(
    target: LintTarget,
    entry: TypedEntry,
    annotation: str,
    description: str,
    affected_rules: tuple[str, ...],
) -> FixPlan:
    """Build a FixPlan that replaces an entry's header with the corrected type."""
    return FixPlan(
        description=description,
        target=target.ref,
        edits=(
            DocstringEdit(
                kind=EditKind.REPLACE,
                span=entry.span,
                text=_entry_with_type(entry, annotation),
            ),
        ),
        affected_rules=affected_rules,
    )


# ---------------------------------------------------------------------------
# Shared typed-entry consistency checker
# ---------------------------------------------------------------------------


def _check_missing_types(
    rule,
    target: LintTarget,
    context: RuleContext,
    section_kind: TypedSectionKind,
    entries_with_annotation: list[tuple[TypedEntry, str]],
    message: str,
    affected_rules: tuple[str, ...],
) -> tuple[Diagnostic, ...]:
    """Check for entries that are missing a type annotation."""
    diagnostics: list[Diagnostic] = []

    for entry, annotation in entries_with_annotation:
        if entry.type_text is not None:
            continue
        if entry.name is not None:
            desc = f"Add type '{annotation}' to parameter '{entry.name}'"
        else:
            desc = f"Add type '{annotation}' to {section_kind.value} entry"
        fix = _make_entry_fix(target, entry, annotation, desc, affected_rules)
        diagnostics.append(
            make_diagnostic(rule, target, context, message, span=entry.span, fix=fix)
        )

    return tuple(diagnostics)


def _enclosing_class_name(target: LintTarget) -> str | None:
    """Return the enclosing class name for a method or class target."""
    path = target.ref.symbol_path
    if target.kind is TargetKind.CLASS:
        return path[-1] if path else None
    if target.kind in (TargetKind.METHOD, TargetKind.PROPERTY) and len(path) >= 2:
        return path[-2]
    return None


def _check_mismatched_types(
    rule,
    target: LintTarget,
    context: RuleContext,
    entries_with_annotation: list[tuple[TypedEntry, str]],
    message_fn,
    affected_rules: tuple[str, ...],
) -> tuple[Diagnostic, ...]:
    """Check for entries whose type does not match the annotation."""
    diagnostics: list[Diagnostic] = []
    class_name = _enclosing_class_name(target)

    for entry, annotation in entries_with_annotation:
        if entry.type_text is None:
            continue
        if _types_match(entry.type_text, annotation, default_text=entry.default_text, class_name=class_name):
            continue
        if entry.name is not None:
            desc = f"Replace type '{entry.type_text}' with '{annotation}' for parameter '{entry.name}'"
        else:
            desc = f"Replace type '{entry.type_text}' with '{annotation}'"
        fix = _make_entry_fix(target, entry, annotation, desc, affected_rules)
        diagnostics.append(
            make_diagnostic(
                rule, target, context,
                message_fn(entry, annotation),
                span=entry.span,
                fix=fix,
            )
        )

    return tuple(diagnostics)


# ---------------------------------------------------------------------------
# Helpers for section + annotation pairing
# ---------------------------------------------------------------------------


def _param_entries_with_annotation(target: LintTarget) -> list[tuple[TypedEntry, str]] | None:
    """Return (entry, annotation) pairs for Parameters section entries."""
    if target.docstring is None:
        return None
    params_section = target.docstring.typed_section(TypedSectionKind.PARAMETERS)
    if params_section is None:
        return None

    sig_params = {p.name: p for p in documentable_params(target)}
    result: list[tuple[TypedEntry, str]] = []
    for entry in params_section.entries:
        if entry.name is None:
            continue
        # Strip leading ``*``/``**`` so ``**kwargs`` matches the bare name.
        bare_name = entry.name.lstrip("*")
        sig_param = sig_params.get(bare_name)
        if sig_param is None or sig_param.annotation is None:
            continue
        result.append((entry, sig_param.annotation))
    return result if result else None


_GENERATOR_RE = re.compile(
    r"^(?:collections\.abc\.)?"
    r"(?:Async)?(?:Generator|Iterator)\[(.+)\]$"
)


def _extract_yield_type(annotation: str) -> str:
    """Extract the yield type from Generator/Iterator annotations.

    ``Generator[YieldType, SendType, ReturnType]`` → ``YieldType``
    ``Iterator[YieldType]`` → ``YieldType``
    ``AsyncGenerator[YieldType, SendType]`` → ``YieldType``
    """
    m = _GENERATOR_RE.match(annotation.strip())
    if m is None:
        return annotation
    inner = m.group(1)
    # Extract the first type argument, respecting bracket nesting.
    depth = 0
    for i, ch in enumerate(inner):
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(depth - 1, 0)
        elif ch == "," and depth == 0:
            return inner[:i].strip()
    return inner.strip()


def _section_entries_with_annotation(
    target: LintTarget,
    section_kind: TypedSectionKind,
) -> list[tuple[TypedEntry, str]] | None:
    """Return (entry, annotation) pairs for a return/yield typed section."""
    if target.docstring is None:
        return None
    if target.signature is None or target.signature.return_annotation is None:
        return None

    section = target.docstring.typed_section(section_kind)
    if section is None or not section.entries:
        return None

    annotation = target.signature.return_annotation
    if section_kind == TypedSectionKind.YIELDS:
        annotation = _extract_yield_type(annotation)
    return [(entry, annotation) for entry in section.entries]


# ---------------------------------------------------------------------------
# missing-param-type
# ---------------------------------------------------------------------------


class MissingParamType:
    """Parameter type missing from docstring."""

    metadata = RuleMetadata(
        name="missing-param-type",
        group=_GROUP,
        description="Parameter type missing from docstring",
        default_severity=Severity.WARNING,
        applies_to=CALLABLE_AND_CLASS_KINDS,
        fixable=True,
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
        pairs = _param_entries_with_annotation(target)
        if pairs is None:
            return ()
        return _check_missing_types(
            self, target, context,
            section_kind=TypedSectionKind.PARAMETERS,
            entries_with_annotation=pairs,
            message="Parameter is missing a type in the docstring",
            affected_rules=("missing-param-type", "param-type-mismatch"),
        )


# ---------------------------------------------------------------------------
# param-type-mismatch
# ---------------------------------------------------------------------------


class ParamTypeMismatch:
    """Parameter type mismatches annotation."""

    metadata = RuleMetadata(
        name="param-type-mismatch",
        group=_GROUP,
        description="Parameter type mismatches annotation",
        default_severity=Severity.WARNING,
        applies_to=CALLABLE_AND_CLASS_KINDS,
        fixable=True,
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
        pairs = _param_entries_with_annotation(target)
        if pairs is None:
            return ()
        return _check_mismatched_types(
            self, target, context,
            entries_with_annotation=pairs,
            message_fn=lambda e, a: (
                f"Parameter '{e.name}' type '{e.type_text}'"
                f" does not match annotation '{a}'"
            ),
            affected_rules=("param-type-mismatch",),
        )


# ---------------------------------------------------------------------------
# missing-return-type
# ---------------------------------------------------------------------------


class MissingReturnType:
    """Return type missing from docstring."""

    metadata = RuleMetadata(
        name="missing-return-type",
        group=_GROUP,
        description="Return type missing from docstring",
        default_severity=Severity.WARNING,
        applies_to=CALLABLE_TARGET_KINDS,
        fixable=True,
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
        pairs = _section_entries_with_annotation(target, TypedSectionKind.RETURNS)
        if pairs is None:
            return ()
        return _check_missing_types(
            self, target, context,
            section_kind=TypedSectionKind.RETURNS,
            entries_with_annotation=pairs,
            message="Returns section entry is missing a type",
            affected_rules=("missing-return-type", "return-type-mismatch"),
        )


# ---------------------------------------------------------------------------
# return-type-mismatch
# ---------------------------------------------------------------------------


class ReturnTypeMismatch:
    """Return type mismatches annotation."""

    metadata = RuleMetadata(
        name="return-type-mismatch",
        group=_GROUP,
        description="Return type mismatches annotation",
        default_severity=Severity.WARNING,
        applies_to=CALLABLE_TARGET_KINDS,
        fixable=True,
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
        pairs = _section_entries_with_annotation(target, TypedSectionKind.RETURNS)
        if pairs is None:
            return ()
        return _check_mismatched_types(
            self, target, context,
            entries_with_annotation=pairs,
            message_fn=lambda e, a: (
                f"Returns entry type '{e.type_text}' does not match annotation '{a}'"
            ),
            affected_rules=("return-type-mismatch",),
        )


# ---------------------------------------------------------------------------
# yield-type-mismatch
# ---------------------------------------------------------------------------


class YieldTypeMismatch:
    """Yield type missing or mismatched."""

    metadata = RuleMetadata(
        name="yield-type-mismatch",
        group=_GROUP,
        description="Yield type missing or mismatched",
        default_severity=Severity.WARNING,
        applies_to=CALLABLE_TARGET_KINDS,
        fixable=True,
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
        pairs = _section_entries_with_annotation(target, TypedSectionKind.YIELDS)
        if pairs is None:
            return ()
        return _check_missing_types(
            self, target, context,
            section_kind=TypedSectionKind.YIELDS,
            entries_with_annotation=pairs,
            message="Yields section entry is missing a type",
            affected_rules=("yield-type-mismatch",),
        ) + _check_mismatched_types(
            self, target, context,
            entries_with_annotation=pairs,
            message_fn=lambda e, a: (
                f"Yields entry type '{e.type_text}' does not match annotation '{a}'"
            ),
            affected_rules=("yield-type-mismatch",),
        )


# ---------------------------------------------------------------------------
# missing-attribute-type
# ---------------------------------------------------------------------------


class MissingAttributeType:
    """Attribute type missing where Attributes entry exists."""

    metadata = RuleMetadata(
        name="missing-attribute-type",
        group=_GROUP,
        description="Attribute type missing where Attributes entry exists",
        default_severity=Severity.WARNING,
        applies_to=frozenset({TargetKind.CLASS}),
        fixable=True,
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
        if target.docstring is None:
            return ()
        attrs_section = target.docstring.typed_section(TypedSectionKind.ATTRIBUTES)
        if attrs_section is None or not attrs_section.entries:
            return ()

        attr_facts = {a.name: a for a in target.attributes}
        pairs: list[tuple[TypedEntry, str]] = []
        for entry in attrs_section.entries:
            if entry.name is None:
                continue
            attr_fact = attr_facts.get(entry.name)
            if attr_fact is None or attr_fact.annotation is None:
                continue
            pairs.append((entry, attr_fact.annotation))

        if not pairs:
            return ()

        return _check_missing_types(
            self, target, context,
            section_kind=TypedSectionKind.ATTRIBUTES,
            entries_with_annotation=pairs,
            message="Attribute is missing a type in the docstring",
            affected_rules=("missing-attribute-type",),
        )
