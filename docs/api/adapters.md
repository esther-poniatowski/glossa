<a id="adapters"></a>

# Adapters

User-facing adapters: CLI entry point, bootstrap wiring, and output formatters.

<a id="module-glossa.adapters.bootstrap"></a>

<a id="bootstrap"></a>

## Bootstrap

<a id="glossa.adapters.bootstrap.bootstrap"></a>

### glossa.adapters.bootstrap.bootstrap(base_path=None, config_path=None)

Build the fully-wired application service.

<a id="module-glossa.adapters.cli"></a>

<a id="cli"></a>

## CLI

<a id="glossa.adapters.cli.main_callback"></a>

### glossa.adapters.cli.main_callback(ctx, version=<typer.models.OptionInfo object>)

Glossa - Python docstring linter for NumPy-style docstrings.

<a id="glossa.adapters.cli.lint"></a>

### glossa.adapters.cli.lint(paths=<typer.models.ArgumentInfo object>, config=<typer.models.OptionInfo object>, select=<typer.models.OptionInfo object>, ignore=<typer.models.OptionInfo object>, output_format=<typer.models.OptionInfo object>, no_color=<typer.models.OptionInfo object>)

Lint Python source files for docstring issues.

<a id="glossa.adapters.cli.fix"></a>

### glossa.adapters.cli.fix(paths=<typer.models.ArgumentInfo object>, config=<typer.models.OptionInfo object>, dry_run=<typer.models.OptionInfo object>)

Apply automatic fixes to docstring issues.

<a id="glossa.adapters.cli.check"></a>

### glossa.adapters.cli.check(paths=<typer.models.ArgumentInfo object>, config=<typer.models.OptionInfo object>)

Check if files need fixing (non-zero exit if fixes available).

<a id="glossa.adapters.cli.info"></a>

### glossa.adapters.cli.info()

Display version and platform diagnostics.

<a id="module-glossa.adapters.formatters"></a>

<a id="formatters"></a>

## Formatters

<a id="glossa.adapters.formatters.format_text"></a>

### glossa.adapters.formatters.format_text(diagnostics, show_source=True)

Format diagnostics as human-readable text.

<a id="glossa.adapters.formatters.format_json"></a>

### glossa.adapters.formatters.format_json(diagnostics)

Format diagnostics as JSON.
