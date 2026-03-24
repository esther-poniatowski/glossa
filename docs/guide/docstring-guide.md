# Docstring Guide

Canonical docstring conventions for all Python projects in the ecosystem. Based on
NumPy-style docstrings (Napoleon with `napoleon_numpy_docstring = True`,
`napoleon_google_docstring = False`).

## 1. General Rules

### 1.1 Format

All docstrings use NumPy style. This is enforced by the Sphinx Napoleon extension
configured in every project's `docs/conf.py`.

### 1.2 Tone

Use **imperative mood** for summary lines:

- "Return the configuration." (not "Returns the configuration.")
- "Compute the loss function." (not "Computes the loss function.")
- "Load parameters from a YAML file." (not "Loads parameters...")

The imperative mood follows PEP 257 and the numpydoc standard.

Use **impersonal voice** throughout. Avoid first person ("we compute...") and
second person ("you can..."). Write "The function computes..." or simply
"Compute...".

### 1.3 Types in Docstrings

**Always include types in `Parameters`, `Returns`, `Yields`, and `Attributes`
sections**, even when the function signature already has type annotations.
This follows the numpydoc standard, which documents all three sections
symmetrically as typed entries (`name : type`).

```python
def load(path: Path, strict: bool = True) -> Config:
    """Load configuration from a YAML file.

    Parameters
    ----------
    path : Path
        Path to the YAML configuration file.
    strict : bool, default True
        If True, raise on unknown keys.

    Returns
    -------
    Config
        The parsed configuration object.
    """
```

Rationale:

- Matches published numpydoc examples and tooling expectations.
- Keeps generated documentation readable in contexts where annotations are
  not displayed exactly as intended by the renderer.
- Avoids divergence between runtime documentation and numpydoc linting.

Types should be **as precise as possible**. Use the same syntax as in type
annotations (`str | None`, `list[int]`, `dict[str, Any]`). For default
values, use the `default` notation: `param : type, default value`.

### 1.4 Minimum Bar

Public modules, public classes, and public functions/methods must have docstrings.
This is consistent with PEP 257 and numpydoc.

Constructor parameters are documented in the **class docstring**, not in
`__init__`. Napoleon's `napoleon_include_init_with_doc` setting supports either
convention; this ecosystem uses the class docstring.

The following elements follow **project policy** (not universal standard):

| Element | Policy |
| ------- | ------ |
| Private helper (`_foo`) | Yes — document when behavior is non-trivial |
| Special methods (`__repr__`, `__call__`, etc.) | Yes — document when behavior is non-trivial |
| Test functions | Yes |
| Trivial property accessor | Optional |

## 2. Module Docstrings

### 2.1 Template

```python
"""
Short summary line in imperative mood.

Extended description (optional). Explain the module's purpose, scope, and
relationship to other modules in the package.

Classes
-------
ClassName
    One-line description.

Functions
---------
function_name
    One-line description.

See Also
--------
related_module : Related functionality.
"""
```

### 2.2 Rules

- **Always present** for public modules.
- Use a **one-line summary** followed by an optional extended description.
- Include a **`Classes` and/or `Functions` inventory** when the module has more
  than two public symbols. This helps readers navigate without scrolling.
- Use **RST-style section headers** (`-------`) for the inventory sections.
  This is the NumPy docstring convention and renders correctly with Napoleon.
- Include **`See Also`** to cross-reference related modules when useful.
- Do **not** include `Examples` in module docstrings unless the module is a
  top-level API entry point (e.g., `__init__.py`).

## 3. Class Docstrings

### 3.1 Template

```python
class Pipeline:
    """Short summary of the class in imperative mood.

    Extended description (optional). Explain the class's role, design intent,
    and typical usage context.

    Parameters
    ----------
    name : str
        Human-readable name for the pipeline.
    steps : list[Step]
        Ordered sequence of processing steps.

    Attributes
    ----------
    status : PipelineStatus
        Current execution status. Updated by ``run()``.

    Examples
    --------
    >>> pipeline = Pipeline("preprocess", steps=[step_a, step_b])
    >>> pipeline.run()
    """
```

### 3.2 Rules

- Document **constructor parameters in the class docstring**, not in `__init__`.
  Either location is valid; this ecosystem uses the class docstring for
  consistency across all projects.
- Include **`Attributes`** for public instance attributes that are not constructor
  parameters, or for attributes whose semantics differ from the parameter name.
- Include **`Examples`** for classes that serve as primary API entry points or
  have non-trivial construction patterns.
- Do **not** document every inherited method. Document only methods that override
  or extend parent behavior.

## 4. Function and Method Docstrings

### 4.1 Template

