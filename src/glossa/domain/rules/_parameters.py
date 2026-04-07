"""Shared parameter filtering utilities for rule implementations."""

from __future__ import annotations

from glossa.domain.contracts import LintTarget, ParameterFact, TargetKind


def _excluded_names(target: LintTarget) -> frozenset[str]:
    """Return parameter names that should be excluded from documentation checks.

    ``self`` is excluded for regular (non-static) methods.  ``cls`` is excluded
    only for classmethods, **not** for plain functions that happen to use
    ``cls`` as a parameter name.
    """
    if target.kind not in (TargetKind.METHOD, TargetKind.PROPERTY):
        return frozenset()

    decorators = target.decorators
    if "classmethod" in decorators:
        return frozenset({"cls"})
    if "staticmethod" in decorators:
        return frozenset()

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
    # For constructor params, always exclude ``self``.
    return frozenset(
        p.name for p in constructor.signature.parameters
        if p.name != "self"
    )
