"""Tests for file discovery with absolute and relative paths."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from glossa.infrastructure.discovery import FileDiscovery
from glossa.errors import DiscoveryError


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    """Create a minimal project structure for discovery tests.

    The project lives in a *subdirectory* of ``tmp_path`` so that sibling
    directories (e.g. ``tmp_path / "external"``) are genuinely outside the
    base path used by ``FileDiscovery``.
    """
    project = tmp_path / "project"
    project.mkdir()
    (project / "src").mkdir()
    (project / "src" / "mod.py").write_text("# module\n")
    (project / "src" / "sub").mkdir()
    (project / "src" / "sub" / "inner.py").write_text("# inner\n")
    (project / "src" / "sub" / "data.txt").write_text("not python\n")
    return project


def test_discover_relative_paths(tmp_project: Path) -> None:
    """Relative paths yield project-relative POSIX strings."""
    discovery = FileDiscovery(tmp_project)
    found = sorted(discovery.discover(["src"]))
    assert "src/mod.py" in found
    assert "src/sub/inner.py" in found
    assert all(f.endswith(".py") for f in found)


def test_discover_absolute_path_outside_base(tmp_project: Path, tmp_path: Path) -> None:
    """Absolute paths outside base_path yield absolute source IDs."""
    external = tmp_path / "external"
    external.mkdir()
    (external / "lib.py").write_text("# external lib\n")

    discovery = FileDiscovery(tmp_project)
    found = list(discovery.discover([str(external)]))
    assert len(found) == 1
    assert found[0] == str((external / "lib.py").resolve())


def test_discover_single_file(tmp_project: Path) -> None:
    """Discovering a single .py file yields just that file."""
    discovery = FileDiscovery(tmp_project)
    found = list(discovery.discover(["src/mod.py"]))
    assert found == ["src/mod.py"]


def test_discover_nonexistent_raises(tmp_project: Path) -> None:
    """Discovering a non-existent path raises DiscoveryError."""
    discovery = FileDiscovery(tmp_project)
    with pytest.raises(DiscoveryError):
        list(discovery.discover(["nope/missing.py"]))


def test_discover_excludes_patterns(tmp_project: Path) -> None:
    """Excluded glob patterns are skipped."""
    discovery = FileDiscovery(tmp_project)
    found = list(discovery.discover(["src"], exclude=("src/sub/*",)))
    assert "src/mod.py" in found
    assert not any("inner" in f for f in found)