```python
def resolve(config: Config, overrides: dict[str, Any] | None = None) -> Config:
    """Resolve configuration by applying overrides and validating constraints.

    Merge user-provided overrides into the base configuration, then validate
    all relational constraints between parameters.

    Parameters
    ----------
    config : Config
        Base configuration to resolve.
    overrides : dict[str, Any] | None, default None
        Key-value pairs to override in the base configuration. Keys use
        dot-notation for nested access.

    Returns
    -------
    Config
        The resolved and validated configuration.

    Raises
    ------
    ValidationError
        If any relational constraint is violated after merging.

    See Also
    --------
    validate : Validate a configuration without merging.

    Examples
    --------
    >>> resolved = resolve(base_config, {"model.lr": 0.001})
    """
```

### 4.2 Rules

- **Summary line**: one line, imperative mood, ending with a period.
- **Extended description**: optional. Include only when the summary is insufficient
  to understand the function's behavior.
- **`Parameters`**: required for all public functions with parameters. Always
  include the type (`name : type`). Describe semantics, not just the type.
- **`Returns`**: required for all functions that return a value. Include the type
  as the section entry name (NumPy convention) and a description.
- **`Raises`**: document exceptions that are **non-obvious or part of the public
  contract**. The criterion is interface relevance, not exception class. A
  `ValueError` raised for a predictable misuse mode (e.g., unsupported enum
  value) is worth documenting; a `TypeError` that arises incidentally from
  passing the wrong type to a standard library call is not. Domain-specific exceptions
  (`ConfigError`, `ValidationError`, `BuildError`) should always be documented.
- **`See Also`**: include for closely related routines, alternative APIs, or
  companion functions that help navigation — especially those users may not
  otherwise discover in the same or other submodules.
- **`Examples`**: include for functions that benefit from usage demonstration (even private helpers if they have non-trivial logic). Use doctest format for code snippets.
- **`Notes`**: use sparingly for algorithmic explanations, performance
  characteristics, or important caveats.
- **Deprecation**: use the `.. deprecated::` directive in a deprecation warning
  block before the extended summary, per numpydoc convention.
- **`Warns`**: document warnings emitted at runtime (e.g., `UserWarning`,
  `DeprecationWarning`), symmetric with `Raises`.
- **`Warnings`**: use for prose cautions, pitfalls, or common misuse patterns.

## 5. Property Docstrings

### 5.1 Template

For simple properties, a short declarative summary is natural:

```python
@property
def is_valid(self) -> bool:
    """Whether all constraints are satisfied."""
```

For properties with non-trivial logic or important caveats, a richer docstring
with `Returns`, `Raises`, or `Notes` sections is appropriate:

```python
@property
def engine(self) -> Engine:
    """Resolve the LaTeX engine for this document.

    Returns
    -------
    Engine
        The detected engine, falling back to pdflatex if no markers are found.

    Raises
    ------
    EngineConflictError
        If the preamble contains conflicting engine markers.
    """
```

### 5.2 Rules

- A **short declarative summary** ("Whether...", "The current...", "Number of...")
  is the preferred form for data-like properties.
- Richer docstrings with `Returns`, `Raises`, or `Notes` sections are acceptable
  when the property involves computation, side effects, or non-obvious behavior.
- Properties are documented like attributes by Sphinx autodoc and Napoleon; both
  short and extended forms render correctly.

## 6. Inline Comments

### 6.1 Rules

- Use inline comments **only for non-obvious logic**: algorithmic steps,
  workarounds, performance trade-offs, or domain-specific decisions.
- Do **not** restate what is trivial from the code. `# Increment counter` above
  `counter += 1` adds no value.
- Use **step markers** (`# Step 1: ...`, `# Step 2: ...`) for multi-phase
  algorithms where the logical flow benefits from explicit segmentation.
- Prefer self-documenting code (clear variable names, small functions) over
  compensatory comments.

## 7. Anti-Patterns

Avoid these patterns across all projects:

| Anti-pattern | Example | Fix |
| ------------ | ------- | --- |
| Empty docstrings | `"""."""` or `""""""` | Write a real docstring |
| Trivial docstrings on dunder methods | `def __repr__(self): """Return repr."""` | Remove or document only when behavior is non-trivial (e.g., custom `__getitem__`, `__call__`, `__enter__`) |
| RST directives where a NumPy section exists | `.. note::` instead of `Notes` section | Prefer NumPy sections (`Notes`, `Examples`, `Warnings`) for consistency; RST directives are valid but less uniform |
| Markdown in docstrings | `**bold**` or `` `code` `` | Use RST inline markup (``double backticks``) |
| First-person voice | `"""We compute the loss..."""` | `"""Compute the loss..."""` |
| Redundant `Returns None` | Documenting `-> None` return | Omit `Returns` section entirely |
