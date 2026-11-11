"""Command-line interface of glossa.

Commands
--------
lint : Report the docstring issues of Python source files.
fix : Apply the automatic fixes, or list them with ``--dry-run`` or ``--check``.
info : Display version and platform diagnostics.

The exit status is 0 on success, 1 when a check finds a problem, and 2 on a
usage or configuration error, or when a file cannot be analyzed.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Optional

import typer
from rich.console import Console

from glossa import __version__
from glossa.application.configuration import DEFAULT_PATHS, OutputFormat

if TYPE_CHECKING:
    from glossa.application.service import GlossaService, OperationalIssue

EXIT_SUCCESS = 0
"""Exit status of a run that found nothing to report or to change."""

EXIT_PROBLEM = 1
"""Exit status of a run whose check found a problem."""

EXIT_ERROR = 2
"""Exit status of a usage or configuration error, or of a file that cannot be analyzed."""

app = typer.Typer(
    name="glossa",
    help="Docstring linter for Python projects.",
    add_completion=False,
    no_args_is_help=False,
)
console = Console()
error_console = Console(stderr=True)

ROOT_OPTION = typer.Option(
    None,
    "--root",
    "-r",
    help=(
        "Folder from which glossa finds its configuration file and resolves the paths written "
        "in it; GLOSSA_ROOT, then the nearest ancestor holding a configuration file, then the "
        "current folder by default."
    ),
)
CONFIG_OPTION = typer.Option(
    None,
    "--config",
    "-c",
    help=(
        "Configuration file of glossa; config/tools/glossa.yml or glossa.yml below the root by "
        "default."
    ),
)


def _parse_names(value: Optional[str]) -> tuple[str, ...] | None:
    if value is None:
        return None
    names = tuple(name.strip() for name in value.split(",") if name.strip())
    return names or None


def _output_format(value: str) -> OutputFormat:
    try:
        return OutputFormat(value)
    except ValueError as exc:
        raise typer.BadParameter("Output format must be 'text' or 'json'.") from exc


def _bootstrap_or_exit(root: Path | None, config_path: str | None) -> GlossaService:
    from glossa.adapters.bootstrap import bootstrap
    from glossa.errors import GlossaError
    from glossa.infrastructure.config import resolve_root

    try:
        base_path = resolve_root(root, os.environ, Path.cwd())
        return bootstrap(base_path=base_path, config_path=config_path)
    except GlossaError as exc:
        error_console.print(f"[red]Startup error:[/red] {exc}")
        raise typer.Exit(code=EXIT_ERROR)


def _targets(paths: Optional[list[str]]) -> list[str]:
    """Return the paths to analyze: those given, read from the current folder, or the defaults
    below the root."""
    if not paths:
        return list(DEFAULT_PATHS)
    return [str(Path(path).resolve()) for path in paths]


def _report_issues(issues: Iterable[OperationalIssue]) -> None:
    for issue in issues:
        prefix = f"{issue.source_id}: " if issue.source_id is not None else ""
        error_console.print(f"[yellow]Warning:[/yellow] {prefix}{issue.message}")


def _interactive() -> bool:
    """Return whether a person can answer a confirmation on the standard input."""
    return sys.stdin.isatty()


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", "-v", help="Show the version and exit."
    ),
) -> None:
    """Glossa - Python docstring linter for NumPy-style docstrings."""
    if version:
        typer.echo(__version__)
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command()
def lint(
    paths: Optional[list[str]] = typer.Argument(
        default=None, help="Paths to lint (files or directories); `src` below the root by default."
    ),
    root: Optional[Path] = ROOT_OPTION,
    config: Optional[str] = CONFIG_OPTION,
    select: Optional[str] = typer.Option(
        None, "--select", help="Comma-separated rule names or groups to select."
    ),
    ignore: Optional[str] = typer.Option(
        None, "--ignore", help="Comma-separated rule names or groups to ignore."
    ),
    output_format: Optional[str] = typer.Option(
        None, "--format", help="Output format: text or json."
    ),
    no_color: bool = typer.Option(
        False, "--no-color", help="Disable colored output."
    ),
) -> None:
    """Lint Python source files for docstring issues.

    The exit status is 0 without diagnostics, 1 with diagnostics, and 2 when a
    path or a file cannot be analyzed.
    """
    from glossa.adapters.formatters import format_json, format_text

    service = _bootstrap_or_exit(root, config)
    format_override = _output_format(output_format) if output_format is not None else None
    result = service.lint_paths(
        _targets(paths),
        select=_parse_names(select),
        ignore=_parse_names(ignore),
        output_format=format_override,
        color=False if no_color else None,
    )
    all_diagnostics = result.diagnostics
    effective_config = result.effective_config

    if effective_config.output.format is OutputFormat.JSON:
        typer.echo(format_json(all_diagnostics))
    else:
        typer.echo(
            format_text(
                all_diagnostics,
                show_source=effective_config.output.show_source,
            )
        )

    _report_issues(result.operational_issues)

    if result.operational_issues:
        raise typer.Exit(code=EXIT_ERROR)
    raise typer.Exit(code=EXIT_PROBLEM if all_diagnostics else EXIT_SUCCESS)


@app.command()
def fix(
    paths: Optional[list[str]] = typer.Argument(
        default=None, help="Paths to fix (files or directories); `src` below the root by default."
    ),
    root: Optional[Path] = ROOT_OPTION,
    config: Optional[str] = CONFIG_OPTION,
    dry_run: bool = typer.Option(
        False, "--dry-run", help="List the fixable issues without changing any file."
    ),
    check: bool = typer.Option(
        False,
        "--check",
        help="List the fixable issues without changing any file, and exit 1 when one exists.",
    ),
    yes: bool = typer.Option(
        False, "--yes", help="Apply the fixes without asking for a confirmation."
    ),
) -> None:
    """Apply automatic fixes to docstring issues.

    The fixes rewrite source files, so the command asks for a confirmation on a
    terminal; `--yes` answers it, and without a terminal and without `--yes`
    the command stops with status 2. With `--dry-run` it changes nothing and
    exits 0; with `--check` it changes nothing and exits 1 when a fix is
    available. Applying exits 1 when a fix was skipped, and 2 when a path or a
    file cannot be analyzed.
    """
    if dry_run and check:
        error_console.print("[red]Usage error:[/red] --dry-run and --check exclude each other.")
        raise typer.Exit(code=EXIT_ERROR)
    service = _bootstrap_or_exit(root, config)
    writes = not (dry_run or check)
    if writes and not yes and not _interactive():
        error_console.print(
            "[red]Usage error:[/red] fix rewrites source files and needs a confirmation; "
            "run it on a terminal, or pass --yes."
        )
        raise typer.Exit(code=EXIT_ERROR)

    targets = _targets(paths)
    preview = service.fix_paths(targets, dry_run=True)
    if not preview.fix_enabled:
        console.print("[yellow]Fix mode is disabled in configuration.[/yellow]")
        raise typer.Exit(code=EXIT_SUCCESS)

    fixable = preview.fixable_diagnostics
    if not writes or not fixable:
        _report_issues(preview.operational_issues)
        if not fixable:
            console.print("No fixable issues found.")
        else:
            console.print(f"Found {len(fixable)} fixable issue(s):")
            for d in fixable:
                console.print(f"  {d.rule}: {d.message} \\[{d.target.source_id}]")
        if preview.operational_issues:
            raise typer.Exit(code=EXIT_ERROR)
        raise typer.Exit(code=EXIT_PROBLEM if check and fixable else EXIT_SUCCESS)

    if not yes:
        files = len({d.target.source_id for d in fixable})
        typer.confirm(f"Apply {len(fixable)} fix(es) to {files} file(s)?", abort=True)

    result = service.fix_paths(targets)
    _report_issues(result.operational_issues)
    console.print(f"Applied {result.applied_count} fix(es).")
    if result.rejected_count:
        console.print(
            f"[yellow]Skipped {result.rejected_count} fix(es) due to conflicts or validation failures.[/yellow]"
        )

    if result.operational_issues:
        raise typer.Exit(code=EXIT_ERROR)
    raise typer.Exit(code=EXIT_PROBLEM if result.rejected_count else EXIT_SUCCESS)


@app.command()
def info() -> None:
    """Display version and platform diagnostics."""
    from glossa import info as get_info
    typer.echo(get_info())
