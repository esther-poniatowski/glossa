"""Comprehensive tests for glossa.domain.parsing.parse_docstring."""

from glossa.domain.parsing import parse_docstring
from glossa.domain.models import (
    TypedSection, TypedSectionKind, ProseSection, ProseSectionKind,
    InventorySection, InventorySectionKind, SeeAlsoSection, UnknownSection,
    DeprecationDirective, Summary,
)

_Q = '"""'
_P = ""
_I = "    "


def _parse(body: str):
    return parse_docstring(body, _Q, _P, _I)


# ---------------------------------------------------------------------------
# 1. Empty / whitespace bodies
# ---------------------------------------------------------------------------


def test_empty_body():
    result = _parse("")
    assert result.summary is None
    assert result.sections == ()
    assert result.extended_description_lines == ()
    assert result.deprecation is None


def test_whitespace_only():
    result = _parse("   \n   \n   ")
    assert result.summary is None
    assert result.sections == ()


# ---------------------------------------------------------------------------
# 2. Summary extraction
# ---------------------------------------------------------------------------


def test_single_line_summary():
    body = "Do something."
    result = _parse(body)
    assert isinstance(result.summary, Summary)
    assert result.summary.text == "Do something."
    assert result.sections == ()


def test_summary_with_extended_description():
    body = (
        "Do something.\n"
        "\n"
        "    This is a longer explanation that spans\n"
        "    multiple lines."
    )
    result = _parse(body)
    assert result.summary is not None
    assert result.summary.text == "Do something."
    assert len(result.extended_description_lines) == 2
    assert "longer explanation" in result.extended_description_lines[0]


# ---------------------------------------------------------------------------
# 3. Typed sections
# ---------------------------------------------------------------------------


def test_parameters_section():
    body = (
        "Do something.\n"
        "\n"
        "    Parameters\n"
        "    ----------\n"
        "    x : int\n"
        "        The first integer.\n"
        "    y : str\n"
        "        The second string.\n"
        "    z : float\n"
        "        The third float.\n"
    )
    result = _parse(body)
    assert len(result.sections) == 1
    sec = result.sections[0]
    assert isinstance(sec, TypedSection)
    assert sec.kind == TypedSectionKind.PARAMETERS
    assert len(sec.entries) == 3

    x, y, z = sec.entries
    assert x.name == "x"
    assert x.type_text == "int"
    assert "first integer" in x.description_lines[0]

    assert y.name == "y"
    assert y.type_text == "str"

    assert z.name == "z"
    assert z.type_text == "float"


def test_returns_section():
    body = (
        "Do something.\n"
        "\n"
        "    Returns\n"
        "    -------\n"
        "    int\n"
        "        The computed result.\n"
    )
    result = _parse(body)
    assert len(result.sections) == 1
    sec = result.sections[0]
    assert isinstance(sec, TypedSection)
    assert sec.kind == TypedSectionKind.RETURNS
    assert len(sec.entries) == 1
    entry = sec.entries[0]
    assert entry.name is None
    assert entry.type_text == "int"
    assert "computed result" in entry.description_lines[0]


def test_yields_section():
    body = (
        "Generate values.\n"
        "\n"
        "    Yields\n"
        "    ------\n"
        "    str\n"
        "        Each yielded string.\n"
    )
    result = _parse(body)
    assert len(result.sections) == 1
    sec = result.sections[0]
    assert isinstance(sec, TypedSection)
    assert sec.kind == TypedSectionKind.YIELDS
    assert len(sec.entries) == 1
    entry = sec.entries[0]
    assert entry.name is None
    assert entry.type_text == "str"


def test_raises_section():
    body = (
        "Do something.\n"
        "\n"
        "    Raises\n"
        "    ------\n"
        "    ValueError\n"
        "        When the input is invalid.\n"
        "    TypeError\n"
        "        When the type is wrong.\n"
    )
    result = _parse(body)
    assert len(result.sections) == 1
    sec = result.sections[0]
    assert isinstance(sec, TypedSection)
    assert sec.kind == TypedSectionKind.RAISES
    assert len(sec.entries) == 2

    names = [e.name for e in sec.entries]
    assert "ValueError" in names
    assert "TypeError" in names


def test_warns_section():
    body = (
        "Do something.\n"
        "\n"
        "    Warns\n"
        "    -----\n"
        "    UserWarning\n"
        "        Issued when something suspicious happens.\n"
    )
    result = _parse(body)
    assert len(result.sections) == 1
    sec = result.sections[0]
    assert isinstance(sec, TypedSection)
    assert sec.kind == TypedSectionKind.WARNS
    assert len(sec.entries) == 1
    assert sec.entries[0].name == "UserWarning"


