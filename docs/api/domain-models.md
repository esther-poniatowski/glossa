<a id="domain-models"></a>

# Domain Models

Pure domain types and behaviour: docstring models, parsing, fix planning, and traceability.

<a id="module-glossa.domain.models"></a>

<a id="models"></a>

## Models

Immutable semantic and syntax-preserving docstring models.

<a id="glossa.domain.models.DocstringSpan"></a>

### *class* glossa.domain.models.DocstringSpan(start_offset: 'int', end_offset: 'int')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.models.DocstringSpan.start_offset"></a>

#### start_offset *: [int](https://docs.python.org/3/library/functions.html#int)*

<a id="glossa.domain.models.DocstringSpan.end_offset"></a>

#### end_offset *: [int](https://docs.python.org/3/library/functions.html#int)*

<a id="glossa.domain.models.DocstringSyntax"></a>

### *class* glossa.domain.models.DocstringSyntax(raw_body: 'str', quote: 'Literal[\\'"""\\', "\\'\\'\\'"]', string_prefix: 'str', indentation: 'str', leading_blank_lines: 'int', trailing_blank_lines: 'int')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.models.DocstringSyntax.raw_body"></a>

#### raw_body *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.models.DocstringSyntax.quote"></a>

#### quote *: [Literal](https://docs.python.org/3/library/typing.html#typing.Literal)['"""', "'''"]*

<a id="glossa.domain.models.DocstringSyntax.string_prefix"></a>

#### string_prefix *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.models.DocstringSyntax.indentation"></a>

#### indentation *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.models.DocstringSyntax.leading_blank_lines"></a>

#### leading_blank_lines *: [int](https://docs.python.org/3/library/functions.html#int)*

<a id="glossa.domain.models.DocstringSyntax.trailing_blank_lines"></a>

#### trailing_blank_lines *: [int](https://docs.python.org/3/library/functions.html#int)*

<a id="glossa.domain.models.TypedSectionKind"></a>

### *class* glossa.domain.models.TypedSectionKind(value, names=<not given>, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

<a id="glossa.domain.models.TypedSectionKind.PARAMETERS"></a>

#### PARAMETERS *= 'Parameters'*

<a id="glossa.domain.models.TypedSectionKind.RETURNS"></a>

#### RETURNS *= 'Returns'*

<a id="glossa.domain.models.TypedSectionKind.YIELDS"></a>

#### YIELDS *= 'Yields'*

<a id="glossa.domain.models.TypedSectionKind.ATTRIBUTES"></a>

#### ATTRIBUTES *= 'Attributes'*

<a id="glossa.domain.models.TypedSectionKind.RAISES"></a>

#### RAISES *= 'Raises'*

<a id="glossa.domain.models.TypedSectionKind.WARNS"></a>

#### WARNS *= 'Warns'*

<a id="glossa.domain.models.ProseSectionKind"></a>

### *class* glossa.domain.models.ProseSectionKind(value, names=<not given>, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

<a id="glossa.domain.models.ProseSectionKind.NOTES"></a>

#### NOTES *= 'Notes'*

<a id="glossa.domain.models.ProseSectionKind.WARNINGS"></a>

#### WARNINGS *= 'Warnings'*

<a id="glossa.domain.models.ProseSectionKind.EXAMPLES"></a>

#### EXAMPLES *= 'Examples'*

<a id="glossa.domain.models.ProseSectionKind.USAGE"></a>

#### USAGE *= 'Usage'*

<a id="glossa.domain.models.InventorySectionKind"></a>

### *class* glossa.domain.models.InventorySectionKind(value, names=<not given>, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

<a id="glossa.domain.models.InventorySectionKind.CLASSES"></a>

#### CLASSES *= 'Classes'*

<a id="glossa.domain.models.InventorySectionKind.FUNCTIONS"></a>

#### FUNCTIONS *= 'Functions'*

<a id="glossa.domain.models.Summary"></a>

### *class* glossa.domain.models.Summary(text: 'str', span: 'DocstringSpan')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.models.Summary.text"></a>

#### text *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.models.Summary.span"></a>

#### span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.TypedEntry"></a>

### *class* glossa.domain.models.TypedEntry(name: 'str | None', type_text: 'str | None', default_text: 'str | None', description_lines: 'tuple[str, ...]', span: 'DocstringSpan')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.models.TypedEntry.name"></a>

#### name *: [str](https://docs.python.org/3/library/stdtypes.html#str) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.models.TypedEntry.type_text"></a>

#### type_text *: [str](https://docs.python.org/3/library/stdtypes.html#str) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.models.TypedEntry.default_text"></a>

#### default_text *: [str](https://docs.python.org/3/library/stdtypes.html#str) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.models.TypedEntry.description_lines"></a>

