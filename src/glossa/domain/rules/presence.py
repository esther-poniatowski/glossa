"""D1xx Presence and Coverage rules for the glossa docstring linter."""

from __future__ import annotations

from typing import Callable

from glossa.application.contracts import (
    ALL_TARGET_KINDS,
    CALLABLE_TARGET_KINDS,
    Diagnostic,
    ExceptionFact,
    LintTarget,
    Severity,
    SignatureFacts,
    TargetKind,
    Visibility,
    WarningFact,
)
from glossa.domain.models import InventorySectionKind, TypedSectionKind
from glossa.domain.rules import RuleContext, RuleMetadata, make_diagnostic
from glossa.domain.rules._parameters import documentable_param_names


# ---------------------------------------------------------------------------
# Parameterized rule factories (Fix #3)
# ---------------------------------------------------------------------------


def _make_missing_docstring_rule(
    kind: TargetKind,
    code: str,
    description: str,
    message: str,
) -> type:
    """Factory for D100/D101: fire if a public target of *kind* has no docstring."""

    class _Rule:
        metadata = RuleMetadata(
            code=code,
            description=description,
            default_severity=Severity.CONVENTION,
            applies_to=frozenset({kind}),
            fixable=False,
            requires_docstring=False,
        )

        def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
            if (
                target.kind is kind
                and target.visibility is Visibility.PUBLIC
                and target.docstring is None
            ):
                return (make_diagnostic(self, target, context, message),)
            return ()

    _Rule.__name__ = code
    _Rule.__qualname__ = code
    _Rule.__doc__ = description
    return _Rule


def _make_missing_section_rule(
    code: str,
    description: str,
    message: str,
    section_kind: TypedSectionKind,
    signature_predicate: Callable[[SignatureFacts], bool],
    applies_to: frozenset[TargetKind],
    option_key: str | None = None,
) -> type:
    """Factory for D104/D105: fire if a signature predicate is True but section is missing."""

    class _Rule:
        metadata = RuleMetadata(
            code=code,
            description=description,
            default_severity=Severity.WARNING,
            applies_to=applies_to,
            fixable=True,
        )

        def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
            if target.docstring is None or target.signature is None:
                return ()
            if not signature_predicate(target.signature):
                return ()

            if option_key is not None and target.kind is TargetKind.PROPERTY:
                if not context.policy.options.get(option_key, True):
                    return ()

            if not target.docstring.has_typed_section(section_kind):
                return (make_diagnostic(self, target, context, message),)
            return ()

    _Rule.__name__ = code
    _Rule.__qualname__ = code
    _Rule.__doc__ = description
    return _Rule


def _make_missing_fact_section_rule(
    code: str,
    description: str,
    message: str,
    fact_accessor: Callable[[LintTarget], tuple[ExceptionFact, ...] | tuple[WarningFact, ...]],
    section_kind: TypedSectionKind,
    confidence_filter: str = "high",
    exclude_evidence: str | None = None,
) -> type:
    """Factory for D106/D107: fire if high-confidence facts exist but section is missing."""

    class _Rule:
        metadata = RuleMetadata(
            code=code,
            description=description,
            default_severity=Severity.WARNING,
            applies_to=CALLABLE_TARGET_KINDS,
            fixable=False,
        )

        def evaluate(self, target: LintTarget, context: RuleContext) -> tuple[Diagnostic, ...]:
            if target.docstring is None:
                return ()
            facts = fact_accessor(target)
            relevant = [
                f for f in facts
                if f.confidence == confidence_filter
                and (exclude_evidence is None or getattr(f, "evidence", None) != exclude_evidence)
            ]
            if not relevant:
                return ()

            if not target.docstring.has_typed_section(section_kind):
                return (make_diagnostic(self, target, context, message),)
            return ()

    _Rule.__name__ = code
    _Rule.__qualname__ = code
    _Rule.__doc__ = description
    return _Rule


# ---------------------------------------------------------------------------
# D100 — Missing public module docstring
# ---------------------------------------------------------------------------

