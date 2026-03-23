from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from glossa import __version__

app = typer.Typer(
    name="glossa",
    help="Docstring linter for Python projects.",
    add_completion=False,
    no_args_is_help=False,
)
console = Console()


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
    paths: list[str] = typer.Argument(
        default=["src"], help="Paths to lint (files or directories)."
    ),
    config: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to configuration file."
    ),
    select: Optional[str] = typer.Option(
        None, "--select", help="Comma-separated rule codes to select."
    ),
    ignore: Optional[str] = typer.Option(
        None, "--ignore", help="Comma-separated rule codes to ignore."
    ),
    output_format: str = typer.Option(
        "text", "--format", "-f", help="Output format: text or json."
    ),
    no_color: bool = typer.Option(
        False, "--no-color", help="Disable colored output."
    ),
) -> None:
    """Lint Python source files for docstring issues."""
    from glossa.adapters.bootstrap import bootstrap
    from glossa.adapters.formatters import format_json, format_text
    from glossa.application.linting import lint_file
    from glossa.errors import GlossaError

    try:
        application = bootstrap(config_path=config)
    except GlossaError as exc:
        console.print(f"[red]Configuration error:[/red] {exc}")
        raise typer.Exit(code=2)

    all_diagnostics = []
    operational_errors: list[str] = []

    for source_id in application.discovery.discover(paths):
        try:
            source_text = application.file_port.read(source_id)
            diagnostics = lint_file(
                source_id=source_id,
                source_text=source_text,
                extraction_port=application.extractor,
                config=application.config,
                registry=application.registry,
            )
            all_diagnostics.extend(diagnostics)
        except GlossaError as exc:
            operational_errors.append(f"{source_id}: {exc}")

    # Format output
    if output_format == "json":
        typer.echo(format_json(all_diagnostics))
    else:
        typer.echo(format_text(all_diagnostics, color=not no_color))

    # Report operational errors
    for err in operational_errors:
        console.print(f"[yellow]Warning:[/yellow] {err}", err=True)

    # Exit codes per design plan section 8.3
    if operational_errors and all_diagnostics:
        raise typer.Exit(code=4)
    elif operational_errors:
        raise typer.Exit(code=4)
    elif all_diagnostics:
        raise typer.Exit(code=1)
    else:
        raise typer.Exit(code=0)


@app.command()
def fix(
    paths: list[str] = typer.Argument(
        default=["src"], help="Paths to fix (files or directories)."
    ),
    config: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to configuration file."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be fixed without applying changes."
    ),
) -> None:
    """Apply automatic fixes to docstring issues."""
    from glossa.adapters.bootstrap import bootstrap
    from glossa.application.fixing import apply_fixes
    from glossa.application.linting import lint_file
    from glossa.errors import GlossaError

    try:
        application = bootstrap(config_path=config)
    except GlossaError as exc:
        console.print(f"[red]Configuration error:[/red] {exc}")
        raise typer.Exit(code=2)

    if not application.config.fix.enabled:
        console.print("[yellow]Fix mode is disabled in configuration.[/yellow]")
        raise typer.Exit(code=0)

    all_diagnostics = []
    for source_id in application.discovery.discover(paths):
        try:
            source_text = application.file_port.read(source_id)
            diagnostics = lint_file(
                source_id=source_id,
                source_text=source_text,
                extraction_port=application.extractor,
                config=application.config,
                registry=application.registry,
            )
            all_diagnostics.extend(diagnostics)
        except GlossaError:
            pass

    fixable = tuple(d for d in all_diagnostics if d.fix is not None)
    if not fixable:
        console.print("No fixable issues found.")
        raise typer.Exit(code=0)

    if dry_run:
        console.print(f"Found {len(fixable)} fixable issue(s):")
        for d in fixable:
            console.print(f"  {d.code}: {d.message} [{d.target.source_id}]")
        raise typer.Exit(code=1)

    results = apply_fixes(
        diagnostics=tuple(all_diagnostics),
        file_port=application.file_port,
        config=application.config,
    )

    applied_count = sum(len(r.applied) for r in results)
    rejected_count = sum(len(r.rejected) for r in results)
    console.print(f"Applied {applied_count} fix(es).")
    if rejected_count:
        console.print(f"[yellow]Skipped {rejected_count} conflicting fix(es).[/yellow]")

    raise typer.Exit(code=0 if not rejected_count else 1)


@app.command()
def check(
    paths: list[str] = typer.Argument(
        default=["src"], help="Paths to check."
    ),
    config: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to configuration file."
    ),
) -> None:
    """Check if files need fixing (non-zero exit if fixes available)."""
    from glossa.adapters.bootstrap import bootstrap
    from glossa.application.linting import lint_file
    from glossa.errors import GlossaError

    try:
        application = bootstrap(config_path=config)
    except GlossaError as exc:
        console.print(f"[red]Configuration error:[/red] {exc}")
        raise typer.Exit(code=2)

    fixable_count = 0
    for source_id in application.discovery.discover(paths):
        try:
            source_text = application.file_port.read(source_id)
            diagnostics = lint_file(
                source_id=source_id,
                source_text=source_text,
                extraction_port=application.extractor,
                config=application.config,
                registry=application.registry,
            )
            fixable_count += sum(1 for d in diagnostics if d.fix is not None)
        except GlossaError:
            pass

    if fixable_count:
        console.print(f"{fixable_count} issue(s) can be auto-fixed. Run `glossa fix` to apply.")
        raise typer.Exit(code=1)
    else:
        console.print("No fixable issues found.")
        raise typer.Exit(code=0)


@app.command()
def info() -> None:
    """Display version and platform diagnostics."""
    from glossa import info as get_info
    typer.echo(get_info())
