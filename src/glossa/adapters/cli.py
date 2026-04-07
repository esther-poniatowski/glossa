from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

from glossa import __version__
from glossa.application.configuration import DEFAULT_PATHS, OutputFormat

app = typer.Typer(
    name="glossa",
    help="Docstring linter for Python projects.",
    add_completion=False,
    no_args_is_help=False,
)
console = Console()


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


def _bootstrap_or_exit(config_path: str | None):
    from glossa.adapters.bootstrap import bootstrap
    from glossa.errors import GlossaError

    try:
        return bootstrap(config_path=config_path)
    except GlossaError as exc:
        console.print(f"[red]Startup error:[/red] {exc}")
        raise typer.Exit(code=2)


def _report_issues(issues) -> None:
    for issue in issues:
        prefix = f"{issue.source_id}: " if issue.source_id is not None else ""
        console.print(f"[yellow]Warning:[/yellow] {prefix}{issue.message}", err=True)


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
        default=None, help="Paths to lint (files or directories)."
    ),
    config: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to configuration file."
    ),
    select: Optional[str] = typer.Option(
        None, "--select", help="Comma-separated rule names or groups to select."
    ),
    ignore: Optional[str] = typer.Option(
        None, "--ignore", help="Comma-separated rule names or groups to ignore."
    ),
    output_format: Optional[str] = typer.Option(
        None, "--format", "-f", help="Output format: text or json."
    ),
    no_color: bool = typer.Option(
        False, "--no-color", help="Disable colored output."
    ),
) -> None:
    """Lint Python source files for docstring issues."""
    from glossa.adapters.formatters import format_json, format_text

    paths = paths or list(DEFAULT_PATHS)
    service = _bootstrap_or_exit(config)
    format_override = _output_format(output_format) if output_format is not None else None
    result = service.lint_paths(
        paths,
        select=_parse_names(select),
        ignore=_parse_names(ignore),
        output_format=format_override,
        color=False if no_color else None,
    )
    all_diagnostics = result.diagnostics
    effective_config = result.effective_config

    # Format output
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

    # Exit codes: 0 = clean, 1 = diagnostics found, 4 = operational issues
    if result.operational_issues:
        raise typer.Exit(code=4)
    elif all_diagnostics:
        raise typer.Exit(code=1)
    else:
        raise typer.Exit(code=0)


@app.command()
def fix(
    paths: Optional[list[str]] = typer.Argument(
        default=None, help="Paths to fix (files or directories)."
    ),
    config: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to configuration file."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be fixed without applying changes."
    ),
) -> None:
    """Apply automatic fixes to docstring issues."""
    paths = paths or list(DEFAULT_PATHS)
    service = _bootstrap_or_exit(config)
    result = service.fix_paths(paths, dry_run=dry_run)

    if not result.fix_enabled:
        console.print("[yellow]Fix mode is disabled in configuration.[/yellow]")
        raise typer.Exit(code=0)

    _report_issues(result.operational_issues)

    fixable = result.fixable_diagnostics
    if not fixable:
        console.print("No fixable issues found.")
        raise typer.Exit(code=4 if result.operational_issues else 0)

    if dry_run:
        console.print(f"Found {len(fixable)} fixable issue(s):")
        for d in fixable:
            console.print(f"  {d.rule}: {d.message} \\[{d.target.source_id}]")
        raise typer.Exit(code=4 if result.operational_issues else 1)

    console.print(f"Applied {result.applied_count} fix(es).")
    if result.rejected_count:
        console.print(
            f"[yellow]Skipped {result.rejected_count} fix(es) due to conflicts or validation failures.[/yellow]"
        )

    if result.operational_issues:
        raise typer.Exit(code=4)
    raise typer.Exit(code=0 if not result.rejected_count else 1)


@app.command()
def check(
    paths: Optional[list[str]] = typer.Argument(
        default=None, help="Paths to check."
    ),
    config: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to configuration file."
    ),
) -> None:
    """Check if files need fixing (non-zero exit if fixes available)."""
    paths = paths or list(DEFAULT_PATHS)
    service = _bootstrap_or_exit(config)
    result = service.check_paths(paths)
    _report_issues(result.operational_issues)

    if result.fixable_count:
        console.print(f"{result.fixable_count} issue(s) can be auto-fixed. Run `glossa fix` to apply.")
        raise typer.Exit(code=1)
    if result.operational_issues:
        raise typer.Exit(code=4)
    console.print("No fixable issues found.")
    raise typer.Exit(code=0)


@app.command()
def info() -> None:
    """Display version and platform diagnostics."""
    from glossa import info as get_info
    typer.echo(get_info())