def test_attributes_section():
    body = (
        "A class.\n"
        "\n"
        "    Attributes\n"
        "    ----------\n"
        "    name : str\n"
        "        The object name.\n"
        "    value : int\n"
        "        The stored value.\n"
    )
    result = _parse(body)
    assert len(result.sections) == 1
    sec = result.sections[0]
    assert isinstance(sec, TypedSection)
    assert sec.kind == TypedSectionKind.ATTRIBUTES
    assert len(sec.entries) == 2
    assert sec.entries[0].name == "name"
    assert sec.entries[1].name == "value"


# ---------------------------------------------------------------------------
# 4. Prose sections
# ---------------------------------------------------------------------------


def test_notes_section():
    body = (
        "Do something.\n"
        "\n"
        "    Notes\n"
        "    -----\n"
        "    This is an important note.\n"
        "    It spans two lines.\n"
    )
    result = _parse(body)
    assert len(result.sections) == 1
    sec = result.sections[0]
    assert isinstance(sec, ProseSection)
    assert sec.kind == ProseSectionKind.NOTES
    assert any("important note" in line for line in sec.body_lines)


def test_examples_section():
    body = (
        "Do something.\n"
        "\n"
        "    Examples\n"
        "    --------\n"
        "    >>> result = do_something(1, 2)\n"
        "    >>> print(result)\n"
        "    3\n"
    )
    result = _parse(body)
    assert len(result.sections) == 1
    sec = result.sections[0]
    assert isinstance(sec, ProseSection)
    assert sec.kind == ProseSectionKind.EXAMPLES
    assert any("do_something" in line for line in sec.body_lines)


# ---------------------------------------------------------------------------
# 5. Inventory and See Also sections
# ---------------------------------------------------------------------------


def test_see_also_section():
    body = (
        "Do something.\n"
        "\n"
        "    See Also\n"
        "    --------\n"
        "    other_func\n"
        "        A related function.\n"
        "    another_func\n"
        "        Another related function.\n"
    )
    result = _parse(body)
    assert len(result.sections) == 1
    sec = result.sections[0]
    assert isinstance(sec, SeeAlsoSection)
    assert len(sec.items) == 2
    names = [item.name for item in sec.items]
    assert "other_func" in names
    assert "another_func" in names


def test_classes_inventory():
    body = (
        "Module summary.\n"
        "\n"
        "    Classes\n"
        "    -------\n"
        "    Foo\n"
        "        The Foo class.\n"
        "    Bar\n"
        "        The Bar class.\n"
    )
    result = _parse(body)
    assert len(result.sections) == 1
    sec = result.sections[0]
    assert isinstance(sec, InventorySection)
    assert sec.kind == InventorySectionKind.CLASSES
    assert len(sec.items) == 2
    names = [item.name for item in sec.items]
    assert "Foo" in names
    assert "Bar" in names


def test_functions_inventory():
    body = (
        "Module summary.\n"
        "\n"
        "    Functions\n"
        "    ---------\n"
        "    do_this\n"
        "        Does this.\n"
        "    do_that\n"
        "        Does that.\n"
    )
    result = _parse(body)
    assert len(result.sections) == 1
    sec = result.sections[0]
    assert isinstance(sec, InventorySection)
    assert sec.kind == InventorySectionKind.FUNCTIONS
    assert len(sec.items) == 2


# ---------------------------------------------------------------------------
# 6. Unknown sections
# ---------------------------------------------------------------------------


def test_unknown_section():
    body = (
        "Do something.\n"
        "\n"
        "    CustomSection\n"
        "    -------------\n"
        "    Some content here.\n"
    )
    result = _parse(body)
    assert len(result.sections) == 1
    sec = result.sections[0]
    assert isinstance(sec, UnknownSection)
    assert sec.title == "CustomSection"
    assert any("Some content" in line for line in sec.body_lines)


# ---------------------------------------------------------------------------
# 7. Multiple sections
# ---------------------------------------------------------------------------


def test_multiple_sections():
    body = (
        "Do something.\n"
        "\n"
        "    Parameters\n"
        "    ----------\n"
        "    x : int\n"
        "        Input value.\n"
        "\n"
        "    Returns\n"
        "    -------\n"
        "    int\n"
        "        Output value.\n"
        "\n"
        "    Examples\n"
        "    --------\n"
        "    >>> do_something(1)\n"
        "    1\n"
    )
    result = _parse(body)
    assert len(result.sections) == 3

    params = result.sections[0]
    returns = result.sections[1]
    examples = result.sections[2]

    assert isinstance(params, TypedSection)
    assert params.kind == TypedSectionKind.PARAMETERS

    assert isinstance(returns, TypedSection)
    assert returns.kind == TypedSectionKind.RETURNS

    assert isinstance(examples, ProseSection)
    assert examples.kind == ProseSectionKind.EXAMPLES