D100 = _make_missing_docstring_rule(
    kind=TargetKind.MODULE,
    code="D100",
    description="Missing public module docstring.",
    message="Missing docstring in public module.",
)


# ---------------------------------------------------------------------------
# D101 — Missing public class docstring
# ---------------------------------------------------------------------------

D101 = _make_missing_docstring_rule(
    kind=TargetKind.CLASS,
    code="D101",
    description="Missing public class docstring.",
    message="Missing docstring in public class.",
)


# ---------------------------------------------------------------------------
# D102 — Missing public callable docstring
# ---------------------------------------------------------------------------


class D102:
    """Missing public callable docstring."""

    metadata = RuleMetadata(
        code="D102",
        description="Missing public callable docstring.",
        default_severity=Severity.CONVENTION,
        applies_to=frozenset({TargetKind.FUNCTION, TargetKind.METHOD, TargetKind.PROPERTY}),
        fixable=False,
        requires_docstring=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if target.docstring is not None:
            return ()

        include_test = context.policy.options.get("include_test_functions", False)
        if not include_test and target.is_test_target:
            return ()

        include_private = context.policy.options.get("include_private_helpers", False)
        if not include_private and target.visibility is Visibility.PRIVATE:
            return ()

        if target.visibility is Visibility.PUBLIC:
            return (make_diagnostic(self, target, context, "Missing docstring in public callable."),)
        return ()


# ---------------------------------------------------------------------------
# D103 — Missing Parameters section for documentable parameters
# ---------------------------------------------------------------------------


class D103:
    """Missing Parameters section for documentable parameters."""

    metadata = RuleMetadata(
        code="D103",
        description="Missing Parameters section for documentable parameters.",
        default_severity=Severity.WARNING,
        applies_to=frozenset({TargetKind.FUNCTION, TargetKind.METHOD, TargetKind.CLASS}),
        fixable=True,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:
        if not documentable_param_names(target):
            return ()

        if target.docstring is None or not target.docstring.has_typed_section(TypedSectionKind.PARAMETERS):
            return (
                make_diagnostic(
                    self, target, context,
                    "Missing Parameters section for documentable parameters.",
                ),
            )
        return ()


# ---------------------------------------------------------------------------
# D104 — Missing Returns section where required
# ---------------------------------------------------------------------------

D104 = _make_missing_section_rule(
    code="D104",
    description="Missing Returns section where required.",
    message="Missing Returns section where required.",
    section_kind=TypedSectionKind.RETURNS,
    signature_predicate=lambda s: s.returns_value,
    applies_to=CALLABLE_TARGET_KINDS,
    option_key="simple_property_requires_returns",
)


# ---------------------------------------------------------------------------
# D105 — Missing Yields section for generators
# ---------------------------------------------------------------------------

D105 = _make_missing_section_rule(
    code="D105",
    description="Missing Yields section for generators.",
    message="Missing Yields section for generator.",
    section_kind=TypedSectionKind.YIELDS,
    signature_predicate=lambda s: s.yields_value,
    applies_to=CALLABLE_TARGET_KINDS,
)


# ---------------------------------------------------------------------------
# D106 — Missing Raises section for public-contract exceptions
# ---------------------------------------------------------------------------

D106 = _make_missing_fact_section_rule(
    code="D106",
    description="Missing Raises section for public-contract exceptions.",
    message="Missing Raises section for public-contract exceptions.",
    fact_accessor=lambda t: t.exceptions,
    section_kind=TypedSectionKind.RAISES,
    confidence_filter="high",
    exclude_evidence="reraise",
)


# ---------------------------------------------------------------------------
# D107 — Missing Warns section for public warnings
# ---------------------------------------------------------------------------

D107 = _make_missing_fact_section_rule(
    code="D107",
    description="Missing Warns section for public warnings.",
    message="Missing Warns section for public warnings.",
    fact_accessor=lambda t: t.warnings,
    section_kind=TypedSectionKind.WARNS,
    confidence_filter="high",
)


# ---------------------------------------------------------------------------
# D108 — Missing module Classes/Functions inventory when required
# ---------------------------------------------------------------------------


class D108:
    """Missing module Classes/Functions inventory when required."""

    metadata = RuleMetadata(
        code="D108",
        description="Missing module Classes/Functions inventory when required.",
        default_severity=Severity.CONVENTION,
        applies_to=frozenset({TargetKind.MODULE}),
        fixable=True,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:

        threshold = context.policy.options.get("inventory_threshold", 2)

        public_classes = sum(
            1
            for sym in target.module_symbols
            if sym.kind == "class" and sym.is_public
        )
        public_functions = sum(
            1
            for sym in target.module_symbols
            if sym.kind == "function" and sym.is_public
        )

        if target.docstring is None:
            return ()

        diagnostics: list[Diagnostic] = []

        if public_classes >= threshold and not target.docstring.has_inventory_section(
            InventorySectionKind.CLASSES
        ):
            diagnostics.append(
                make_diagnostic(
                    self, target, context,
                    "Missing Classes inventory section in module docstring.",
                )
            )

        if public_functions >= threshold and not target.docstring.has_inventory_section(
            InventorySectionKind.FUNCTIONS
        ):
            diagnostics.append(
                make_diagnostic(
                    self, target, context,
                    "Missing Functions inventory section in module docstring.",
                )
            )

        return tuple(diagnostics)


# ---------------------------------------------------------------------------
# D109 — Missing Attributes section where class attributes require documentation
# ---------------------------------------------------------------------------


class D109:
    """Missing Attributes section where class attributes require documentation."""

    metadata = RuleMetadata(
        code="D109",
        description="Missing Attributes section where class attributes require documentation.",
        default_severity=Severity.WARNING,
        applies_to=frozenset({TargetKind.CLASS}),
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:

        public_attrs = [a for a in target.attributes if a.is_public]
        if not public_attrs:
            return ()

        if target.docstring is None or not target.docstring.has_typed_section(TypedSectionKind.ATTRIBUTES):
            return (
                make_diagnostic(
                    self, target, context,
                    "Missing Attributes section for public class attributes.",
                ),
            )
        return ()


# ---------------------------------------------------------------------------
# D110 — Constructor parameters documented in __init__ instead of class docstring
# ---------------------------------------------------------------------------


class D110:
    """Constructor parameters documented in __init__ instead of class docstring."""

    metadata = RuleMetadata(
        code="D110",
        description="Constructor parameters documented in __init__ instead of class docstring.",
        default_severity=Severity.WARNING,
        applies_to=frozenset({TargetKind.CLASS}),
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:

        constructor = target.related.constructor
        if constructor is None:
            return ()

        constructor_has_params_section = (
            constructor.docstring is not None
            and constructor.docstring.has_typed_section(TypedSectionKind.PARAMETERS)
        )
        class_has_params_section = (
            target.docstring is not None
            and target.docstring.has_typed_section(TypedSectionKind.PARAMETERS)
        )

        if constructor_has_params_section and not class_has_params_section:
            return (
                make_diagnostic(
                    self, target, context,
                    "Constructor parameters are documented in __init__ "
                    "instead of the class docstring.",
                ),
            )
        return ()


# ---------------------------------------------------------------------------
# D111 — Missing deprecation directive for deprecated public API
# ---------------------------------------------------------------------------


class D111:
    """Missing deprecation directive for deprecated public API."""

    metadata = RuleMetadata(
        code="D111",
        description="Missing deprecation directive for deprecated public API.",
        default_severity=Severity.WARNING,
        applies_to=ALL_TARGET_KINDS,
        fixable=False,
    )

    def evaluate(
        self,
        target: LintTarget,
        context: RuleContext,
    ) -> tuple[Diagnostic, ...]:

        has_deprecated_decorator = any(
            "deprecated" in dec.lower() for dec in target.decorators
        )
        if not has_deprecated_decorator:
            return ()

        if target.docstring is None or target.docstring.deprecation is None:
            return (
                make_diagnostic(
                    self, target, context,
                    "Deprecated public API is missing a deprecation directive "
                    "in its docstring.",
                ),
            )
        return ()
