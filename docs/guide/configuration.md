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
select = ["presence", "prose", "structure", "typed-entries", "anti-patterns"]
ignore = ["markdown-in-docstring"]
section_order = [
    "Parameters", "Returns", "Yields", "Raises", "Warns",
    "Attributes", "Usage", "Notes", "Warnings", "See Also", "Examples",
    "Classes", "Functions",
]

[tool.glossa.rules.severity_overrides]
missing-period = "error"

[tool.glossa.rules.per_file_ignores]
"tests/**.py" = ["missing-callable-docstring"]

[tool.glossa.rules.rule_options.missing-callable-docstring]
include_test_functions = false
include_private_helpers = false

[tool.glossa.rules.rule_options.missing-returns-section]
simple_property_requires_returns = false

[tool.glossa.rules.rule_options.missing-module-inventory]
inventory_threshold = 2

[tool.glossa.rules.rule_options.examples-in-non-entry-module]
api_entry_modules = ["src/mypackage/api.py"]

[tool.glossa.rules.rule_options.trivial-dunder-docstring]
trivial_dunder_allowlist = ["__repr__", "__str__"]

[tool.glossa.parsing.section_aliases]
Hint = "Notes"
"Return Value" = "Returns"

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
  select: ["presence", "prose", "structure", "typed-entries", "anti-patterns"]
  ignore: ["markdown-in-docstring"]
  section_order:
    - Parameters
    - Returns
    - Yields
    - Raises
    - Warns
    - Attributes
    - Usage
    - Notes
    - Warnings
    - See Also
    - Examples
    - Classes
    - Functions
  severity_overrides:
    missing-period: error
  per_file_ignores:
    "tests/**.py": ["missing-callable-docstring"]
  rule_options:
    missing-callable-docstring:
      include_test_functions: false
      include_private_helpers: false
    missing-returns-section:
      simple_property_requires_returns: false
    missing-module-inventory:
      inventory_threshold: 2
    examples-in-non-entry-module:
      api_entry_modules: ["src/mypackage/api.py"]
    trivial-dunder-docstring:
      trivial_dunder_allowlist: ["__repr__", "__str__"]

parsing:
  section_aliases:
    Hint: Notes
    "Return Value": Returns

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
| `rules.select` | Rule names or groups to enable. | All (`presence`, `prose`, `structure`, `typed-entries`, `anti-patterns`) |
| `rules.ignore` | Rule names or groups to disable. | None |
| `rules.section_order` | Canonical ordering of NumPy docstring sections. | See default list above |
| `rules.severity_overrides` | Map rule names to `"convention"`, `"warning"`, or `"error"`. | None |
| `rules.per_file_ignores` | Disable specific rules for matching file globs. | None |
| `rules.rule_options` | Per-rule settings that resolve ambiguous guide policies. | None |
| `parsing.section_aliases` | Map non-standard section headings to canonical names. | None |
| `suppressions.inline_enabled` | Enable inline `glossa: ignore=` directives. | `true` |
| `suppressions.directive_prefix` | Prefix string for inline suppression comments. | `"glossa: ignore="` |
| `fix.enabled` | Enable or disable the fix pipeline globally. | `true` |
| `fix.apply` | Control fix behavior: `"never"`, `"safe"`, or `"unsafe"`. | `"safe"` |
| `fix.validate_after_apply` | Re-lint after applying fixes and reject fixes that do not resolve the diagnostic. | `true` |
| `output.format` | Output format (`"text"` or `"json"`). | `"text"` |
| `output.color` | Enable colored terminal output. | `true` |
| `output.show_source` | Include source context in text output. | `true` |

## Rule Options

Some rules accept per-rule options under `rules.rule_options.<rule-name>`.

| Rule | Option | Type | Default | Description |
| ---- | ------ | ---- | ------- | ----------- |
| missing-callable-docstring | `include_test_functions` | bool | `false` | Require docstrings on test functions (`test_*`). |
| missing-callable-docstring | `include_private_helpers` | bool | `false` | Require docstrings on private (`_`-prefixed) callables. |
| missing-returns-section | `simple_property_requires_returns` | bool | `true` | Require a Returns section on simple properties. |
| missing-module-inventory | `inventory_threshold` | int | `2` | Minimum public symbols before a Classes/Functions inventory section is required. |
| examples-in-non-entry-module | `api_entry_modules` | list[str] | `[]` | File globs identifying API entry-point modules where Examples sections are expected. |
| trivial-dunder-docstring | `trivial_dunder_allowlist` | list[str] | `[]` | Dunder method names exempt from the trivial-docstring check. |

## Inline Suppressions

Inline suppressions attach to a module header or target definition:

```python
def render(config: Config) -> str:  # glossa: ignore=non-imperative-summary,markdown-in-docstring
    """Returns the rendered text"""
```
