"""Tests for the root resolution and the settings file of glossa."""

from __future__ import annotations

from pathlib import Path

import pytest

from glossa.errors import ConfigurationError
from glossa.infrastructure.config import ConfigLoader, resolve_root


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_root_option_wins_over_variable_and_search(tmp_path) -> None:
    option, variable = tmp_path / "a", tmp_path / "b"
    option.mkdir()
    variable.mkdir()
    _write(tmp_path / "glossa.yml", "{}")
    root = resolve_root(Path("a"), {"GLOSSA_ROOT": str(variable)}, tmp_path)
    assert root == option.resolve()


def test_root_variable_wins_over_search(tmp_path) -> None:
    variable = tmp_path / "b"
    variable.mkdir()
    _write(tmp_path / "glossa.yml", "{}")
    assert resolve_root(None, {"GLOSSA_ROOT": str(variable)}, tmp_path) == variable.resolve()


@pytest.mark.parametrize("place", ["config/tools/glossa.yml", "glossa.toml"])
def test_root_is_nearest_ancestor_holding_settings(tmp_path, place) -> None:
    _write(tmp_path / place, "")
    nested = tmp_path / "src" / "package"
    nested.mkdir(parents=True)
    assert resolve_root(None, {}, nested) == tmp_path.resolve()


def test_root_falls_back_to_current_folder(tmp_path) -> None:
    assert resolve_root(None, {}, tmp_path) == tmp_path.resolve()


def test_root_option_naming_no_folder_is_an_error(tmp_path) -> None:
    with pytest.raises(ConfigurationError, match="--root"):
        resolve_root(Path("missing"), {}, tmp_path)


def test_loader_reads_settings_in_config_tools(tmp_path) -> None:
    _write(tmp_path / "config" / "tools" / "glossa.yml", "rules:\n  select: [presence]\n")
    assert ConfigLoader(tmp_path).load() == {"rules": {"select": ["presence"]}}


def test_loader_reads_toml_settings_at_top_level(tmp_path) -> None:
    _write(tmp_path / "glossa.toml", "[rules]\nselect = ['prose']\n")
    assert ConfigLoader(tmp_path).load() == {"rules": {"select": ["prose"]}}


def test_loader_without_settings_returns_defaults(tmp_path) -> None:
    _write(tmp_path / "pyproject.toml", "[tool.glossa.rules]\nselect = ['prose']\n")
    _write(tmp_path / ".glossa.yaml", "rules:\n  select: [prose]\n")
    assert ConfigLoader(tmp_path).load() == {}


def test_loader_rejects_competing_settings(tmp_path) -> None:
    first = _write(tmp_path / "config" / "tools" / "glossa.yml", "{}")
    second = _write(tmp_path / "glossa.yml", "{}")
    with pytest.raises(ConfigurationError) as excinfo:
        ConfigLoader(tmp_path).load()
    assert str(first) in str(excinfo.value) and str(second) in str(excinfo.value)


def test_loader_rejects_absent_explicit_file(tmp_path) -> None:
    with pytest.raises(ConfigurationError, match="does not exist"):
        ConfigLoader(tmp_path).load(str(tmp_path / "custom.yml"))
