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

[tool.glossa.rules.severity_overrides]
D201 = "error"

[tool.glossa.rules.per_file_ignores]
"tests/**.py" = ["D102"]

[tool.glossa.rules.rule_options.D104]
simple_property_requires_returns = false

[tool.glossa.rules.rule_options.D108]
inventory_threshold = 2

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
  severity_overrides:
    D201: error
  per_file_ignores:
    "tests/**.py": ["D102"]
  rule_options:
    D104:
      simple_property_requires_returns: false
    D108:
      inventory_threshold: 2

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
| `rules.select` | Rule codes or groups to enable. | All |
| `rules.ignore` | Rule codes to disable. | None |
| `rules.per_file_ignores` | Disable specific rules for matching file globs. | None |
| `rules.rule_options` | Resolve ambiguous guide policies explicitly. | None |
| `fix.apply` | Control fix behavior: `disabled`, `safe`, or `unsafe`. | `safe` |
| `suppressions.inline_enabled` | Enable inline `glossa: ignore=` directives. | `true` |
| `output.format` | Output format (`text` or `json`). | `text` |

## Inline Suppressions

Inline suppressions attach to a module header or target definition:

```python
def render(config: Config) -> str:  # glossa: ignore=D200,D205
    """Returns the rendered text"""
```
