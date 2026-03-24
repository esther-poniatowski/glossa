"""D4xx Typed Entry Consistency rules for the glossa docstring linter."""

from __future__ import annotations

from glossa.core.contracts import (
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


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _get_signature_params(target: LintTarget) -> tuple:
    """Get parameters from target.signature, excluding self/cls.

    For CLASS targets, also checks the related constructor's signature when
    the target's own signature has no parameters.
    """
    _EXCLUDED = frozenset({"self", "cls"})

    def _filter(params: tuple) -> tuple:
        return tuple(p for p in params if p.name not in _EXCLUDED)

    if target.signature is not None:
        params = _filter(target.signature.parameters)
        if params:
            return params

    if target.kind is TargetKind.CLASS:
        constructor_ref = target.related.constructor
        if constructor_ref is not None and constructor_ref.signature is not None:
            return _filter(constructor_ref.signature.parameters)

    if target.signature is not None:
        return _filter(target.signature.parameters)

    return ()


def _types_match(doc_type: str, annotation: str) -> bool:
    """Check whether a docstring type string matches a signature annotation."""
    doc = doc_type.strip()
    ann = annotation.strip()

    if doc == ann:
        return True

    def _normalize_optional(t: str) -> str:
        if t.startswith("Optional[") and t.endswith("]"):
            inner = t[len("Optional["):-1].strip()
            return f"{inner} | None"
        return t

    doc_norm = _normalize_optional(doc)
    ann_norm = _normalize_optional(ann)

    if doc_norm == ann_norm:
        return True

    if doc.endswith(", optional"):
        base = doc[: -len(", optional")].strip()
        base_norm = _normalize_optional(base)
        if base_norm == ann_norm:
            return True
        if ann_norm in (f"{base_norm} | None", f"{base} | None"):
            return True
        if base == ann:
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
    anchor: str,
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
                anchor=anchor,
                text=_entry_with_type(entry, annotation),
            ),
        ),
        affected_rules=affected_rules,
    )


# ---------------------------------------------------------------------------
# Shared typed-entry consistency checker (Fix #5)
# ---------------------------------------------------------------------------


