"""The learning loop: saved human corrections.

Every time a reviewer confirms or corrects a match during
`voltas-tracker review`, the (project, document) → file mapping is stored
here and applied deterministically on every future run. Accumulated
corrections double as a training dataset if fine-tuning a small local model
ever proves worthwhile.
"""

from __future__ import annotations

import json
from pathlib import Path

from .excel_reader import ExpectedDocument

STORE_PATH = Path.home() / ".voltas-tracker" / "feedback.json"


class FeedbackStore:
    def __init__(self, path: Path = STORE_PATH):
        self.path = path
        self._data: dict[str, str] = {}
        if path.exists():
            self._data = json.loads(path.read_text())

    @staticmethod
    def _key(doc: ExpectedDocument) -> str:
        return f"{doc.project}::{doc.name}".lower()

    def lookup(self, doc: ExpectedDocument) -> str | None:
        """Return the file path a human previously pinned for this document."""
        return self._data.get(self._key(doc))

    def record(self, doc: ExpectedDocument, file_path: str) -> None:
        self._data[self._key(doc)] = file_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2))
