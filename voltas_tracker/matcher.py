"""Match checklist stages against files scanned from the P: drive.

For each project the candidate pool is first narrowed to files whose path
mentions that project (project number, or a fuzzy hit on the address). Then
every evidence-bearing stage is scored against the pool: saved corrections
from the feedback store win outright, otherwise rapidfuzz keyword scoring
with folder-location boosts decides. Low-confidence hits are flagged
AMBIGUOUS for human review instead of being silently guessed.

Stage statuses:
- DONE            the sheet has a date for the stage
- EVIDENCE_FOUND  no date in the sheet, but a matching file exists on the
                  drive (the sheet is behind reality)
- PENDING         no date and no evidence
- AMBIGUOUS       no date; candidate files exist but none scored above the
                  review threshold
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from rapidfuzz import fuzz

from .conventions import StageSpec, spec_for
from .excel_reader import ProjectChecklist, Stage
from .feedback import FeedbackStore
from .pdrive_scanner import ScannedFile


class Status(str, Enum):
    DONE = "done"
    EVIDENCE_FOUND = "evidence found"
    PENDING = "pending"
    AMBIGUOUS = "ambiguous"


@dataclass
class StageResult:
    project: ProjectChecklist
    stage: Stage
    spec: StageSpec | None
    status: Status
    file: ScannedFile | None = None
    score: float = 0.0
    candidates: list[tuple[ScannedFile, float]] = field(default_factory=list)


def project_files(chk: ProjectChecklist, files: list[ScannedFile]) -> list[ScannedFile]:
    """Narrow the scan to files that belong to this project."""
    number = chk.project_number.lower()
    address = " ".join(chk.address.lower().split())
    if not number and not address:
        return files
    scoped = []
    for f in files:
        path = f.path.lower()
        if number and number in path:
            scoped.append(f)
        elif address and fuzz.partial_ratio(address, path) >= 85:
            scoped.append(f)
    return scoped


def _score(stage: Stage, spec: StageSpec, f: ScannedFile) -> float:
    name = f.name.lower()
    path = f.path.lower()
    score = max(fuzz.partial_ratio(kw, name) for kw in spec.keywords)
    if any(hint in path for hint in spec.folder_hints):
        score += 10
    # "Inspection 2" must match a file mentioning the same ordinal: without
    # it the score is capped below the review threshold so the match lands
    # in the human review queue instead of being claimed as evidence.
    ordinal = re.search(r"\b(\d)\b", stage.activity)
    if ordinal:
        if re.search(rf"\b{ordinal.group(1)}\b", name):
            score += 10
        else:
            score = min(score, 70.0)
    return min(100.0, score)


def match_project(
    chk: ProjectChecklist,
    files: list[ScannedFile],
    feedback: FeedbackStore,
    review_threshold: int = 75,
) -> list[StageResult]:
    pool = project_files(chk, files)
    results: list[StageResult] = []
    for stage in chk.stages:
        spec = spec_for(stage.activity)

        if stage.done_on:
            results.append(StageResult(chk, stage, spec, Status.DONE))
            continue
        if spec is None or not spec.keywords:
            results.append(StageResult(chk, stage, spec, Status.PENDING))
            continue

        # 1. A saved human correction always wins.
        pinned = feedback.lookup(chk.label, stage.activity)
        if pinned:
            hit = next((f for f in pool if f.path == pinned), None)
            if hit:
                results.append(
                    StageResult(chk, stage, spec, Status.EVIDENCE_FOUND, hit, 100.0)
                )
                continue

        # 2. Keyword scoring over the project-scoped pool.
        scored = sorted(
            ((f, _score(stage, spec, f)) for f in pool),
            key=lambda t: t[1],
            reverse=True,
        )
        scored = [(f, s) for f, s in scored if s >= 50]

        if not scored:
            results.append(StageResult(chk, stage, spec, Status.PENDING))
        elif scored[0][1] >= review_threshold:
            results.append(
                StageResult(
                    chk, stage, spec, Status.EVIDENCE_FOUND,
                    scored[0][0], scored[0][1], scored[:5],
                )
            )
        else:
            results.append(
                StageResult(
                    chk, stage, spec, Status.AMBIGUOUS,
                    None, scored[0][1], scored[:5],
                )
            )
    return results
