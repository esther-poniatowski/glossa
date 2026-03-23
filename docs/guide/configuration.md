# Configuration

## Configuration File

glossa reads configuration from YAML files located in the `config/`
directory.

The canonical configuration schema is provided in `config/default.yaml`.

```yaml
# Example configuration
var_1: value1
var_2: value2
```

## Environment Variables

| Variable | Description | Default | Required |
| -------- | ----------- | ------- | -------- |
| `VAR_1` | Description. | None | Yes |
| `VAR_2` | Description. | `false` | No |

## Precedence

Configuration is resolved in the following order (highest priority first):

1. Command-line arguments
2. Environment variables
3. Project configuration file (`config/default.yaml`)
4. Built-in defaults
