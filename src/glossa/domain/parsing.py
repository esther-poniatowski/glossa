"""Parse raw docstring text into lossless and semantic structures.

Receives only raw docstring text and docstring-local metadata from an
``ExtractedDocstring`` DTO. No ``ast.AST``, ``Path``, or file handles cross
into the domain.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Literal, Mapping, Sequence

from glossa.domain.models import (
    DeprecationDirective,
    DocstringSpan,
    DocstringSyntax,
    InventoryItem,
    InventorySection,
    InventorySectionKind,
    ParsedDocstring,
    ParseIssue,
    ProseSection,
    ProseSectionKind,
    SectionNode,
    SeeAlsoItem,
    SeeAlsoSection,
    Summary,
    TypedEntry,
    TypedSection,
    TypedSectionKind,
    UnknownSection,
)

# ---------------------------------------------------------------------------
# Section title constants
# ---------------------------------------------------------------------------

_TYPED_SECTION_TITLES: dict[str, TypedSectionKind] = {
    "Parameters": TypedSectionKind.PARAMETERS,
    "Params": TypedSectionKind.PARAMETERS,
    "Arguments": TypedSectionKind.PARAMETERS,
    "Args": TypedSectionKind.PARAMETERS,
    "Returns": TypedSectionKind.RETURNS,
    "Yields": TypedSectionKind.YIELDS,
    "Attributes": TypedSectionKind.ATTRIBUTES,
    "Raises": TypedSectionKind.RAISES,
    "Warns": TypedSectionKind.WARNS,
}

_PROSE_SECTION_TITLES: dict[str, ProseSectionKind] = {
    "Notes": ProseSectionKind.NOTES,
    "Warnings": ProseSectionKind.WARNINGS,
    "Examples": ProseSectionKind.EXAMPLES,
    "Usage": ProseSectionKind.USAGE,
}

_INVENTORY_SECTION_TITLES: dict[str, InventorySectionKind] = {
    "Classes": InventorySectionKind.CLASSES,
    "Functions": InventorySectionKind.FUNCTIONS,
}

_SEE_ALSO_TITLE = "See Also"

_ALL_KNOWN_TITLES = (
    set(_TYPED_SECTION_TITLES)
    | set(_PROSE_SECTION_TITLES)
    | set(_INVENTORY_SECTION_TITLES)
    | {_SEE_ALSO_TITLE}
)

# Pattern for section underlines: dashes only, at least 3.
_UNDERLINE_RE = re.compile(r"^\s*-{3,}\s*$")

# Pattern for ``.. deprecated:: <version>``
_DEPRECATED_RE = re.compile(
    r"^\.\.\s+deprecated::\s*(?P<version>\S+)?\s*$", re.IGNORECASE
)

# Pattern for typed entry headers: ``name : type`` or ``name : type, default value``
_TYPED_ENTRY_RE = re.compile(
    r"^(?P<name>\*{0,2}\w+)(?:\s*:\s*(?P<type>[^,]+?)(?:\s*,\s*(?P<default>.+))?)?\s*$"
)

# Pattern for return/yield entries (no name): ``type``
_UNNAMED_ENTRY_RE = re.compile(r"^(?P<type>[^,]+?)(?:\s*,\s*(?P<default>.+))?\s*$")

# ---------------------------------------------------------------------------
# Section parse function type
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SectionParseContext:
    """Bundled context passed to section parse functions."""

    title: str
    body_lines: list[str]
    title_span: DocstringSpan
    underline_span: DocstringSpan
    section_span: DocstringSpan
    all_lines: list[str]
    body_start: int


SectionParseFunc = Callable[[SectionParseContext], SectionNode]


@dataclass(frozen=True)
class SectionParser:
    """Associates a set of section titles with a parse function.

    To register a custom section type, construct a ``SectionParser`` and pass
    it to ``parse_docstring`` via the ``extra_parsers`` argument.
    """

    titles: frozenset[str]
    parse: SectionParseFunc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _count_leading_blank(lines: list[str]) -> int:
    count = 0
    for line in lines:
        if line.strip():
            break
        count += 1
    return count


def _count_trailing_blank(lines: list[str]) -> int:
    count = 0
    for line in reversed(lines):
        if line.strip():
            break
        count += 1
    if count > 0 and lines and lines[-1] == "":
        count = max(0, count - 1)
    return count


def _offset_of_line(lines: list[str], idx: int) -> int:
    offset = 0
    for i in range(idx):
        offset += len(lines[i]) + 1
    return offset


def _span_of_lines(lines: list[str], start_idx: int, end_idx: int) -> DocstringSpan:
    start = _offset_of_line(lines, start_idx)
    if end_idx <= start_idx:
        return DocstringSpan(start, start)
    end = _offset_of_line(lines, end_idx - 1) + len(lines[end_idx - 1])
    return DocstringSpan(start, end)


def _is_section_header(lines: list[str], idx: int) -> str | None:
    if idx + 1 >= len(lines):
        return None
    title_line = lines[idx].strip()
    underline = lines[idx + 1]
    if _UNDERLINE_RE.match(underline) and title_line:
        return title_line
    return None


def _dedent_body(lines: list[str], indent: int) -> tuple[str, ...]:
    result = []
    for line in lines:
        if line.strip() == "":
            result.append("")
        elif len(line) > indent and line[:indent].strip() == "":
            result.append(line[indent:])
        else:
            result.append(line.rstrip())
    return tuple(result)


# ---------------------------------------------------------------------------
# Indent-based block grouping
# ---------------------------------------------------------------------------


def _group_indented_blocks(
    body_lines: list[str],
) -> list[tuple[int, list[str]]]:
    if not body_lines:
        return []

    base_indent = 0
    for line in body_lines:
        if line.strip():
            base_indent = len(line) - len(line.lstrip())
            break

    blocks: list[tuple[int, list[str]]] = []
    current_start: int | None = None
    current_lines: list[str] = []

    for i, line in enumerate(body_lines):
        stripped = line.rstrip()
        if not stripped:
            if current_lines:
                current_lines.append(stripped)
            continue

        line_indent = len(line) - len(line.lstrip())
        if line_indent == base_indent:
            if current_lines:
                blocks.append((current_start, current_lines))  # type: ignore[arg-type]
            current_start = i
            current_lines = [stripped]
        elif current_lines:
            current_lines.append(stripped)
        else:
            current_start = i
            current_lines = [stripped]

    if current_lines:
        blocks.append((current_start, current_lines))  # type: ignore[arg-type]

    return blocks


def _trim_trailing_blanks(lines: tuple[str, ...]) -> tuple[str, ...]:
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    return lines


# ---------------------------------------------------------------------------
# Section body parsers
# ---------------------------------------------------------------------------


def _parse_typed_entries(
    body_lines: list[str],
    kind: TypedSectionKind,
    all_lines: list[str],
    body_start_idx: int,
) -> tuple[TypedEntry, ...]:
    blocks = _group_indented_blocks(body_lines)
    if not blocks:
        return ()

    uses_names = kind not in (TypedSectionKind.RETURNS, TypedSectionKind.YIELDS)
    entries: list[TypedEntry] = []

    for block_start, block_lines in blocks:
        header = block_lines[0].strip()
        desc_lines = _trim_trailing_blanks(tuple(block_lines[1:]))

        name: str | None = None
        type_text: str | None = None
        default_text: str | None = None

        if uses_names:
            m = _TYPED_ENTRY_RE.match(header)
            if m:
                name = m.group("name")
                type_text = m.group("type")
                if type_text:
                    type_text = type_text.strip()
                default_text = m.group("default")
                if default_text:
                    default_text = default_text.strip()
            else:
                name = header.split(":")[0].strip() if ":" in header else header.strip()
        else:
            m = _UNNAMED_ENTRY_RE.match(header)
            if m:
                type_text = m.group("type")
                if type_text:
                    type_text = type_text.strip()
                default_text = m.group("default")
                if default_text:
                    default_text = default_text.strip()

        abs_start = body_start_idx + block_start
        abs_end = abs_start + len(block_lines)
        span = _span_of_lines(all_lines, abs_start, abs_end)

        entries.append(
            TypedEntry(
                name=name,
                type_text=type_text,
                default_text=default_text,
                description_lines=desc_lines,
                span=span,
            )
        )

    return tuple(entries)


def _parse_inventory_items(
    body_lines: list[str],
    all_lines: list[str],
    body_start_idx: int,
) -> tuple[InventoryItem, ...]:
    blocks = _group_indented_blocks(body_lines)
    if not blocks:
        return ()

    items: list[InventoryItem] = []
    for block_start, block_lines in blocks:
        name = block_lines[0].strip()
        desc_lines = _trim_trailing_blanks(tuple(block_lines[1:]))

        abs_start = body_start_idx + block_start
        abs_end = abs_start + len(block_lines)
        span = _span_of_lines(all_lines, abs_start, abs_end)

        items.append(
            InventoryItem(name=name, description_lines=desc_lines, span=span)
        )

    return tuple(items)


def _parse_see_also_items(
    body_lines: list[str],
    all_lines: list[str],
    body_start_idx: int,
) -> tuple[SeeAlsoItem, ...]:
    blocks = _group_indented_blocks(body_lines)
    if not blocks:
        return ()

    items: list[SeeAlsoItem] = []
    for block_start, block_lines in blocks:
        header = block_lines[0].strip()
        if " : " in header:
            name, _, desc = header.partition(" : ")
            desc_lines: tuple[str, ...] = (desc.strip(),) + tuple(block_lines[1:])
        else:
            name = header
            desc_lines = tuple(block_lines[1:]) if len(block_lines) > 1 else ()
        desc_lines = _trim_trailing_blanks(desc_lines)

        abs_start = body_start_idx + block_start
        abs_end = abs_start + len(block_lines)
        span = _span_of_lines(all_lines, abs_start, abs_end)

        items.append(
            SeeAlsoItem(name=name.strip(), description_lines=desc_lines, span=span)
        )

    return tuple(items)


# ---------------------------------------------------------------------------
# Concrete section parse functions
# ---------------------------------------------------------------------------


def _parse_typed_section(ctx: SectionParseContext) -> TypedSection:
    kind = _TYPED_SECTION_TITLES[ctx.title]
    entries = _parse_typed_entries(ctx.body_lines, kind, ctx.all_lines, ctx.body_start)
    return TypedSection(
        kind=kind,
        title_span=ctx.title_span,
        underline_span=ctx.underline_span,
        entries=entries,
        span=ctx.section_span,
        source_title=ctx.title,
    )


def _parse_prose_section(ctx: SectionParseContext) -> ProseSection:
    kind = _PROSE_SECTION_TITLES[ctx.title]
    return ProseSection(
        kind=kind,
        title_span=ctx.title_span,
        underline_span=ctx.underline_span,
        body_lines=tuple(line.rstrip() for line in ctx.body_lines),
        span=ctx.section_span,
    )


def _parse_inventory_section(ctx: SectionParseContext) -> InventorySection:
    kind = _INVENTORY_SECTION_TITLES[ctx.title]
    items = _parse_inventory_items(ctx.body_lines, ctx.all_lines, ctx.body_start)
    return InventorySection(
        kind=kind,
        title_span=ctx.title_span,
        underline_span=ctx.underline_span,
        items=items,
        span=ctx.section_span,
    )


def _parse_see_also_section(ctx: SectionParseContext) -> SeeAlsoSection:
    items = _parse_see_also_items(ctx.body_lines, ctx.all_lines, ctx.body_start)
    return SeeAlsoSection(
        title_span=ctx.title_span,
        underline_span=ctx.underline_span,
        items=items,
        span=ctx.section_span,
    )


# ---------------------------------------------------------------------------
# Built-in section parser registry
# ---------------------------------------------------------------------------

_BUILTIN_SECTION_PARSERS: list[SectionParser] = [
    SectionParser(
        titles=frozenset(_TYPED_SECTION_TITLES.keys()),
        parse=_parse_typed_section,
    ),
    SectionParser(
        titles=frozenset(_PROSE_SECTION_TITLES.keys()),
        parse=_parse_prose_section,
    ),
    SectionParser(
        titles=frozenset(_INVENTORY_SECTION_TITLES.keys()),
        parse=_parse_inventory_section,
    ),
    SectionParser(
        titles=frozenset({_SEE_ALSO_TITLE}),
        parse=_parse_see_also_section,
    ),
]


def _build_dispatch(
    extra_parsers: Sequence[SectionParser] | None,
    section_aliases: Mapping[str, str] | None = None,
) -> dict[str, SectionParseFunc]:
    """Return a title → parse-function dict from built-ins plus any extras.

    Parameters
    ----------
    extra_parsers : Sequence[SectionParser] | None
        Additional section parsers beyond built-ins.
    section_aliases : Mapping[str, str] | None
        Maps custom titles to known section titles (e.g. ``{"Hint": "Notes"}``).
        The alias inherits the parse function and kind of its target.
    """
    dispatch: dict[str, SectionParseFunc] = {}
    for entry in _BUILTIN_SECTION_PARSERS:
        for title in entry.titles:
            dispatch[title] = entry.parse
    if extra_parsers:
        for entry in extra_parsers:
            for title in entry.titles:
                dispatch[title] = entry.parse
    if section_aliases:
        for alias, target in section_aliases.items():
            if target in dispatch:
                dispatch[alias] = dispatch[target]
    return dispatch


def _register_aliases(section_aliases: Mapping[str, str]) -> None:
    """Register user-defined section aliases into the title lookup dicts.

    Must be called before parsing so that section parse functions can
    resolve the kind of aliased titles.
    """
    for alias, target in section_aliases.items():
        if target in _TYPED_SECTION_TITLES:
            _TYPED_SECTION_TITLES[alias] = _TYPED_SECTION_TITLES[target]
        elif target in _PROSE_SECTION_TITLES:
            _PROSE_SECTION_TITLES[alias] = _PROSE_SECTION_TITLES[target]
        elif target in _INVENTORY_SECTION_TITLES:
            _INVENTORY_SECTION_TITLES[alias] = _INVENTORY_SECTION_TITLES[target]
        _ALL_KNOWN_TITLES.add(alias)


# ---------------------------------------------------------------------------
# Deprecation directive parser
# ---------------------------------------------------------------------------


def _try_parse_deprecation(
    lines: list[str], start_idx: int
) -> tuple[DeprecationDirective, int] | None:
    if start_idx >= len(lines):
        return None
    m = _DEPRECATED_RE.match(lines[start_idx].strip())
    if not m:
        return None

    version = m.group("version")
    body_start = start_idx + 1
    body_lines: list[str] = []
    idx = body_start

    if idx < len(lines):
        base_indent: int | None = None
        while idx < len(lines):
            line = lines[idx]
            if line.strip():
                ind = len(line) - len(line.lstrip())
                if base_indent is None:
                    base_indent = ind
                if ind < (base_indent or 0) and line.strip():
                    break
                body_lines.append(line.rstrip())
            else:
                body_lines.append("")
            idx += 1

    while body_lines and not body_lines[-1].strip():
        body_lines.pop()

    span = _span_of_lines(lines, start_idx, idx)
    return (
        DeprecationDirective(
            version=version, body_lines=tuple(body_lines), span=span
        ),
        idx,
    )


# ---------------------------------------------------------------------------
# Section boundary detection
# ---------------------------------------------------------------------------


def _find_section_boundaries(lines: list[str]) -> list[tuple[int, str]]:
    sections: list[tuple[int, str]] = []
    idx = 0
    while idx < len(lines):
        title = _is_section_header(lines, idx)
        if title is not None:
            sections.append((idx, title))
            idx += 2
        else:
            idx += 1
    return sections


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------


def parse_docstring(
    body: str,
    quote: Literal['"""', "'''"],
    string_prefix: str,
    indentation: str,
    extra_parsers: Sequence[SectionParser] | None = None,
    section_aliases: Mapping[str, str] | None = None,
) -> ParsedDocstring:
    """Parse a raw docstring body into a ``ParsedDocstring``.

    Parameters
    ----------
    body : str
        The raw text between the opening and closing quotes.
    quote : Literal['\"\"\"', "'''"]
        The quote style used.
    string_prefix : str
        Any string prefix (e.g. ``"r"``).
    indentation : str
        The indentation of the docstring within its source file.
    extra_parsers : Sequence[SectionParser] | None, optional
        Additional section parsers to recognise beyond the built-in NumPy
        vocabulary.  Extra parsers take precedence over built-ins when their
        title sets overlap.

    Returns
    -------
    ParsedDocstring
        The parsed docstring with syntax, summary, sections, and issues.
    """
    if section_aliases:
        _register_aliases(section_aliases)
    dispatch = _build_dispatch(extra_parsers, section_aliases)

    if not body.strip():
        syntax = DocstringSyntax(
            raw_body=body,
            quote=quote,
            string_prefix=string_prefix,
            indentation=indentation,
            leading_blank_lines=0,
            trailing_blank_lines=0,
        )
        return ParsedDocstring(
            syntax=syntax,
            summary=None,
            deprecation=None,
            extended_description_lines=(),
            sections=(),
            parse_issues=(),
        )

    lines = body.split("\n")
    leading_blank = _count_leading_blank(lines)
    trailing_blank = _count_trailing_blank(lines)

    syntax = DocstringSyntax(
        raw_body=body,
        quote=quote,
        string_prefix=string_prefix,
        indentation=indentation,
        leading_blank_lines=leading_blank,
        trailing_blank_lines=trailing_blank,
    )

    issues: list[ParseIssue] = []

    summary: Summary | None = None
    content_start = leading_blank

    # Skip leading reST title + underline (e.g. "module.name\n==========")
    if (
        content_start + 1 < len(lines)
        and lines[content_start].strip()
        and re.match(r"^\s*[=]{3,}\s*$", lines[content_start + 1])
    ):
        content_start += 2
        while content_start < len(lines) and not lines[content_start].strip():
            content_start += 1

    if content_start < len(lines) and lines[content_start].strip():
        summary_text = lines[content_start].strip()
        summary_span = _span_of_lines(lines, content_start, content_start + 1)
        summary = Summary(text=summary_text, span=summary_span)
        content_start += 1
    elif content_start < len(lines):
        issues.append(
            ParseIssue(code="P001", message="No summary line found", span=None)
        )

    while content_start < len(lines) and not lines[content_start].strip():
        content_start += 1

    deprecation: DeprecationDirective | None = None
    if content_start < len(lines):
        dep_result = _try_parse_deprecation(lines, content_start)
        if dep_result is not None:
            deprecation, content_start = dep_result
            while content_start < len(lines) and not lines[content_start].strip():
                content_start += 1

    effective_end = len(lines) - trailing_blank if trailing_blank > 0 else len(lines)
    section_boundaries = _find_section_boundaries(lines[content_start:effective_end])
    section_boundaries = [
        (idx + content_start, title) for idx, title in section_boundaries
    ]

    ext_desc_end = section_boundaries[0][0] if section_boundaries else effective_end
    ext_desc_lines_raw = lines[content_start:ext_desc_end]
    while ext_desc_lines_raw and not ext_desc_lines_raw[-1].strip():
        ext_desc_lines_raw.pop()
    extended_description_lines = tuple(line.rstrip() for line in ext_desc_lines_raw)

    sections: list[SectionNode] = []
    for i, (sec_start, title) in enumerate(section_boundaries):
        if i + 1 < len(section_boundaries):
            sec_end = section_boundaries[i + 1][0]
        else:
            sec_end = effective_end

        title_span = _span_of_lines(lines, sec_start, sec_start + 1)
        underline_span = _span_of_lines(lines, sec_start + 1, sec_start + 2)
        body_start = sec_start + 2
        body_lines = lines[body_start:sec_end]
        while body_lines and not body_lines[-1].strip():
            body_lines.pop()
        section_span = _span_of_lines(lines, sec_start, sec_end)

        parse_fn = dispatch.get(title)
        if parse_fn is not None:
            ctx = SectionParseContext(
                title=title,
                body_lines=body_lines,
                title_span=title_span,
                underline_span=underline_span,
                section_span=section_span,
                all_lines=lines,
                body_start=body_start,
            )
            sections.append(parse_fn(ctx))
        else:
            sections.append(
                UnknownSection(
                    title=title,
                    title_span=title_span,
                    underline_span=underline_span,
                    body_lines=tuple(line.rstrip() for line in body_lines),
                    span=section_span,
                )
            )

    return ParsedDocstring(
        syntax=syntax,
        summary=summary,
        deprecation=deprecation,
        extended_description_lines=extended_description_lines,
        sections=tuple(sections),
        parse_issues=tuple(issues),
    )
