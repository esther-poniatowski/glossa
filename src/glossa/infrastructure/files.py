from __future__ import annotations

from pathlib import Path

from glossa.errors import FileWriteError


class LocalFilePort:
    """Read source files and write edited output."""

    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path

    def read(self, source_id: str) -> str:
        p = Path(source_id)
        path = p if p.is_absolute() else self._base_path / source_id
        return path.read_text(encoding="utf-8")

    def write(self, source_id: str, content: str) -> None:
        p = Path(source_id)
        path = p if p.is_absolute() else self._base_path / source_id
        try:
            path.write_text(content, encoding="utf-8")
        except OSError as exc:
            raise FileWriteError(f"Failed to write {source_id}: {exc}") from exc
