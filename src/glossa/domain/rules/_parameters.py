"""Shared parameter filtering utilities for rule implementations."""

from __future__ import annotations

from glossa.domain.contracts import LintTarget, ParameterFact, TargetKind
from glossa.domain.models import TypedSectionKind


# Methods that implicitly receive ``cls`` as the first parameter even
# without an explicit ``@classmethod`` decorator.
_IMPLICIT_CLS_METHODS: frozenset[str] = frozenset({
    "__new__", "__init_subclass__", "__class_getitem__",
})


def _excluded_names(target: LintTarget) -> frozenset[str]:
    """Return parameter names that should be excluded from documentation checks.

    ``self`` is excluded for regular (non-static) methods.  ``cls`` is excluded
    for classmethods and for special methods that implicitly receive ``cls``
    (``__new__``, ``__init_subclass__``, ``__class_getitem__``).
    """
    if target.kind not in (TargetKind.METHOD, TargetKind.PROPERTY):
        return frozenset()

    decorators = target.decorators
    if "classmethod" in decorators:
        return frozenset({"cls"})
    if "staticmethod" in decorators:
        return frozenset()

    # Special methods that implicitly take ``cls`` without @classmethod.
    method_name = target.ref.symbol_path[-1] if target.ref.symbol_path else ""
    if method_name in _IMPLICIT_CLS_METHODS:
        return frozenset({"cls"})

    return frozenset({"self"})


def documentable_param_names(target: LintTarget) -> frozenset[str]:
    """Return documentable parameter names, with constructor fallback for classes."""
    names = _sig_param_names(target)
    if target.kind is TargetKind.CLASS:
        names = names | _constructor_param_names(target)
    return names


def documentable_params(target: LintTarget) -> tuple[ParameterFact, ...]:
    """Return documentable ParameterFact objects, with constructor fallback for classes."""
    if target.signature is not None:
        params = _filter_params(target.signature.parameters, target)
        if params:
            return params

    if target.kind is TargetKind.CLASS:
        constructor = target.related.constructor
        if constructor is not None and constructor.signature is not None:
            return _filter_params(constructor.signature.parameters, target)

    if target.signature is not None:
        return _filter_params(target.signature.parameters, target)

    return ()


def _filter_params(
    params: tuple[ParameterFact, ...], target: LintTarget,
) -> tuple[ParameterFact, ...]:
    excluded = _excluded_names(target)
    return tuple(p for p in params if p.name not in excluded)


def _sig_param_names(target: LintTarget) -> frozenset[str]:
    if target.signature is None:
        return frozenset()
    excluded = _excluded_names(target)
    return frozenset(
        p.name for p in target.signature.parameters
        if p.name not in excluded
    )


def _constructor_param_names(target: LintTarget) -> frozenset[str]:
    constructor = target.related.constructor
    if constructor is None or constructor.signature is None:
        return frozenset()
    # Exclude ``self`` (for __init__) and ``cls`` (for __new__).
    return frozenset(
        p.name for p in constructor.signature.parameters
        if p.name not in ("self", "cls")
    )


def init_params_on_class(target: LintTarget) -> bool:
    """Check if this is a constructor whose params are documented on the class.

    Returns ``True`` when the target is an ``__init__`` or ``__new__`` method
    and the parent class docstring already contains a Parameters section, so
    per-parameter rules should be suppressed on the constructor itself.
    """
    if target.kind is not TargetKind.METHOD:
        return False
    if not target.ref.symbol_path or target.ref.symbol_path[-1] not in ("__init__", "__new__"):
        return False
    parent = target.related.parent
    if parent is None or parent.docstring is None:
        return False
    return parent.docstring.has_typed_section(TypedSectionKind.PARAMETERS)
