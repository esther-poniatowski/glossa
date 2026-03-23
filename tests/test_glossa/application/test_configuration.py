"""Tests for typed configuration resolution."""

from __future__ import annotations

import pytest

from glossa.application.configuration import FixApplyMode, OutputFormat, resolve_config
from glossa.errors import ConfigurationError


def test_resolve_config_rejects_invalid_output_format() -> None:
    with pytest.raises(ConfigurationError):
        resolve_config({"output": {"format": "xml"}})


def test_resolve_config_rejects_invalid_fix_mode() -> None:
    with pytest.raises(ConfigurationError):
        resolve_config({"fix": {"apply": "banana"}})


def test_resolve_config_rejects_unknown_builtin_rule_option() -> None:
    with pytest.raises(ConfigurationError):
        resolve_config({"rules": {"rule_options": {"D102": {"unexpected": True}}}})


def test_resolve_config_builds_typed_values() -> None:
    config = resolve_config(
        {
            "output": {"format": "json"},
            "fix": {"apply": "unsafe"},
            "rules": {
                "rule_options": {
                    "D102": {"include_test_functions": True},
                    "D306": {"api_entry_modules": ["src/**"]},
                }
            },
        }
    )

    assert config.output.format is OutputFormat.JSON
    assert config.fix.apply is FixApplyMode.UNSAFE
    assert config.rules.rule_options["D102"].include_test_functions is True
    assert config.rules.rule_options["D306"].api_entry_modules == ("src/**",)
