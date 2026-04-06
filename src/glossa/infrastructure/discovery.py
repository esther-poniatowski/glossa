from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator, Sequence

from glossa.errors import DiscoveryError


class FileDiscovery:
    """Walk configured paths and yield Python source files."""

    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path.resolve()

    def _make_source_id(self, full_path: Path) -> str:
        """Return a relative POSIX string if inside base_path, else absolute."""
        full = full_path.resolve()
        if full.is_relative_to(self._base_path):
            return full.relative_to(self._base_path).as_posix()
        return str(full)

    def discover(self, paths: Sequence[str], exclude: Sequence[str] = ()) -> Iterator[str]:
        """Yield source-id strings for Python source files."""
        for path_str in paths:
            target = Path(path_str) if Path(path_str).is_absolute() else self._base_path / path_str
            target = target.resolve()

            if target.is_file() and target.suffix == ".py":
                source_id = self._make_source_id(target)
                if not self._is_excluded(source_id, exclude):
                    yield source_id
            elif target.is_dir():
                for root, dirs, files in os.walk(target):
                    dirs[:] = sorted(
                        d for d in dirs
                        if not self._is_excluded(
                            self._make_source_id(Path(root, d)) + "/",
                            exclude,
                        )
                    )
                    for f in sorted(files):
                        if f.endswith(".py"):
                            full = Path(root) / f
                            source_id = self._make_source_id(full)
                            if not self._is_excluded(source_id, exclude):
                                yield source_id
            else:
                raise DiscoveryError(f"Path does not exist: {path_str}")

    @staticmethod
    def _is_excluded(rel_path: str, patterns: Sequence[str]) -> bool:
        import fnmatch
        return any(fnmatch.fnmatch(rel_path, p) for p in patterns)
