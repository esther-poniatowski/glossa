"""Tests for the traceability matrix validation."""

from glossa.application.registry import build_builtin_registry
from glossa.domain.traceability import validate_matrix_codes


def test_traceability_matrix_codes_exist_in_registry():
    registry = build_builtin_registry()
    registered = frozenset(rule.metadata.name for rule in registry.all_rules())
    orphaned = validate_matrix_codes(registered)
    assert not orphaned, f"Traceability matrix references unregistered rules: {orphaned}"
