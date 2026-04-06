from __future__ import annotations

import json
from typing import Sequence

from glossa.domain.contracts import Diagnostic


def format_text(
    diagnostics: Sequence[Diagnostic],
    show_source: bool = True,
) -> str:
    """Format diagnostics as human-readable text."""
    if not diagnostics:
        return "All checks passed."

    lines: list[str] = []
    for diag in diagnostics:
        source_id = diag.target.source_id
        symbol = ".".join(diag.target.symbol_path) if diag.target.symbol_path else ""

        location = source_id
        if diag.span is not None:
            location += f":{diag.span.start.line}:{diag.span.start.column}"

        sev = diag.severity.value.upper()

        line = f"{location}: {sev} {diag.rule} {diag.message}"
        if show_source and symbol:
            line += f" [{symbol}]"
        if diag.fix is not None:
            line += " (fixable)"
        lines.append(line)

    lines.append("")
    lines.append(f"Found {len(diagnostics)} issue(s).")
    return "\n".join(lines)


def format_json(diagnostics: Sequence[Diagnostic]) -> str:
    """Format diagnostics as JSON."""
    items = []
    for diag in diagnostics:
        item: dict[str, object] = {
            "rule": diag.rule,
            "message": diag.message,
            "severity": diag.severity.value,
            "source_id": diag.target.source_id,
            "symbol_path": list(diag.target.symbol_path),
        }
        if diag.span is not None:
            item["location"] = {
                "start_line": diag.span.start.line,
                "start_column": diag.span.start.column,
                "end_line": diag.span.end.line,
                "end_column": diag.span.end.column,
            }
        item["fixable"] = diag.fix is not None
        items.append(item)

    return json.dumps({"diagnostics": items, "count": len(items)}, indent=2)
