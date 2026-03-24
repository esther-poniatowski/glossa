"""Tests for glossa.infrastructure.extraction.ASTExtractor."""

from __future__ import annotations

import pytest

from glossa.core.contracts import TargetKind, Visibility
from glossa.infrastructure.extraction import ASTExtractor


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def extractor() -> ASTExtractor:
    return ASTExtractor()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract(extractor: ASTExtractor, source: str, source_id: str = "test.py"):
    return extractor.extract(source_id, source)


def _target_by_path(targets, *path: str):
    """Return the first target whose symbol_path matches the given path tuple."""
    for t in targets:
        if t.ref.symbol_path == path:
            return t
    raise KeyError(f"No target with symbol_path={path!r}. Available: {[t.ref.symbol_path for t in targets]}")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_extract_module_docstring(extractor: ASTExtractor) -> None:
    """A module with a docstring produces a MODULE target that has a docstring."""
    source = '"""Module docstring."""\n'
    targets = _extract(extractor, source)

    module = _target_by_path(targets)
    assert module.kind is TargetKind.MODULE
    assert module.docstring is not None
    assert "Module docstring." in module.docstring.body


def test_extract_function(extractor: ASTExtractor) -> None:
    """A top-level function is extracted as a FUNCTION target with signature facts."""
    source = "def greet(name: str) -> str:\n    return f'Hi {name}'\n"
    targets = _extract(extractor, source)

    func = _target_by_path(targets, "greet")
    assert func.kind is TargetKind.FUNCTION
    assert func.signature is not None
    param_names = [p.name for p in func.signature.parameters]
    assert "name" in param_names


def test_extract_class(extractor: ASTExtractor) -> None:
    """A class definition is extracted as a CLASS target."""
    source = "class MyClass:\n    pass\n"
    targets = _extract(extractor, source)

    cls = _target_by_path(targets, "MyClass")
    assert cls.kind is TargetKind.CLASS


def test_extract_method(extractor: ASTExtractor) -> None:
    """A method inside a class is extracted as a METHOD target."""
    source = (
        "class Calc:\n"
        "    def add(self, x: int, y: int) -> int:\n"
        "        return x + y\n"
    )
    targets = _extract(extractor, source)

    method = _target_by_path(targets, "Calc", "add")
    assert method.kind is TargetKind.METHOD


def test_extract_property(extractor: ASTExtractor) -> None:
    """A method decorated with @property is extracted as a PROPERTY target."""
    source = (
        "class Box:\n"
        "    @property\n"
        "    def value(self) -> int:\n"
        "        return self._value\n"
    )
    targets = _extract(extractor, source)

    prop = _target_by_path(targets, "Box", "value")
    assert prop.kind is TargetKind.PROPERTY


def test_extract_parameters(extractor: ASTExtractor) -> None:
    """Parameter facts carry correct name, annotation, default, and kind."""
    source = "def func(x: int, y: str = 'hello') -> None:\n    pass\n"
    targets = _extract(extractor, source)

    func = _target_by_path(targets, "func")
    assert func.signature is not None

    params = {p.name: p for p in func.signature.parameters}
    assert "x" in params
    assert params["x"].annotation == "int"
    assert params["x"].default is None

    assert "y" in params
    assert params["y"].annotation == "str"
    assert params["y"].default == "'hello'"


def test_extract_return_annotation(extractor: ASTExtractor) -> None:
    """A function annotated with '-> int' has return_annotation set to 'int'."""
    source = "def compute() -> int:\n    return 42\n"
    targets = _extract(extractor, source)

    func = _target_by_path(targets, "compute")
    assert func.signature is not None
    assert func.signature.return_annotation == "int"


def test_extract_exceptions(extractor: ASTExtractor) -> None:
    """A function that raises ValueError has a corresponding ExceptionFact."""
    source = (
        "def risky(x: int) -> int:\n"
        "    if x < 0:\n"
        "        raise ValueError('negative')\n"
        "    return x\n"
    )
    targets = _extract(extractor, source)

    func = _target_by_path(targets, "risky")
    exc_types = [e.type_name for e in func.exceptions]
    assert "ValueError" in exc_types


def test_extract_visibility(extractor: ASTExtractor) -> None:
    """public names are PUBLIC, _single-underscore names are INTERNAL, __mangled names are PRIVATE.

    Dunder names (__x__) start with '_' so they are classified as INTERNAL,
    because _visibility only returns PRIVATE for names that start with '__'
    but do NOT end with '__' (i.e. name-mangled identifiers).
    """
    source = (
        "def public_func(): pass\n"
        "def _internal_func(): pass\n"
        "def __mangled(): pass\n"
        "def __dunder__(): pass\n"
    )
    targets = _extract(extractor, source)

    pub = _target_by_path(targets, "public_func")
    assert pub.visibility is Visibility.PUBLIC

    internal = _target_by_path(targets, "_internal_func")
    assert internal.visibility is Visibility.INTERNAL

    # Name-mangled (__name, no trailing __): classified as PRIVATE.
    mangled = _target_by_path(targets, "__mangled")
    assert mangled.visibility is Visibility.PRIVATE

    # Dunder (__name__): starts with '_' but also ends with '__',
    # so _visibility falls through to the single-underscore branch → INTERNAL.
    dunder = _target_by_path(targets, "__dunder__")
    assert dunder.visibility is Visibility.INTERNAL


def test_extract_empty_file(extractor: ASTExtractor) -> None:
    """An empty file produces exactly one MODULE target with no docstring."""
    targets = _extract(extractor, "")

    assert len(targets) == 1
    module = targets[0]
    assert module.kind is TargetKind.MODULE
    assert module.docstring is None


def test_extract_nested_class(extractor: ASTExtractor) -> None:
    """A class nested inside another class is extracted with the full symbol_path."""
    source = (
        "class Outer:\n"
        "    class Inner:\n"
        "        pass\n"
    )
    targets = _extract(extractor, source)

    inner = _target_by_path(targets, "Outer", "Inner")
    assert inner.kind is TargetKind.CLASS
    assert inner.ref.symbol_path == ("Outer", "Inner")
