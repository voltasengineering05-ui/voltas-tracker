"""Match expected documents (from the Excel tracker) against scanned files.

Deterministic first: saved corrections from the feedback store always win.
Then fuzzy matching via rapidfuzz. Anything scoring below the review
threshold is flagged as AMBIGUOUS for human review (or the optional local-AI
fallback) instead of being silently guessed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from rapidfuzz import fuzz

from .excel_reader import ExpectedDocument
from .feedback import FeedbackStore
from .pdrive_scanner import ScannedFile


class Status(str, Enum):
    RECEIVED = "received"
    MISSING = "missing"
    AMBIGUOUS = "ambiguous"


@dataclass
class MatchResult:
    expected: ExpectedDocument
    status: Status
    file: ScannedFile | None = None
    score: float = 0.0
    candidates: list[tuple[ScannedFile, float]] = field(default_factory=list)


def match(
    expected: list[ExpectedDocument],
    files: list[ScannedFile],
    feedback: FeedbackStore,
    review_threshold: int = 80,
) -> list[MatchResult]:
    results: list[MatchResult] = []
    for doc in expected:
        # 1. A saved human correction always wins.
        pinned = feedback.lookup(doc)
        if pinned:
            hit = next((f for f in files if f.path == pinned), None)
            if hit:
                results.append(MatchResult(doc, Status.RECEIVED, hit, 100.0))
                continue

        # 2. Fuzzy match on filename, boosted when the project name appears
        #    in the folder path.
        scored: list[tuple[ScannedFile, float]] = []
        for f in files:
            score = fuzz.token_set_ratio(doc.name.lower(), f.name.lower())
            if doc.project and doc.project.lower() in f.folder.lower():
                score = min(100.0, score + 10)
            if score >= 50:
                scored.append((f, score))
        scored.sort(key=lambda t: t[1], reverse=True)

        if not scored:
            results.append(MatchResult(doc, Status.MISSING))
        elif scored[0][1] >= review_threshold:
            results.append(
                MatchResult(doc, Status.RECEIVED, scored[0][0], scored[0][1], scored[:5])
            )
        else:
            results.append(
                MatchResult(doc, Status.AMBIGUOUS, None, scored[0][1], scored[:5])
            )
    return results
