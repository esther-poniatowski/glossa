<a id="infrastructure"></a>

# Infrastructure

Infrastructure adapters: configuration loading, file discovery, docstring extraction, file I/O, and plugin loading.

<a id="module-glossa.infrastructure.config"></a>

<a id="configuration"></a>

## Configuration

<a id="glossa.infrastructure.config.ConfigLoader"></a>

### *class* glossa.infrastructure.config.ConfigLoader(base_path)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Load glossa configuration from pyproject.toml or .glossa.yaml.

<a id="glossa.infrastructure.config.ConfigLoader.load"></a>

#### load(config_path=None)

Return raw configuration dictionary.

* **Parameters:**
  **config_path** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* *None* *,* *optional*) – Explicit path to a configuration file. When `None`, search for
  `pyproject.toml` then `.glossa.yaml` under the base path.
* **Returns:**
  Raw, unvalidated configuration data. An empty dict is returned
  when no configuration file is found.
* **Return type:**
  [dict](https://docs.python.org/3/library/stdtypes.html#dict)[[str](https://docs.python.org/3/library/stdtypes.html#str), [object](https://docs.python.org/3/library/functions.html#object)]
* **Raises:**
  [**ConfigurationError**](errors.md#glossa.errors.ConfigurationError) – If the specified or discovered file cannot be read or parsed.

<a id="module-glossa.infrastructure.discovery"></a>

<a id="discovery"></a>

## Discovery

<a id="glossa.infrastructure.discovery.FileDiscovery"></a>

### *class* glossa.infrastructure.discovery.FileDiscovery(base_path)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Walk configured paths and yield Python source files.

<a id="glossa.infrastructure.discovery.FileDiscovery.discover"></a>

#### discover(paths, exclude=())

Yield source-id strings for Python source files.

<a id="module-glossa.infrastructure.extraction"></a>

<a id="extraction"></a>

## Extraction

<a id="glossa.infrastructure.extraction.ASTExtractor"></a>

### *class* glossa.infrastructure.extraction.ASTExtractor

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Extract lintable targets from Python source text using the AST.

<a id="glossa.infrastructure.extraction.ASTExtractor.extract"></a>

#### extract(source_id, source_text)

Parse *source_text* and return all extracted targets.

* **Parameters:**
  * **source_id** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Project-relative POSIX path used to build `SourceRef` values.
  * **source_text** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Full text content of the Python source file.
* **Returns:**
  One `ExtractedTarget` per documentable symbol in the file.
* **Return type:**
  [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[ExtractedTarget](domain-contracts.md#glossa.domain.contracts.extraction.ExtractedTarget), …]
* **Raises:**
  [**ExtractionError**](errors.md#glossa.errors.ExtractionError) – If the source text cannot be parsed as valid Python.

<a id="module-glossa.infrastructure.files"></a>

<a id="files"></a>

## Files

<a id="glossa.infrastructure.files.LocalFilePort"></a>

### *class* glossa.infrastructure.files.LocalFilePort(base_path)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Read source files and write edited output.

<a id="glossa.infrastructure.files.LocalFilePort.read"></a>

#### read(source_id)

<a id="glossa.infrastructure.files.LocalFilePort.write"></a>

#### write(source_id, content)

<a id="module-glossa.infrastructure.plugins"></a>

<a id="plugins"></a>

## Plugins

<a id="glossa.infrastructure.plugins.EntryPointPluginLoader"></a>

### *class* glossa.infrastructure.plugins.EntryPointPluginLoader

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Load third-party rule providers from entry points.

<a id="glossa.infrastructure.plugins.EntryPointPluginLoader.load_plugins"></a>

#### load_plugins()