# ---------------------------------------------------------------------------
# 8. Deprecation directive
# ---------------------------------------------------------------------------


def test_deprecation_directive():
    body = (
        "Do something.\n"
        "\n"
        "    .. deprecated:: 1.0\n"
        "        Use new_func instead.\n"
    )
    result = _parse(body)
    assert isinstance(result.deprecation, DeprecationDirective)
    assert result.deprecation.version == "1.0"
    assert any("new_func" in line for line in result.deprecation.body_lines)
    assert result.sections == ()


def test_deprecation_before_sections():
    body = (
        "Do something.\n"
        "\n"
        "    .. deprecated:: 2.3\n"
        "        Use other_func instead.\n"
        "\n"
        "    Parameters\n"
        "    ----------\n"
        "    x : int\n"
        "        The input.\n"
    )
    result = _parse(body)
    assert result.summary is not None
    assert result.summary.text == "Do something."
    assert isinstance(result.deprecation, DeprecationDirective)
    assert result.deprecation.version == "2.3"
    assert len(result.sections) == 1
    assert isinstance(result.sections[0], TypedSection)
    assert result.sections[0].kind == TypedSectionKind.PARAMETERS


# ---------------------------------------------------------------------------
# 9. Duplicate sections
# ---------------------------------------------------------------------------


def test_duplicate_sections():
    body = (
        "Do something.\n"
        "\n"
        "    Parameters\n"
        "    ----------\n"
        "    x : int\n"
        "        First param.\n"
        "\n"
        "    Parameters\n"
        "    ----------\n"
        "    y : str\n"
        "        Second param in duplicate section.\n"
    )
    result = _parse(body)
    param_sections = [
        s for s in result.sections
        if isinstance(s, TypedSection) and s.kind == TypedSectionKind.PARAMETERS
    ]
    assert len(param_sections) == 2
    assert param_sections[0].entries[0].name == "x"
    assert param_sections[1].entries[0].name == "y"


# ---------------------------------------------------------------------------
# 10. Syntax / lossless properties
# ---------------------------------------------------------------------------


def test_leading_trailing_blanks():
    body = "\n\n    Do something.\n\n"
    result = _parse(body)
    assert result.syntax.leading_blank_lines == 2
    assert result.syntax.trailing_blank_lines == 1


def test_lossless_raw_body():
    body = (
        "Do something.\n"
        "\n"
        "    Parameters\n"
        "    ----------\n"
        "    x : int\n"
        "        A value.\n"
    )
    result = _parse(body)
    assert result.syntax.raw_body == body
    assert result.syntax.quote == _Q
    assert result.syntax.string_prefix == _P
    assert result.syntax.indentation == _I


# ---------------------------------------------------------------------------
# 11. Default and optional type annotations
# ---------------------------------------------------------------------------


def test_params_with_defaults():
    body = (
        "Do something.\n"
        "\n"
        "    Parameters\n"
        "    ----------\n"
        "    x : int, default 5\n"
        "        An integer with a default.\n"
    )
    result = _parse(body)
    sec = result.sections[0]
    assert isinstance(sec, TypedSection)
    entry = sec.entries[0]
    assert entry.name == "x"
    assert entry.type_text == "int"
    assert entry.default_text == "default 5"


def test_optional_type():
    body = (
        "Do something.\n"
        "\n"
        "    Parameters\n"
        "    ----------\n"
        "    x : int, optional\n"
        "        An optional integer.\n"
    )
    result = _parse(body)
    sec = result.sections[0]
    assert isinstance(sec, TypedSection)
    entry = sec.entries[0]
    assert entry.name == "x"
    assert entry.type_text == "int"
    assert entry.default_text == "optional"


# ---------------------------------------------------------------------------
# 12. Star parameters
# ---------------------------------------------------------------------------


def test_star_params():
    body = (
        "Do something.\n"
        "\n"
        "    Parameters\n"
        "    ----------\n"
        "    *args : tuple\n"
        "        Positional arguments.\n"
        "    **kwargs : dict\n"
        "        Keyword arguments.\n"
    )
    result = _parse(body)
    sec = result.sections[0]
    assert isinstance(sec, TypedSection)
    assert len(sec.entries) == 2

    names = [e.name for e in sec.entries]
    assert "*args" in names
    assert "**kwargs" in names

    for entry in sec.entries:
        if entry.name == "*args":
            assert entry.type_text == "tuple"
        elif entry.name == "**kwargs":
            assert entry.type_text == "dict"
