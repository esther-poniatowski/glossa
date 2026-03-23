from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator, Sequence

from glossa.errors import DiscoveryError


class FileDiscovery:
    """Walk configured paths and yield Python source files."""

    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path

    def discover(self, paths: Sequence[str], exclude: Sequence[str] = ()) -> Iterator[str]:
        """Yield project-relative POSIX path strings for Python source files."""
        for path_str in paths:
            target = self._base_path / path_str
            if target.is_file() and target.suffix == ".py":
                rel = target.relative_to(self._base_path).as_posix()
                if not self._is_excluded(rel, exclude):
                    yield rel
            elif target.is_dir():
                for root, dirs, files in os.walk(target):
                    # Filter excluded directories
                    dirs[:] = [
                        d for d in dirs
                        if not self._is_excluded(
                            Path(root, d).relative_to(self._base_path).as_posix() + "/",
                            exclude,
                        )
                    ]
                    for f in sorted(files):
                        if f.endswith(".py"):
                            full = Path(root) / f
                            rel = full.relative_to(self._base_path).as_posix()
                            if not self._is_excluded(rel, exclude):
                                yield rel
            else:
                raise DiscoveryError(f"Path does not exist: {path_str}")

    @staticmethod
    def _is_excluded(rel_path: str, patterns: Sequence[str]) -> bool:
        import fnmatch
        return any(fnmatch.fnmatch(rel_path, p) for p in patterns)
