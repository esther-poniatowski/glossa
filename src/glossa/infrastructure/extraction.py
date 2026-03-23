from __future__ import annotations

import ast
import re

from glossa.core.contracts import (
    AttributeFact,
    ExceptionFact,
    ExtractedDocstring,
    ExtractedTarget,
    ModuleSymbolFact,
    ParameterFact,
    RelatedTargets,
    SignatureFacts,
    SourceRef,
    TargetKind,
    TextPosition,
    TextSpan,
    Visibility,
    WarningFact,
)
from glossa.errors import ExtractionError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _visibility(name: str) -> Visibility:
    if name.startswith("__") and not name.endswith("__"):
        return Visibility.PRIVATE
    if name.startswith("_"):
        return Visibility.INTERNAL
    return Visibility.PUBLIC


def _is_test_target(name: str, source_id: str) -> bool:
    return name.startswith("test_") or "tests/" in source_id


def _annotation_str(node: ast.expr | None) -> str | None:
    if node is None:
        return None
    return ast.unparse(node)


def _default_str(node: ast.expr | None) -> str | None:
    if node is None:
        return None
    return ast.unparse(node)


def _text_pos(line: int, col: int) -> TextPosition:
    return TextPosition(line=line, column=col)


def _node_span(node: ast.AST) -> TextSpan:
    start = _text_pos(node.lineno, node.col_offset)  # type: ignore[attr-defined]
    end = _text_pos(
        getattr(node, "end_lineno", node.lineno),  # type: ignore[attr-defined]
        getattr(node, "end_col_offset", node.col_offset),  # type: ignore[attr-defined]
    )
    return TextSpan(start=start, end=end)


# ---------------------------------------------------------------------------
# Docstring extraction
# ---------------------------------------------------------------------------

_QUOTE_RE = re.compile(r'^([brBRuUfF]*)(?:"""|\'{3}|"|\')', re.MULTILINE)


def _extract_docstring(
    node: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
    source_lines: list[str],
) -> ExtractedDocstring | None:
    raw_body = ast.get_docstring(node, clean=False)
    if raw_body is None:
        return None

    # Find the actual Constant node that holds the docstring.
    body = node.body
    if not body:
        return None
    first_stmt = body[0]
    if not isinstance(first_stmt, ast.Expr):
        return None
    value = first_stmt.value
    if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
        return None

    literal_span = _node_span(value)

    # Recover the raw source text for the literal to detect quote style.
    start_line = value.lineno - 1  # 0-indexed
    end_line = value.end_lineno - 1  # type: ignore[attr-defined]
    raw_literal_lines = source_lines[start_line : end_line + 1]
    raw_literal = "\n".join(raw_literal_lines)

    # Detect optional prefix (b/r/u) and triple-quote style.
    prefix = ""
    quote: str = '"""'
    match = _QUOTE_RE.search(raw_literal)
    if match:
        prefix = match.group(1)
        matched_quote = match.group(0)[len(prefix):]
        # Normalise to triple-quote form.
        if matched_quote in ('"""', "'''"):
            quote = matched_quote
        elif matched_quote in ('"', "'"):
            quote = matched_quote * 3  # single-quoted becomes triple for uniformity

    # Indentation: leading whitespace on the opening line of the literal.
    opening_line = source_lines[start_line]
    indentation = opening_line[: len(opening_line) - len(opening_line.lstrip())]

    quote_len = len(matched_quote) if match else 3
    body_span = TextSpan(
        start=_text_pos(value.lineno, value.col_offset + len(prefix) + quote_len),
        end=_text_pos(
            getattr(value, "end_lineno", value.lineno),
            getattr(value, "end_col_offset", value.col_offset) - quote_len,
        ),
    )

    return ExtractedDocstring(
        body=raw_body,
        quote=quote,  # type: ignore[arg-type]
        string_prefix=prefix,
        indentation=indentation,
        body_span=body_span,
        literal_span=literal_span,
    )


# ---------------------------------------------------------------------------
# Signature extraction
# ---------------------------------------------------------------------------