def _check_typed_entries(
    rule,
    target: LintTarget,
    context: RuleContext,
    section_kind: TypedSectionKind,
    entries_with_annotation: list[tuple[TypedEntry, str]],
    anchor_prefix: str,
    check_missing: bool,
    check_mismatch: bool,
    missing_message: str,
    mismatch_message_fn,
    missing_affected: tuple[str, ...],
    mismatch_affected: tuple[str, ...],
) -> tuple[Diagnostic, ...]:
    """Shared checker for missing/mismatched type entries in typed sections."""
    diagnostics: list[Diagnostic] = []

    for entry, annotation in entries_with_annotation:
        if check_missing and entry.type_text is None:
            if entry.name is not None:
                anchor = f"{anchor_prefix}:{entry.name}"
                desc = f"Add type '{annotation}' to parameter '{entry.name}'"
            else:
                anchor = f"{anchor_prefix}:entry"
                desc = f"Add type '{annotation}' to {section_kind.value} entry"
            fix = _make_entry_fix(target, entry, annotation, desc, anchor, missing_affected)
            diagnostics.append(
                make_diagnostic(rule, target, context, missing_message, span=entry.span, fix=fix)
            )
        elif check_mismatch and entry.type_text is not None:
            if _types_match(entry.type_text, annotation):
                continue
            if entry.name is not None:
                anchor = f"{anchor_prefix}:{entry.name}"
                desc = f"Replace type '{entry.type_text}' with '{annotation}' for parameter '{entry.name}'"
            else:
                anchor = f"{anchor_prefix}:entry"
                desc = f"Replace type '{entry.type_text}' with '{annotation}'"
            fix = _make_entry_fix(target, entry, annotation, desc, anchor, mismatch_affected)
            diagnostics.append(
                make_diagnostic(
                    rule, target, context,
                    mismatch_message_fn(entry, annotation),
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

    sig_params = {p.name: p for p in _get_signature_params(target)}
    result: list[tuple[TypedEntry, str]] = []
    for entry in params_section.entries:
        if entry.name is None:
            continue
        sig_param = sig_params.get(entry.name)
        if sig_param is None or sig_param.annotation is None:
            continue
        result.append((entry, sig_param.annotation))
    return result if result else None


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
    return [(entry, annotation) for entry in section.entries]


# ---------------------------------------------------------------------------
# D400 — Parameter type missing from docstring
# ---------------------------------------------------------------------------


class D400:
    """Parameter type missing from docstring."""

    metadata = RuleMetadata(
        code="D400",
        description="Parameter type missing from docstring",
        default_severity=Severity.WARNING,
        applies_to=CALLABLE_AND_CLASS_KINDS,
        fixable=True,
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
        pairs = _param_entries_with_annotation(target)
        if pairs is None:
            return ()
        return _check_typed_entries(
            self, target, context,
            section_kind=TypedSectionKind.PARAMETERS,
            entries_with_annotation=pairs,
            anchor_prefix="Parameters",
            check_missing=True,
            check_mismatch=False,
            missing_message="Parameter is missing a type in the docstring",
            mismatch_message_fn=None,
            missing_affected=("D400", "D401"),
            mismatch_affected=(),
        )


# ---------------------------------------------------------------------------
# D401 — Parameter type mismatches annotation
# ---------------------------------------------------------------------------


class D401:
    """Parameter type mismatches annotation."""

    metadata = RuleMetadata(
        code="D401",
        description="Parameter type mismatches annotation",
        default_severity=Severity.WARNING,
        applies_to=CALLABLE_AND_CLASS_KINDS,
        fixable=True,
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
        pairs = _param_entries_with_annotation(target)
        if pairs is None:
            return ()
        return _check_typed_entries(
            self, target, context,
            section_kind=TypedSectionKind.PARAMETERS,
            entries_with_annotation=pairs,
            anchor_prefix="Parameters",
            check_missing=False,
            check_mismatch=True,
            missing_message="",
            mismatch_message_fn=lambda e, a: (
                f"Parameter '{e.name}' type '{e.type_text}'"
                f" does not match annotation '{a}'"
            ),
            missing_affected=(),
            mismatch_affected=("D401",),
        )


# ---------------------------------------------------------------------------
# D402 — Return type missing from docstring
# ---------------------------------------------------------------------------


class D402:
    """Return type missing from docstring."""

    metadata = RuleMetadata(
        code="D402",
        description="Return type missing from docstring",
        default_severity=Severity.WARNING,
        applies_to=CALLABLE_TARGET_KINDS,
        fixable=True,
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
        pairs = _section_entries_with_annotation(target, TypedSectionKind.RETURNS)
        if pairs is None:
            return ()
        return _check_typed_entries(
            self, target, context,
            section_kind=TypedSectionKind.RETURNS,
            entries_with_annotation=pairs,
            anchor_prefix="Returns",
            check_missing=True,
            check_mismatch=False,
            missing_message="Returns section entry is missing a type",
            mismatch_message_fn=None,
            missing_affected=("D402", "D403"),
            mismatch_affected=(),
        )


# ---------------------------------------------------------------------------
# D403 — Return type mismatches annotation
# ---------------------------------------------------------------------------


class D403:
    """Return type mismatches annotation."""

    metadata = RuleMetadata(
        code="D403",
        description="Return type mismatches annotation",
        default_severity=Severity.WARNING,
        applies_to=CALLABLE_TARGET_KINDS,
        fixable=True,
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
        pairs = _section_entries_with_annotation(target, TypedSectionKind.RETURNS)
        if pairs is None:
            return ()
        return _check_typed_entries(
            self, target, context,
            section_kind=TypedSectionKind.RETURNS,
            entries_with_annotation=pairs,
            anchor_prefix="Returns",
            check_missing=False,
            check_mismatch=True,
            missing_message="",
            mismatch_message_fn=lambda e, a: (
                f"Returns entry type '{e.type_text}' does not match annotation '{a}'"
            ),
            missing_affected=(),
            mismatch_affected=("D403",),
        )


# ---------------------------------------------------------------------------
# D404 — Yield type missing or mismatched
# ---------------------------------------------------------------------------


class D404:
    """Yield type missing or mismatched."""

    metadata = RuleMetadata(
        code="D404",
        description="Yield type missing or mismatched",
        default_severity=Severity.WARNING,
        applies_to=CALLABLE_TARGET_KINDS,
        fixable=True,
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
        pairs = _section_entries_with_annotation(target, TypedSectionKind.YIELDS)
        if pairs is None:
            return ()
        return _check_typed_entries(
            self, target, context,
            section_kind=TypedSectionKind.YIELDS,
            entries_with_annotation=pairs,
            anchor_prefix="Yields",
            check_missing=True,
            check_mismatch=True,
            missing_message="Yields section entry is missing a type",
            mismatch_message_fn=lambda e, a: (
                f"Yields entry type '{e.type_text}' does not match annotation '{a}'"
            ),
            missing_affected=("D404",),
            mismatch_affected=("D404",),
        )


# ---------------------------------------------------------------------------
# D405 — Attribute type missing where Attributes entry exists
# ---------------------------------------------------------------------------


class D405:
    """Attribute type missing where Attributes entry exists."""

    metadata = RuleMetadata(
        code="D405",
        description="Attribute type missing where Attributes entry exists",
        default_severity=Severity.WARNING,
        applies_to=frozenset({TargetKind.CLASS}),
        fixable=True,
    )

    def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
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

        return _check_typed_entries(
            self, target, context,
            section_kind=TypedSectionKind.ATTRIBUTES,
            entries_with_annotation=pairs,
            anchor_prefix="Attributes",
            check_missing=True,
            check_mismatch=False,
            missing_message="Attribute is missing a type in the docstring",
            mismatch_message_fn=None,
            missing_affected=("D405",),
            mismatch_affected=(),
        )
