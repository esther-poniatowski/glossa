"""D4xx Typed Entry Consistency rules for the glossa docstring linter."""

from __future__ import annotations

from glossa.domain.rules import RuleMetadata, RuleContext
from glossa.core.contracts import (
    Diagnostic,
    LintTarget,
    Severity,
    TargetKind,
    DocstringEdit,
    EditKind,
    FixPlan,
)
from glossa.domain.models import TypedSection, TypedSectionKind, TypedEntry


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _find_section(
    sections: tuple,
    kind: TypedSectionKind,
) -> TypedSection | None:
    """Find the first TypedSection of the given kind in sections.

    Parameters
    ----------
    sections : tuple
        The tuple of section nodes from a ParsedDocstring.
    kind : TypedSectionKind
        The section kind to search for.

    Returns
    -------
    TypedSection | None
        The first matching TypedSection, or None if not found.
    """
    for section in sections:
        if isinstance(section, TypedSection) and section.kind is kind:
            return section
    return None


def _find_param_entry(
    sections: tuple,
    param_name: str,
) -> TypedEntry | None:
    """Find a TypedEntry in the Parameters section matching the given name.

    Parameters
    ----------
    sections : tuple
        The tuple of section nodes from a ParsedDocstring.
    param_name : str
        The parameter name to search for.

    Returns
    -------
    TypedEntry | None
        The matching TypedEntry, or None if not found.
    """
    params_section = _find_section(sections, TypedSectionKind.PARAMETERS)
    if params_section is None:
        return None
    for entry in params_section.entries:
        if entry.name == param_name:
            return entry
    return None


def _get_signature_params(target: LintTarget) -> tuple:
    """Get parameters from target.signature, excluding self/cls.

    For CLASS targets, also checks the related constructor's signature when
    the target's own signature has no parameters.

    Parameters
    ----------
    target : LintTarget
        The lint target to extract parameters from.

    Returns
    -------
    tuple
        A tuple of ParameterFact instances, excluding self and cls parameters.
    """
    _EXCLUDED = frozenset({"self", "cls"})

    def _filter(params: tuple) -> tuple:
        return tuple(p for p in params if p.name not in _EXCLUDED)

    if target.signature is not None:
        params = _filter(target.signature.parameters)
        if params:
            return params

    # For CLASS targets, fall back to the related constructor's signature.
    if target.kind is TargetKind.CLASS:
        constructor_ref = target.related.get("constructor")
        if constructor_ref is not None and constructor_ref.signature is not None:
            return _filter(constructor_ref.signature.parameters)

    if target.signature is not None:
        return _filter(target.signature.parameters)

    return ()


def _types_match(doc_type: str, annotation: str) -> bool:
    """Check whether a docstring type string matches a signature annotation.

    Normalizes both sides before comparing:

    - Strips leading and trailing whitespace.
    - Treats ``Optional[X]`` as equivalent to ``X | None``.
    - Treats the NumPy "X, optional" convention as equivalent to ``X | None``
      (the base type ``X`` is compared against *annotation* after stripping
      the ``| None`` suffix, if present).

    Parameters
    ----------
    doc_type : str
        The type string from the docstring entry.
    annotation : str
        The type annotation from the function signature.

    Returns
    -------
    bool
        True if the types are considered equivalent, False otherwise.
    """
    doc = doc_type.strip()
    ann = annotation.strip()

    if doc == ann:
        return True

    def _normalize_optional(t: str) -> str:
        """Convert Optional[X] to X | None."""
        if t.startswith("Optional[") and t.endswith("]"):
            inner = t[len("Optional["):-1].strip()
            return f"{inner} | None"
        return t

    doc_norm = _normalize_optional(doc)
    ann_norm = _normalize_optional(ann)

    if doc_norm == ann_norm:
        return True

    # NumPy "X, optional" convention: the docstring type is "X, optional",
    # meaning the parameter is optional and has base type X.
    # Consider it matching if X equals the annotation, or if the annotation
    # is "X | None" (with or without Optional normalisation).
    if doc.endswith(", optional"):
        base = doc[: -len(", optional")].strip()
        base_norm = _normalize_optional(base)
        # Match bare base type.
        if base_norm == ann_norm:
            return True
        # Match "X | None" variant.
        if ann_norm in (f"{base_norm} | None", f"{base} | None"):
            return True
        if base == ann:
            return True

    return False