def _extract_signature(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> SignatureFacts:
    args = node.args
    params: list[ParameterFact] = []

    # positional-only (Python 3.8+)
    posonlyargs = getattr(args, "posonlyargs", [])
    pos_defaults_offset = len(args.args) + len(posonlyargs) - len(args.defaults)

    all_pos = list(posonlyargs) + list(args.args)
    defaults_map: dict[int, ast.expr] = {}
    for i, d in enumerate(args.defaults):
        defaults_map[len(all_pos) - len(args.defaults) + i] = d

    for idx, arg in enumerate(posonlyargs):
        default = _default_str(defaults_map.get(idx))
        params.append(
            ParameterFact(
                name=arg.arg,
                annotation=_annotation_str(arg.annotation),
                default=default,
                kind="positional_only",
            )
        )

    offset = len(posonlyargs)
    for idx, arg in enumerate(args.args):
        abs_idx = offset + idx
        default = _default_str(defaults_map.get(abs_idx))
        params.append(
            ParameterFact(
                name=arg.arg,
                annotation=_annotation_str(arg.annotation),
                default=default,
                kind="positional_or_keyword",
            )
        )

    if args.vararg:
        params.append(
            ParameterFact(
                name=args.vararg.arg,
                annotation=_annotation_str(args.vararg.annotation),
                default=None,
                kind="var_positional",
            )
        )

    kw_defaults: dict[int, ast.expr | None] = {
        i: d for i, d in enumerate(args.kw_defaults)
    }
    for idx, arg in enumerate(args.kwonlyargs):
        default = _default_str(kw_defaults.get(idx))
        params.append(
            ParameterFact(
                name=arg.arg,
                annotation=_annotation_str(arg.annotation),
                default=default,
                kind="keyword_only",
            )
        )

    if args.kwarg:
        params.append(
            ParameterFact(
                name=args.kwarg.arg,
                annotation=_annotation_str(args.kwarg.annotation),
                default=None,
                kind="var_keyword",
            )
        )

    # Detect return annotation and whether the function returns/yields a value.
    return_annotation = _annotation_str(node.returns)
    returns_value = _has_return_value(node)
    yields_value = _has_yield(node)

    return SignatureFacts(
        parameters=tuple(params),
        return_annotation=return_annotation,
        returns_value=returns_value,
        yields_value=yields_value,
    )


def _has_return_value(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for child in ast.walk(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child is not node:
            continue  # Don't descend into nested functions
        if isinstance(child, ast.Return) and child.value is not None:
            return True
    return False


def _has_yield(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for child in ast.walk(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child is not node:
            continue
        if isinstance(child, (ast.Yield, ast.YieldFrom)):
            return True
    return False


# ---------------------------------------------------------------------------
# Exception / Warning facts
# ---------------------------------------------------------------------------


def _extract_exceptions(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[ExceptionFact, ...]:
    facts: list[ExceptionFact] = []
    _collect_exceptions(node.body, facts, in_conditional=False)
    return tuple(facts)


def _collect_exceptions(
    stmts: list[ast.stmt],
    facts: list[ExceptionFact],
    in_conditional: bool,
) -> None:
    for stmt in stmts:
        if isinstance(stmt, ast.Raise):
            exc_node = stmt.exc
            if exc_node is None:
                # bare re-raise
                facts.append(
                    ExceptionFact(
                        type_name="",
                        evidence="reraise",
                        confidence="high" if not in_conditional else "medium",
                    )
                )
            else:
                type_name = _exc_type_name(exc_node)
                evidence: str = "raise"
                confidence = "high" if not in_conditional else "medium"
                facts.append(
                    ExceptionFact(
                        type_name=type_name,
                        evidence=evidence,  # type: ignore[arg-type]
                        confidence=confidence,  # type: ignore[arg-type]
                    )
                )
        elif isinstance(stmt, (ast.If, ast.For, ast.While, ast.With, ast.AsyncWith, ast.AsyncFor)):
            sub_stmts = _get_sub_stmts(stmt)
            _collect_exceptions(sub_stmts, facts, in_conditional=True)
        elif isinstance(stmt, ast.Try):
            _collect_exceptions(stmt.body, facts, in_conditional=True)
            for handler in stmt.handlers:
                _collect_exceptions(handler.body, facts, in_conditional=True)
            _collect_exceptions(stmt.orelse, facts, in_conditional=True)
            _collect_exceptions(stmt.finalbody, facts, in_conditional=True)
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            pass  # Don't descend into nested function definitions
        else:
            # Recurse into any remaining child statements
            for child in ast.iter_child_nodes(stmt):
                if isinstance(child, ast.stmt):
                    _collect_exceptions([child], facts, in_conditional=in_conditional)


def _get_sub_stmts(node: ast.stmt) -> list[ast.stmt]:
    stmts: list[ast.stmt] = []
    for field, value in ast.iter_fields(node):
        if isinstance(value, list):
            for item in value:
                if isinstance(item, ast.stmt):
                    stmts.append(item)
    return stmts


def _exc_type_name(node: ast.expr) -> str:
    if isinstance(node, ast.Call):
        return _exc_type_name(node.func)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_exc_type_name(node.value)}.{node.attr}"
    return ast.unparse(node)


def _extract_warnings(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[WarningFact, ...]:
    facts: list[WarningFact] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            is_warn = (
                (isinstance(func, ast.Attribute) and func.attr == "warn")
                or (isinstance(func, ast.Name) and func.id == "warn")
            )
            if is_warn:
                # Extract warning category (second positional arg or 'category' kwarg).
                type_name = "UserWarning"
                if len(child.args) >= 2:
                    type_name = ast.unparse(child.args[1])
                else:
                    for kw in child.keywords:
                        if kw.arg == "category":
                            type_name = ast.unparse(kw.value)
                            break
                facts.append(
                    WarningFact(type_name=type_name, confidence="high")
                )
    return tuple(facts)


# ---------------------------------------------------------------------------
# Attribute facts
# ---------------------------------------------------------------------------


def _extract_class_attributes(
    class_node: ast.ClassDef,
) -> tuple[AttributeFact, ...]:
    facts: list[AttributeFact] = []
    seen: set[str] = set()

    # Class-level annotated assignments: `x: int = ...`
    for stmt in class_node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            name = stmt.target.id
            if name not in seen:
                seen.add(name)
                facts.append(
                    AttributeFact(
                        name=name,
                        annotation=_annotation_str(stmt.annotation),
                        defined_in_init=False,
                        is_public=not name.startswith("_"),
                    )
                )

    # __init__ self.x assignments
    for stmt in class_node.body:
        if (
            isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
            and stmt.name == "__init__"
        ):
            for child in ast.walk(stmt):
                if (
                    isinstance(child, ast.Assign)
                    and len(child.targets) == 1
                    and isinstance(child.targets[0], ast.Attribute)
                    and isinstance(child.targets[0].value, ast.Name)
                    and child.targets[0].value.id == "self"
                ):
                    attr_name = child.targets[0].attr
                    if attr_name not in seen:
                        seen.add(attr_name)
                        facts.append(
                            AttributeFact(
                                name=attr_name,
                                annotation=None,
                                defined_in_init=True,
                                is_public=not attr_name.startswith("_"),
                            )
                        )
                elif (
                    isinstance(child, ast.AnnAssign)
                    and isinstance(child.target, ast.Attribute)
                    and isinstance(child.target.value, ast.Name)
                    and child.target.value.id == "self"
                ):
                    attr_name = child.target.attr
                    if attr_name not in seen:
                        seen.add(attr_name)
                        facts.append(
                            AttributeFact(
                                name=attr_name,
                                annotation=_annotation_str(child.annotation),
                                defined_in_init=True,
                                is_public=not attr_name.startswith("_"),
                            )
                        )

    return tuple(facts)


# ---------------------------------------------------------------------------
# Decorator helpers
# ---------------------------------------------------------------------------


def _decorator_names(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> tuple[str, ...]:
    names: list[str] = []
    for dec in node.decorator_list:
        names.append(ast.unparse(dec))
    return tuple(names)


def _is_property(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name) and dec.id == "property":
            return True
        if isinstance(dec, ast.Attribute) and dec.attr == "property":
            return True
    return False


def _target_suppression_lines(
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
    source_lines: list[str],
) -> tuple[str, ...]:
    return (source_lines[node.lineno - 1],)


def _module_suppression_lines(source_lines: list[str]) -> tuple[str, ...]:
    lines: list[str] = []
    for line in source_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            lines.append(line)
            continue
        break
    return tuple(lines)


# ---------------------------------------------------------------------------
# Main extractor
# ---------------------------------------------------------------------------


class ASTExtractor:
    """Extract lintable targets from Python source text using the AST."""

    def extract(self, source_id: str, source_text: str) -> tuple[ExtractedTarget, ...]:
        """Parse *source_text* and return all extracted targets.

        Parameters
        ----------
        source_id : str
            Project-relative POSIX path used to build ``SourceRef`` values.
        source_text : str
            Full text content of the Python source file.

        Returns
        -------
        tuple[ExtractedTarget, ...]
            One ``ExtractedTarget`` per documentable symbol in the file.

        Raises
        ------
        ExtractionError
            If the source text cannot be parsed as valid Python.
        """
        try:
            tree = ast.parse(source_text, filename=source_id)
        except SyntaxError as exc:
            raise ExtractionError(
                f"Failed to parse {source_id}: {exc}"
            ) from exc

        source_lines = source_text.splitlines()
        targets: list[ExtractedTarget] = []

        # Module target
        module_ref = SourceRef(source_id=source_id, symbol_path=())
        module_docstring = _extract_docstring(tree, source_lines)
        module_symbols = self._collect_module_symbols(tree)
        targets.append(
            ExtractedTarget(
                ref=module_ref,
                kind=TargetKind.MODULE,
                visibility=Visibility.PUBLIC,
                is_test_target=_is_test_target("", source_id),
                docstring=module_docstring,
                signature=None,
                exceptions=(),
                warnings=(),
                attributes=(),
                module_symbols=module_symbols,
                decorators=(),
                related=RelatedTargets(),
                suppression_lines=_module_suppression_lines(source_lines),
            )
        )

        # Walk top-level statements
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                targets.extend(
                    self._extract_class(source_id, source_lines, node, parent_path=())
                )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                targets.append(
                    self._extract_function(
                        source_id,
                        source_lines,
                        node,
                        parent_path=(),
                        parent_ref=None,
                    )
                )

        return tuple(targets)

    # ------------------------------------------------------------------
    # Class extraction
    # ------------------------------------------------------------------

    def _extract_class(
        self,
        source_id: str,
        source_lines: list[str],
        node: ast.ClassDef,
        parent_path: tuple[str, ...],
    ) -> list[ExtractedTarget]:
        targets: list[ExtractedTarget] = []
        class_path = parent_path + (node.name,)
        class_ref = SourceRef(source_id=source_id, symbol_path=class_path)

        attributes = _extract_class_attributes(node)
        docstring = _extract_docstring(node, source_lines)
        decorators = _decorator_names(node)

        # Find constructor ref (if __init__ exists)
        constructor_ref: SourceRef | None = None
        for stmt in node.body:
            if (
                isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
                and stmt.name == "__init__"
            ):
                constructor_ref = SourceRef(
                    source_id=source_id,
                    symbol_path=class_path + ("__init__",),
                )
                break

        targets.append(
            ExtractedTarget(
                ref=class_ref,
                kind=TargetKind.CLASS,
                visibility=_visibility(node.name),
                is_test_target=_is_test_target(node.name, source_id),
                docstring=docstring,
                signature=None,
                exceptions=(),
                warnings=(),
                attributes=attributes,
                module_symbols=(),
                decorators=decorators,
                related=RelatedTargets(constructor=constructor_ref),
                suppression_lines=_target_suppression_lines(node, source_lines),
            )
        )

        # Methods and nested classes
        for stmt in node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                targets.append(
                    self._extract_function(
                        source_id,
                        source_lines,
                        stmt,
                        parent_path=class_path,
                        parent_ref=class_ref,
                    )
                )
            elif isinstance(stmt, ast.ClassDef):
                targets.extend(
                    self._extract_class(source_id, source_lines, stmt, parent_path=class_path)
                )

        return targets

    # ------------------------------------------------------------------
    # Function / method extraction
    # ------------------------------------------------------------------

    def _extract_function(
        self,
        source_id: str,
        source_lines: list[str],
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        parent_path: tuple[str, ...],
        parent_ref: SourceRef | None,
    ) -> ExtractedTarget:
        func_path = parent_path + (node.name,)
        func_ref = SourceRef(source_id=source_id, symbol_path=func_path)

        # Determine kind
        if _is_property(node):
            kind = TargetKind.PROPERTY
        elif parent_path:
            kind = TargetKind.METHOD
        else:
            kind = TargetKind.FUNCTION

        docstring = _extract_docstring(node, source_lines)
        signature = _extract_signature(node)
        exceptions = _extract_exceptions(node)
        warnings = _extract_warnings(node)
        decorators = _decorator_names(node)

        related = RelatedTargets(parent=parent_ref)

        return ExtractedTarget(
            ref=func_ref,
            kind=kind,
            visibility=_visibility(node.name),
            is_test_target=_is_test_target(node.name, source_id),
            docstring=docstring,
            signature=signature,
            exceptions=exceptions,
            warnings=warnings,
            attributes=(),
            module_symbols=(),
            decorators=decorators,
            related=related,
            suppression_lines=_target_suppression_lines(node, source_lines),
        )

    # ------------------------------------------------------------------
    # Module symbols
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_module_symbols(tree: ast.Module) -> tuple[ModuleSymbolFact, ...]:
        facts: list[ModuleSymbolFact] = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                facts.append(
                    ModuleSymbolFact(
                        name=node.name,
                        kind="class",
                        is_public=not node.name.startswith("_"),
                    )
                )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                facts.append(
                    ModuleSymbolFact(
                        name=node.name,
                        kind="function",
                        is_public=not node.name.startswith("_"),
                    )
                )
        return tuple(facts)
