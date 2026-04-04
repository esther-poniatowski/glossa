# Configuration

## Sources and Precedence

Glossa resolves configuration from multiple sources. The following list orders
them from lowest to highest precedence:

1. Built-in defaults
2. `pyproject.toml` or `.glossa.yaml`
3. Per-file overrides
4. Inline suppressions
5. CLI flags

## `pyproject.toml`

```toml
[tool.glossa.rules]
select = ["D1xx", "D2xx", "D3xx", "D4xx", "D5xx"]
ignore = ["D205"]
section_order = [
    "Parameters", "Returns", "Yields", "Raises", "Warns",
    "Attributes", "Notes", "Warnings", "See Also", "Examples",
    "Classes", "Functions",
]

[tool.glossa.rules.severity_overrides]
D201 = "error"

[tool.glossa.rules.per_file_ignores]
"tests/**.py" = ["D102"]

[tool.glossa.rules.rule_options.D102]
include_test_functions = false
include_private_helpers = false

[tool.glossa.rules.rule_options.D104]
simple_property_requires_returns = false

[tool.glossa.rules.rule_options.D108]
inventory_threshold = 2

[tool.glossa.rules.rule_options.D306]
api_entry_modules = ["src/mypackage/api.py"]

[tool.glossa.rules.rule_options.D501]
trivial_dunder_allowlist = ["__repr__", "__str__"]

[tool.glossa.suppressions]
inline_enabled = true
directive_prefix = "glossa: ignore="

[tool.glossa.fix]
enabled = true
apply = "safe"
validate_after_apply = true

[tool.glossa.output]
format = "text"
color = true
show_source = true
```

## `.glossa.yaml`

```yaml
rules:
  select: ["D1xx", "D2xx", "D3xx", "D4xx", "D5xx"]
  ignore: ["D205"]
  section_order:
    - Parameters
    - Returns
    - Yields
    - Raises
    - Warns
    - Attributes
    - Notes
    - Warnings
    - See Also
    - Examples
    - Classes
    - Functions
  severity_overrides:
    D201: error
  per_file_ignores:
    "tests/**.py": ["D102"]
  rule_options:
    D102:
      include_test_functions: false
      include_private_helpers: false
    D104:
      simple_property_requires_returns: false
    D108:
      inventory_threshold: 2
    D306:
      api_entry_modules: ["src/mypackage/api.py"]
    D501:
      trivial_dunder_allowlist: ["__repr__", "__str__"]

suppressions:
  inline_enabled: true
  directive_prefix: "glossa: ignore="

fix:
  enabled: true
  apply: safe
  validate_after_apply: true

output:
  format: text
  color: true
  show_source: true
```

## Key Options

| Option | Description | Default |
| ------ | ----------- | ------- |
| `rules.select` | Rule codes or groups to enable. | All (`D1xx`--`D5xx`) |
| `rules.ignore` | Rule codes to disable. | None |
| `rules.section_order` | Canonical ordering of NumPy docstring sections. | See default list above |
| `rules.severity_overrides` | Map rule codes to `"convention"`, `"warning"`, or `"error"`. | None |
| `rules.per_file_ignores` | Disable specific rules for matching file globs. | None |
| `rules.rule_options` | Per-rule settings that resolve ambiguous guide policies. | None |
| `suppressions.inline_enabled` | Enable inline `glossa: ignore=` directives. | `true` |
| `suppressions.directive_prefix` | Prefix string for inline suppression comments. | `"glossa: ignore="` |
| `fix.enabled` | Enable or disable the fix pipeline globally. | `true` |
| `fix.apply` | Control fix behavior: `"never"`, `"safe"`, or `"unsafe"`. | `"safe"` |
| `fix.validate_after_apply` | Re-lint after applying fixes and reject fixes that do not resolve the diagnostic. | `true` |
| `output.format` | Output format (`"text"` or `"json"`). | `"text"` |
| `output.color` | Enable colored terminal output. | `true` |
| `output.show_source` | Include source context in text output. | `true` |

## Rule Options

Some rules accept per-rule options under `rules.rule_options.<CODE>`.

| Rule | Option | Type | Default | Description |
| ---- | ------ | ---- | ------- | ----------- |
| D102 | `include_test_functions` | bool | `false` | Require docstrings on test functions (`test_*`). |
| D102 | `include_private_helpers` | bool | `false` | Require docstrings on private (`_`-prefixed) callables. |
| D104 | `simple_property_requires_returns` | bool | `true` | Require a Returns section on simple properties. |
| D108 | `inventory_threshold` | int | `2` | Minimum public symbols before a Classes/Functions inventory section is required. |
| D306 | `api_entry_modules` | list[str] | `[]` | File globs identifying API entry-point modules where Examples sections are expected. |
| D501 | `trivial_dunder_allowlist` | list[str] | `[]` | Dunder method names exempt from the trivial-docstring check. |

## Inline Suppressions

Inline suppressions attach to a module header or target definition:

```python
def render(config: Config) -> str:  # glossa: ignore=D200,D205
    """Returns the rendered text"""
```