# ---------------------------------------------------------------------------
# D400 — Parameter type missing from docstring
# ---------------------------------------------------------------------------


class D400:
    """Parameter type missing from docstring."""

    metadata = RuleMetadata(
        code="D400",
        description="Parameter type missing from docstring",
        default_severity=Severity.WARNING,
        applies_to=frozenset({TargetKind.FUNCTION, TargetKind.METHOD, TargetKind.CLASS}),
        fixable=True,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        """Evaluate D400 for the given target.

        Parameters
        ----------
        target : LintTarget
            The lint target to evaluate.
        context : RuleContext
            The active rule context.

        Returns
        -------
        tuple[Diagnostic, ...]
            Zero or more diagnostics.
        """
        if target.docstring is None:
            return ()

        sections = target.docstring.sections
        params_section = _find_section(sections, TypedSectionKind.PARAMETERS)
        if params_section is None:
            return ()

        sig_params = {p.name: p for p in _get_signature_params(target)}
        diagnostics: list[Diagnostic] = []

        for entry in params_section.entries:
            if entry.name is None:
                continue
            if entry.type_text is not None:
                continue

            sig_param = sig_params.get(entry.name)
            if sig_param is None or sig_param.annotation is None:
                # No annotation available to suggest — skip.
                continue

            annotation = sig_param.annotation
            fix = FixPlan(
                description=f"Add type '{annotation}' to parameter '{entry.name}'",
                target=target.ref,
                edits=(
                    DocstringEdit(
                        kind=EditKind.REPLACE,
                        span=entry.span,
                        anchor=f"Parameters:{entry.name}",
                        text=_entry_with_type(entry, annotation),
                    ),
                ),
                affected_rules=("D400", "D401"),
            )
            diagnostics.append(
                Diagnostic(
                    code="D400",
                    message=(
                        f"Parameter '{entry.name}' is missing a type in the docstring"
                    ),
                    severity=context.policy.severity,
                    target=target.ref,
                    span=entry.span,
                    fix=fix,
                )
            )

        return tuple(diagnostics)


# ---------------------------------------------------------------------------
# D401 — Parameter type mismatches annotation
# ---------------------------------------------------------------------------


class D401:
    """Parameter type mismatches annotation."""

    metadata = RuleMetadata(
        code="D401",
        description="Parameter type mismatches annotation",
        default_severity=Severity.WARNING,
        applies_to=frozenset({TargetKind.FUNCTION, TargetKind.METHOD, TargetKind.CLASS}),
        fixable=True,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        """Evaluate D401 for the given target.

        Parameters
        ----------
        target : LintTarget
            The lint target to evaluate.
        context : RuleContext
            The active rule context.

        Returns
        -------
        tuple[Diagnostic, ...]
            Zero or more diagnostics.
        """
        if target.docstring is None:
            return ()

        sections = target.docstring.sections
        params_section = _find_section(sections, TypedSectionKind.PARAMETERS)
        if params_section is None:
            return ()

        sig_params = {p.name: p for p in _get_signature_params(target)}
        diagnostics: list[Diagnostic] = []

        for entry in params_section.entries:
            if entry.name is None:
                continue
            if entry.type_text is None:
                continue

            sig_param = sig_params.get(entry.name)
            if sig_param is None or sig_param.annotation is None:
                continue

            if _types_match(entry.type_text, sig_param.annotation):
                continue

            annotation = sig_param.annotation
            fix = FixPlan(
                description=(
                    f"Replace type '{entry.type_text}' with '{annotation}'"
                    f" for parameter '{entry.name}'"
                ),
                target=target.ref,
                edits=(
                    DocstringEdit(
                        kind=EditKind.REPLACE,
                        span=entry.span,
                        anchor=f"Parameters:{entry.name}",
                        text=_entry_with_type(entry, annotation),
                    ),
                ),
                affected_rules=("D401",),
            )
            diagnostics.append(
                Diagnostic(
                    code="D401",
                    message=(
                        f"Parameter '{entry.name}' type '{entry.type_text}'"
                        f" does not match annotation '{annotation}'"
                    ),
                    severity=context.policy.severity,
                    target=target.ref,
                    span=entry.span,
                    fix=fix,
                )
            )

        return tuple(diagnostics)


# ---------------------------------------------------------------------------
# D402 — Return type missing from docstring
# ---------------------------------------------------------------------------


class D402:
    """Return type missing from docstring."""

    metadata = RuleMetadata(
        code="D402",
        description="Return type missing from docstring",
        default_severity=Severity.WARNING,
        applies_to=frozenset({TargetKind.FUNCTION, TargetKind.METHOD, TargetKind.PROPERTY}),
        fixable=True,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        """Evaluate D402 for the given target.

        Parameters
        ----------
        target : LintTarget
            The lint target to evaluate.
        context : RuleContext
            The active rule context.

        Returns
        -------
        tuple[Diagnostic, ...]
            Zero or more diagnostics.
        """
        if target.docstring is None:
            return ()
        if target.signature is None or target.signature.return_annotation is None:
            return ()

        sections = target.docstring.sections
        returns_section = _find_section(sections, TypedSectionKind.RETURNS)
        if returns_section is None or not returns_section.entries:
            return ()

        annotation = target.signature.return_annotation
        diagnostics: list[Diagnostic] = []

        for entry in returns_section.entries:
            if entry.type_text is not None:
                continue

            fix = FixPlan(
                description=f"Add return type '{annotation}' to Returns entry",
                target=target.ref,
                edits=(
                    DocstringEdit(
                        kind=EditKind.REPLACE,
                        span=entry.span,
                        anchor="Returns:entry",
                        text=_entry_with_type(entry, annotation),
                    ),
                ),
                affected_rules=("D402", "D403"),
            )
            diagnostics.append(
                Diagnostic(
                    code="D402",
                    message="Returns section entry is missing a type",
                    severity=context.policy.severity,
                    target=target.ref,
                    span=entry.span,
                    fix=fix,
                )
            )

        return tuple(diagnostics)


# ---------------------------------------------------------------------------
# D403 — Return type mismatches annotation
# ---------------------------------------------------------------------------


class D403:
    """Return type mismatches annotation."""

    metadata = RuleMetadata(
        code="D403",
        description="Return type mismatches annotation",
        default_severity=Severity.WARNING,
        applies_to=frozenset({TargetKind.FUNCTION, TargetKind.METHOD, TargetKind.PROPERTY}),
        fixable=True,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        """Evaluate D403 for the given target.

        Parameters
        ----------
        target : LintTarget
            The lint target to evaluate.
        context : RuleContext
            The active rule context.

        Returns
        -------
        tuple[Diagnostic, ...]
            Zero or more diagnostics.
        """
        if target.docstring is None:
            return ()
        if target.signature is None or target.signature.return_annotation is None:
            return ()

        sections = target.docstring.sections
        returns_section = _find_section(sections, TypedSectionKind.RETURNS)
        if returns_section is None or not returns_section.entries:
            return ()

        annotation = target.signature.return_annotation
        diagnostics: list[Diagnostic] = []

        for entry in returns_section.entries:
            if entry.type_text is None:
                continue
            if _types_match(entry.type_text, annotation):
                continue

            fix = FixPlan(
                description=f"Replace return type '{entry.type_text}' with '{annotation}'",
                target=target.ref,
                edits=(
                    DocstringEdit(
                        kind=EditKind.REPLACE,
                        span=entry.span,
                        anchor="Returns:entry",
                        text=_entry_with_type(entry, annotation),
                    ),
                ),
                affected_rules=("D403",),
            )
            diagnostics.append(
                Diagnostic(
                    code="D403",
                    message=(
                        f"Returns entry type '{entry.type_text}'"
                        f" does not match annotation '{annotation}'"
                    ),
                    severity=context.policy.severity,
                    target=target.ref,
                    span=entry.span,
                    fix=fix,
                )
            )

        return tuple(diagnostics)


# ---------------------------------------------------------------------------
# D404 — Yield type missing or mismatched
# ---------------------------------------------------------------------------


class D404:
    """Yield type missing or mismatched."""

    metadata = RuleMetadata(
        code="D404",
        description="Yield type missing or mismatched",
        default_severity=Severity.WARNING,
        applies_to=frozenset({TargetKind.FUNCTION, TargetKind.METHOD, TargetKind.PROPERTY}),
        fixable=True,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        """Evaluate D404 for the given target.

        Parameters
        ----------
        target : LintTarget
            The lint target to evaluate.
        context : RuleContext
            The active rule context.

        Returns
        -------
        tuple[Diagnostic, ...]
            Zero or more diagnostics.
        """
        if target.docstring is None:
            return ()
        if target.signature is None or target.signature.return_annotation is None:
            return ()

        sections = target.docstring.sections
        yields_section = _find_section(sections, TypedSectionKind.YIELDS)
        if yields_section is None or not yields_section.entries:
            return ()

        annotation = target.signature.return_annotation
        diagnostics: list[Diagnostic] = []

        for entry in yields_section.entries:
            if entry.type_text is None:
                # Missing type — same logic as D402 but for Yields.
                fix = FixPlan(
                    description=f"Add yield type '{annotation}' to Yields entry",
                    target=target.ref,
                    edits=(
                        DocstringEdit(
                            kind=EditKind.REPLACE,
                            span=entry.span,
                            anchor="Yields:entry",
                            text=_entry_with_type(entry, annotation),
                        ),
                    ),
                    affected_rules=("D404",),
                )
                diagnostics.append(
                    Diagnostic(
                        code="D404",
                        message="Yields section entry is missing a type",
                        severity=context.policy.severity,
                        target=target.ref,
                        span=entry.span,
                        fix=fix,
                    )
                )
            elif not _types_match(entry.type_text, annotation):
                # Mismatched type — same logic as D403 but for Yields.
                fix = FixPlan(
                    description=f"Replace yield type '{entry.type_text}' with '{annotation}'",
                    target=target.ref,
                    edits=(
                        DocstringEdit(
                            kind=EditKind.REPLACE,
                            span=entry.span,
                            anchor="Yields:entry",
                            text=_entry_with_type(entry, annotation),
                        ),
                    ),
                    affected_rules=("D404",),
                )
                diagnostics.append(
                    Diagnostic(
                        code="D404",
                        message=(
                            f"Yields entry type '{entry.type_text}'"
                            f" does not match annotation '{annotation}'"
                        ),
                        severity=context.policy.severity,
                        target=target.ref,
                        span=entry.span,
                        fix=fix,
                    )
                )

        return tuple(diagnostics)


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

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        """Evaluate D405 for the given target.

        Parameters
        ----------
        target : LintTarget
            The lint target to evaluate.
        context : RuleContext
            The active rule context.

        Returns
        -------
        tuple[Diagnostic, ...]
            Zero or more diagnostics.
        """
        if target.docstring is None:
            return ()

        sections = target.docstring.sections
        attrs_section = _find_section(sections, TypedSectionKind.ATTRIBUTES)
        if attrs_section is None or not attrs_section.entries:
            return ()

        attr_facts = {a.name: a for a in target.attributes}
        diagnostics: list[Diagnostic] = []

        for entry in attrs_section.entries:
            if entry.name is None:
                continue
            if entry.type_text is not None:
                continue

            attr_fact = attr_facts.get(entry.name)
            if attr_fact is None or attr_fact.annotation is None:
                continue

            annotation = attr_fact.annotation
            fix = FixPlan(
                description=f"Add type '{annotation}' to attribute '{entry.name}'",
                target=target.ref,
                edits=(
                    DocstringEdit(
                        kind=EditKind.REPLACE,
                        span=entry.span,
                        anchor=f"Attributes:{entry.name}",
                        text=_entry_with_type(entry, annotation),
                    ),
                ),
                affected_rules=("D405",),
            )
            diagnostics.append(
                Diagnostic(
                    code="D405",
                    message=(
                        f"Attribute '{entry.name}' is missing a type in the docstring"
                    ),
                    severity=context.policy.severity,
                    target=target.ref,
                    span=entry.span,
                    fix=fix,
                )
            )

        return tuple(diagnostics)


# ---------------------------------------------------------------------------
# Private rendering helper
# ---------------------------------------------------------------------------


def _entry_with_type(entry: TypedEntry, type_text: str) -> str:
    """Render a TypedEntry header line with the given type substituted or added.

    This produces the corrected header text used as the replacement in a
    DocstringEdit.  The rendered form follows the NumPy convention:

    - Named entry (Parameters / Attributes):  ``name : type``
    - Unnamed entry (Returns / Yields):        ``type``

    The existing description lines are not included; the fix engine applies
    the replacement at the entry span level and preserves surrounding text.

    Parameters
    ----------
    entry : TypedEntry
        The entry whose header is being rendered.
    type_text : str
        The type string to use.

    Returns
    -------
    str
        The rendered header line for the entry.
    """
    if entry.name is not None:
        return f"{entry.name} : {type_text}"
    return type_text
