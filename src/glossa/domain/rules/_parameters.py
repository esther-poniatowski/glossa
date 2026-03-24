"""Shared parameter filtering utilities for rule implementations."""

from __future__ import annotations

from glossa.application.contracts import LintTarget, ParameterFact, TargetKind

_EXCLUDED_PARAM_NAMES: frozenset[str] = frozenset({"self", "cls"})


def documentable_param_names(target: LintTarget) -> frozenset[str]:
    """Return documentable parameter names, with constructor fallback for classes."""
    names = _sig_param_names(target)
    if target.kind is TargetKind.CLASS:
        names = names | _constructor_param_names(target)
    return names


def documentable_params(target: LintTarget) -> tuple[ParameterFact, ...]:
    """Return documentable ParameterFact objects, with constructor fallback for classes."""
    if target.signature is not None:
        params = _filter_params(target.signature.parameters)
        if params:
            return params

    if target.kind is TargetKind.CLASS:
        constructor = target.related.constructor
        if constructor is not None and constructor.signature is not None:
            return _filter_params(constructor.signature.parameters)

    if target.signature is not None:
        return _filter_params(target.signature.parameters)

    return ()


def _filter_params(params: tuple[ParameterFact, ...]) -> tuple[ParameterFact, ...]:
    return tuple(p for p in params if p.name not in _EXCLUDED_PARAM_NAMES)


def _sig_param_names(target: LintTarget) -> frozenset[str]:
    if target.signature is None:
        return frozenset()
    return frozenset(
        p.name for p in target.signature.parameters
        if p.name not in _EXCLUDED_PARAM_NAMES
    )


def _constructor_param_names(target: LintTarget) -> frozenset[str]:
    constructor = target.related.constructor
    if constructor is None or constructor.signature is None:
        return frozenset()
    return frozenset(
        p.name for p in constructor.signature.parameters
        if p.name not in _EXCLUDED_PARAM_NAMES
    )
