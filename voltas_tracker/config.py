"""Local configuration: paths to the Excel tracker, P: drive root, etc.

Stored as JSON in the user's home directory so no secrets or client paths
ever live in this repo.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

CONFIG_PATH = Path.home() / ".voltas-tracker" / "config.json"


@dataclass
class Config:
    excel_path: str = ""
    pdrive_root: str = ""
    # Fuzzy-match score (0-100) below which a match is flagged for review.
    review_threshold: int = 80
    # Optional: local Ollama model used only for ambiguous filenames.
    ollama_model: str = "llama3.2:3b"
    use_ai_fallback: bool = False
    use_outlook: bool = False
    extra: dict = field(default_factory=dict)

    def save(self) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls) -> "Config":
        if CONFIG_PATH.exists():
            return cls(**json.loads(CONFIG_PATH.read_text()))
        return cls()