#### description_lines *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.domain.models.TypedEntry.span"></a>

#### span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.SectionProtocol"></a>

### *class* glossa.domain.models.SectionProtocol(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Shared interface for all docstring section types.

<a id="glossa.domain.models.SectionProtocol.section_title"></a>

#### *property* section_title *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.models.SectionProtocol.body_text_lines"></a>

#### *property* body_text_lines *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.domain.models.SectionProtocol.span"></a>

#### *property* span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.UnderlinedSectionProtocol"></a>

### *class* glossa.domain.models.UnderlinedSectionProtocol(\*args, \*\*kwargs)

Bases: [`SectionProtocol`](#glossa.domain.models.SectionProtocol), [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Section type that has a title underline.

<a id="glossa.domain.models.UnderlinedSectionProtocol.title_span"></a>

#### *property* title_span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.UnderlinedSectionProtocol.underline_span"></a>

#### *property* underline_span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.TypedSection"></a>

### *class* glossa.domain.models.TypedSection(kind: 'TypedSectionKind', title_span: 'DocstringSpan', underline_span: 'DocstringSpan', entries: 'tuple[TypedEntry, ...]', span: 'DocstringSpan', source_title: 'str' = '')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.models.TypedSection.kind"></a>

#### kind *: [TypedSectionKind](#glossa.domain.models.TypedSectionKind)*

<a id="glossa.domain.models.TypedSection.title_span"></a>

#### title_span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.TypedSection.underline_span"></a>

#### underline_span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.TypedSection.entries"></a>

#### entries *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[TypedEntry](#glossa.domain.models.TypedEntry), ...]*

<a id="glossa.domain.models.TypedSection.span"></a>

#### span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.TypedSection.source_title"></a>

#### source_title *: [str](https://docs.python.org/3/library/stdtypes.html#str)* *= ''*

<a id="glossa.domain.models.TypedSection.section_title"></a>

#### *property* section_title *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.models.TypedSection.body_text_lines"></a>

#### *property* body_text_lines *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.domain.models.ProseSection"></a>

### *class* glossa.domain.models.ProseSection(kind: 'ProseSectionKind', title_span: 'DocstringSpan', underline_span: 'DocstringSpan', body_lines: 'tuple[str, ...]', span: 'DocstringSpan')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.models.ProseSection.kind"></a>

#### kind *: [ProseSectionKind](#glossa.domain.models.ProseSectionKind)*

<a id="glossa.domain.models.ProseSection.title_span"></a>

#### title_span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.ProseSection.underline_span"></a>

#### underline_span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.ProseSection.body_lines"></a>

#### body_lines *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.domain.models.ProseSection.span"></a>

#### span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.ProseSection.section_title"></a>

#### *property* section_title *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.models.ProseSection.body_text_lines"></a>

#### *property* body_text_lines *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.domain.models.InventoryItem"></a>

### *class* glossa.domain.models.InventoryItem(name: 'str', description_lines: 'tuple[str, ...]', span: 'DocstringSpan')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.models.InventoryItem.name"></a>

#### name *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.models.InventoryItem.description_lines"></a>

#### description_lines *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.domain.models.InventoryItem.span"></a>

#### span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.InventorySection"></a>

### *class* glossa.domain.models.InventorySection(kind: 'InventorySectionKind', title_span: 'DocstringSpan', underline_span: 'DocstringSpan', items: 'tuple[InventoryItem, ...]', span: 'DocstringSpan')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.models.InventorySection.kind"></a>

#### kind *: [InventorySectionKind](#glossa.domain.models.InventorySectionKind)*

<a id="glossa.domain.models.InventorySection.title_span"></a>

#### title_span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.InventorySection.underline_span"></a>

#### underline_span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.InventorySection.items"></a>

#### items *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[InventoryItem](#glossa.domain.models.InventoryItem), ...]*

<a id="glossa.domain.models.InventorySection.span"></a>

#### span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.InventorySection.section_title"></a>

#### *property* section_title *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.models.InventorySection.body_text_lines"></a>

#### *property* body_text_lines *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.domain.models.SeeAlsoItem"></a>

### *class* glossa.domain.models.SeeAlsoItem(name: 'str', description_lines: 'tuple[str, ...]', span: 'DocstringSpan')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.models.SeeAlsoItem.name"></a>

#### name *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.models.SeeAlsoItem.description_lines"></a>

#### description_lines *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.domain.models.SeeAlsoItem.span"></a>

#### span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.SeeAlsoSection"></a>

### *class* glossa.domain.models.SeeAlsoSection(title_span: 'DocstringSpan', underline_span: 'DocstringSpan', items: 'tuple[SeeAlsoItem, ...]', span: 'DocstringSpan')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.models.SeeAlsoSection.title_span"></a>

#### title_span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.SeeAlsoSection.underline_span"></a>

#### underline_span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.SeeAlsoSection.items"></a>

#### items *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[SeeAlsoItem](#glossa.domain.models.SeeAlsoItem), ...]*

<a id="glossa.domain.models.SeeAlsoSection.span"></a>

#### span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.SeeAlsoSection.section_title"></a>

#### *property* section_title *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.models.SeeAlsoSection.body_text_lines"></a>

#### *property* body_text_lines *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.domain.models.DeprecationDirective"></a>

### *class* glossa.domain.models.DeprecationDirective(version: 'str | None', body_lines: 'tuple[str, ...]', span: 'DocstringSpan')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.models.DeprecationDirective.version"></a>

#### version *: [str](https://docs.python.org/3/library/stdtypes.html#str) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.models.DeprecationDirective.body_lines"></a>

#### body_lines *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.domain.models.DeprecationDirective.span"></a>

#### span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.UnknownSection"></a>

### *class* glossa.domain.models.UnknownSection(title: 'str', title_span: 'DocstringSpan', underline_span: 'DocstringSpan', body_lines: 'tuple[str, ...]', span: 'DocstringSpan')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.models.UnknownSection.title"></a>

#### title *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.models.UnknownSection.title_span"></a>

#### title_span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.UnknownSection.underline_span"></a>

#### underline_span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.UnknownSection.body_lines"></a>

#### body_lines *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.domain.models.UnknownSection.span"></a>

#### span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.models.UnknownSection.section_title"></a>

#### *property* section_title *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.models.UnknownSection.body_text_lines"></a>

#### *property* body_text_lines *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.domain.models.ParseIssue"></a>

### *class* glossa.domain.models.ParseIssue(kind: 'str', message: 'str', span: 'DocstringSpan | None')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.models.ParseIssue.kind"></a>

#### kind *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.models.ParseIssue.message"></a>

#### message *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.models.ParseIssue.span"></a>

#### span *: [DocstringSpan](#glossa.domain.models.DocstringSpan) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.models.ParsedDocstring"></a>

### *class* glossa.domain.models.ParsedDocstring(syntax: 'DocstringSyntax', summary: 'Summary | None', deprecation: 'DeprecationDirective | None', extended_description_lines: 'tuple[str, ...]', sections: 'tuple[SectionNode, ...]', parse_issues: 'tuple[ParseIssue, ...]')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.models.ParsedDocstring.syntax"></a>

#### syntax *: [DocstringSyntax](#glossa.domain.models.DocstringSyntax)*

<a id="glossa.domain.models.ParsedDocstring.summary"></a>

#### summary *: [Summary](#glossa.domain.models.Summary) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.models.ParsedDocstring.deprecation"></a>

#### deprecation *: [DeprecationDirective](#glossa.domain.models.DeprecationDirective) | [None](https://docs.python.org/3/library/constants.html#None)*

<a id="glossa.domain.models.ParsedDocstring.extended_description_lines"></a>

#### extended_description_lines *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.domain.models.ParsedDocstring.sections"></a>

#### sections *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[TypedSection](#glossa.domain.models.TypedSection) | [ProseSection](#glossa.domain.models.ProseSection) | [InventorySection](#glossa.domain.models.InventorySection) | [SeeAlsoSection](#glossa.domain.models.SeeAlsoSection) | [UnknownSection](#glossa.domain.models.UnknownSection), ...]*

<a id="glossa.domain.models.ParsedDocstring.parse_issues"></a>

#### parse_issues *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[ParseIssue](#glossa.domain.models.ParseIssue), ...]*

<a id="glossa.domain.models.ParsedDocstring.typed_section"></a>

#### typed_section(kind)

<a id="glossa.domain.models.ParsedDocstring.has_typed_section"></a>

#### has_typed_section(kind)

<a id="glossa.domain.models.ParsedDocstring.inventory_section"></a>

#### inventory_section(kind)

<a id="glossa.domain.models.ParsedDocstring.has_inventory_section"></a>

#### has_inventory_section(kind)

<a id="glossa.domain.models.ParsedDocstring.see_also_section"></a>

#### see_also_section()

<a id="glossa.domain.models.ParsedDocstring.section_by_title"></a>

#### section_by_title(title)

Return the first section whose `section_title` equals *title*.

<a id="glossa.domain.models.ParsedDocstring.all_text_lines"></a>

#### all_text_lines()

<a id="glossa.domain.models.ParsedDocstring.prose_text_lines"></a>

#### prose_text_lines()

<a id="module-glossa.domain.parsing"></a>

<a id="parsing"></a>

## Parsing

Parse raw docstring text into lossless and semantic structures.

Receives only raw docstring text and docstring-local metadata from an
`ExtractedDocstring` DTO. No `ast.AST`, `Path`, or file handles cross
into the domain.

<a id="glossa.domain.parsing.SectionParseContext"></a>

### *class* glossa.domain.parsing.SectionParseContext(title, body_lines, title_span, underline_span, section_span, all_lines, body_start)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Bundled context passed to section parse functions.

<a id="glossa.domain.parsing.SectionParseContext.title"></a>

#### title *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.parsing.SectionParseContext.body_lines"></a>

#### body_lines *: [list](https://docs.python.org/3/library/stdtypes.html#list)[[str](https://docs.python.org/3/library/stdtypes.html#str)]*

<a id="glossa.domain.parsing.SectionParseContext.title_span"></a>

#### title_span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.parsing.SectionParseContext.underline_span"></a>

#### underline_span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.parsing.SectionParseContext.section_span"></a>

#### section_span *: [DocstringSpan](#glossa.domain.models.DocstringSpan)*

<a id="glossa.domain.parsing.SectionParseContext.all_lines"></a>

#### all_lines *: [list](https://docs.python.org/3/library/stdtypes.html#list)[[str](https://docs.python.org/3/library/stdtypes.html#str)]*

<a id="glossa.domain.parsing.SectionParseContext.body_start"></a>

#### body_start *: [int](https://docs.python.org/3/library/functions.html#int)*

<a id="glossa.domain.parsing.parse_docstring"></a>

### glossa.domain.parsing.parse_docstring(body, quote, string_prefix, indentation, section_aliases=None)

Parse a raw docstring body into a `ParsedDocstring`.

* **Parameters:**
  * **body** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – The raw text between the opening and closing quotes.
  * **quote** (*Literal* *[* *'"""'* *,*  *"'''"* *]*) – The quote style used.
  * **string_prefix** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Any string prefix (e.g. `"r"`).
  * **indentation** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – The indentation of the docstring within its source file.
* **Returns:**
  The parsed docstring with syntax, summary, sections, and issues.
* **Return type:**
  [ParsedDocstring](#glossa.domain.models.ParsedDocstring)

<a id="module-glossa.domain.fixes"></a>

<a id="fixes"></a>

## Fixes

Pure overlap detection for edit planning.

This module lives in the domain layer: no I/O, no filesystem access, no ast.

<a id="glossa.domain.fixes.intervals_overlap"></a>

### glossa.domain.fixes.intervals_overlap(a_start, a_end, b_start, b_end)

Return True if two half-open intervals [a_start, a_end) and [b_start, b_end) overlap.

* **Parameters:**
  * **a_start** ([*int*](https://docs.python.org/3/library/functions.html#int)) – Start of the first interval.
  * **a_end** ([*int*](https://docs.python.org/3/library/functions.html#int)) – End of the first interval (exclusive).
  * **b_start** ([*int*](https://docs.python.org/3/library/functions.html#int)) – Start of the second interval.
  * **b_end** ([*int*](https://docs.python.org/3/library/functions.html#int)) – End of the second interval (exclusive).
* **Returns:**
  `True` if the intervals share at least one position.
* **Return type:**
  [bool](https://docs.python.org/3/library/functions.html#bool)

<a id="module-glossa.domain.traceability"></a>

<a id="traceability"></a>

## Traceability

<a id="glossa.domain.traceability.TraceEntry"></a>

### *class* glossa.domain.traceability.TraceEntry(guide_clause: 'str', status: "Literal['enforced', 'enforced_via_config', 'out_of_scope']", coverage: 'tuple[str, ...]')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

<a id="glossa.domain.traceability.TraceEntry.guide_clause"></a>

#### guide_clause *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

<a id="glossa.domain.traceability.TraceEntry.status"></a>

#### status *: [Literal](https://docs.python.org/3/library/typing.html#typing.Literal)['enforced', 'enforced_via_config', 'out_of_scope']*

<a id="glossa.domain.traceability.TraceEntry.coverage"></a>

#### coverage *: [tuple](https://docs.python.org/3/library/stdtypes.html#tuple)[[str](https://docs.python.org/3/library/stdtypes.html#str), ...]*

<a id="glossa.domain.traceability.rules_for_clause"></a>

### glossa.domain.traceability.rules_for_clause(clause)

Return the rule names for a given guide clause.

<a id="glossa.domain.traceability.validate_matrix_codes"></a>

### glossa.domain.traceability.validate_matrix_codes(registered_names)

Return matrix rule names not present in *registered_names*.

<a id="glossa.domain.traceability.clause_for_rule"></a>

### glossa.domain.traceability.clause_for_rule(name)

Return all guide clauses that a given rule name covers.
