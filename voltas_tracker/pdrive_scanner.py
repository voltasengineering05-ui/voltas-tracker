"""Read-only scan of the P: drive folder tree.

Never writes, moves, renames, or deletes anything — it only lists files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# File types that count as documents; tuned once we see the real drive.
DOCUMENT_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".dwg", ".dxf",
    ".msg", ".eml", ".zip", ".jpg", ".png", ".tif",
}


@dataclass
class ScannedFile:
    path: str
    name: str
    folder: str
    size: int
    modified: float


def scan(root: str | Path) -> list[ScannedFile]:
    """Walk the tree under `root` and return every document-like file."""
    results: list[ScannedFile] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if Path(fn).suffix.lower() not in DOCUMENT_EXTENSIONS:
                continue
            full = Path(dirpath) / fn
            try:
                stat = full.stat()
            except OSError:
                continue
            results.append(
                ScannedFile(
                    path=str(full),
                    name=fn,
                    folder=str(Path(dirpath).relative_to(root)),
                    size=stat.st_size,
                    modified=stat.st_mtime,
                )
            )
    return results
