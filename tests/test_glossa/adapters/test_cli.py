"""Tests for the command-line interface of glossa."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from glossa import __version__
from glossa.adapters import cli
from glossa.adapters.cli import EXIT_ERROR, EXIT_PROBLEM, EXIT_SUCCESS, app

SOURCE = '"""Module summary."""\n\n\ndef f():\n    """Return one"""\n    return 1\n'
FIXED = '"""Module summary."""\n\n\ndef f():\n    """Return one."""\n    return 1\n'


@pytest.fixture
def project(tmp_path, monkeypatch) -> Path:
    """A project whose settings select one fixable rule, entered from its `src` folder."""
    (tmp_path / "glossa.yml").write_text("rules:\n  select: [missing-period]\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "m.py").write_text(SOURCE, encoding="utf-8")
    monkeypatch.chdir(tmp_path / "src")
    monkeypatch.delenv("GLOSSA_ROOT", raising=False)
    return tmp_path


runner = CliRunner()


def test_version_short_form() -> None:
    result = runner.invoke(app, ["-v"])
    assert result.exit_code == EXIT_SUCCESS
    assert result.output.strip() == __version__


def test_lint_reads_paths_from_current_folder(project) -> None:
    result = runner.invoke(app, ["lint", "m.py", "--format", "json"])
    assert result.exit_code == EXIT_PROBLEM
    assert "src/m.py" in result.output


def test_lint_retires_short_format_option(project) -> None:
    assert runner.invoke(app, ["lint", "m.py", "-f", "json"]).exit_code == EXIT_ERROR


def test_lint_missing_path_is_an_error(project) -> None:
    assert runner.invoke(app, ["lint", "missing.py"]).exit_code == EXIT_ERROR


def test_absent_explicit_settings_file_is_an_error(project) -> None:
    result = runner.invoke(app, ["lint", "m.py", "--config", "absent.yml"])
    assert result.exit_code == EXIT_ERROR


def test_fix_dry_run_changes_nothing_and_exits_zero(project) -> None:
    result = runner.invoke(app, ["fix", "--dry-run"])
    assert result.exit_code == EXIT_SUCCESS
    assert "missing-period" in result.output
    assert (project / "src" / "m.py").read_text(encoding="utf-8") == SOURCE


def test_fix_check_changes_nothing_and_exits_one(project) -> None:
    assert runner.invoke(app, ["fix", "--check"]).exit_code == EXIT_PROBLEM
    assert (project / "src" / "m.py").read_text(encoding="utf-8") == SOURCE


def test_fix_without_terminal_and_without_yes_stops(project) -> None:
    result = runner.invoke(app, ["fix"])
    assert result.exit_code == EXIT_ERROR
    assert (project / "src" / "m.py").read_text(encoding="utf-8") == SOURCE


def test_fix_with_yes_applies(project) -> None:
    assert runner.invoke(app, ["fix", "--yes"]).exit_code == EXIT_SUCCESS
    assert (project / "src" / "m.py").read_text(encoding="utf-8") == FIXED


def test_fix_on_terminal_asks_for_confirmation(project, monkeypatch) -> None:
    monkeypatch.setattr(cli, "_interactive", lambda: True)
    declined = runner.invoke(app, ["fix"], input="n\n")
    assert declined.exit_code != EXIT_SUCCESS
    assert (project / "src" / "m.py").read_text(encoding="utf-8") == SOURCE
    assert runner.invoke(app, ["fix"], input="y\n").exit_code == EXIT_SUCCESS
    assert (project / "src" / "m.py").read_text(encoding="utf-8") == FIXED


def test_check_command_is_retired(project) -> None:
    assert runner.invoke(app, ["check"]).exit_code == EXIT_ERROR


def test_root_option_reads_settings_of_that_root(project, tmp_path_factory, monkeypatch) -> None:
    elsewhere = tmp_path_factory.mktemp("elsewhere")
    monkeypatch.chdir(elsewhere)
    result = runner.invoke(app, ["fix", "--check", "--root", str(project)])
    assert result.exit_code == EXIT_PROBLEM
