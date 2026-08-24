"""Voltas P: drive naming conventions and stage → evidence rules.

Folder roots, discipline codes, and city codes come from the Company RAG
Implementation Plan (April 2026), which documented the drive's approved v1
layout. Stage specs map each activity on the Project Design Delivery
Checklist to the kind of file that proves it happened, and where on the
drive that file usually lives. Stages with no keywords are workflow-only:
they are tracked purely from the Date column in the sheet.
"""

from __future__ import annotations

from dataclasses import dataclass

DISCIPLINE_CODES = ("AR", "EL", "ME", "PL", "SP", "BE", "PM", "DC")

CITY_CODES = {
    "SRY": "Surrey",
    "BBY": "Burnaby",
    "VAN": "Vancouver",
    "LGY": "Langley",
    "CGY": "Calgary",
}

# Approved v1 folder roots (relative to the P: drive root).
FOLDER_QUOTATIONS = "02 quotations"
FOLDER_TEMPLATES = "04 voltas templates and schedules"
FOLDER_INSPECTIONS = "09 inspections"


@dataclass(frozen=True)
class StageSpec:
    key: str
    # Lowercase substrings that identify this stage's row in the sheet.
    activity_patterns: tuple[str, ...]
    # Filename keywords that count as evidence; empty = workflow-only stage.
    keywords: tuple[str, ...] = ()
    # Path fragments that boost a candidate when present.
    folder_hints: tuple[str, ...] = ()


STAGE_SPECS: tuple[StageSpec, ...] = (
    StageSpec("intake", ("intake",)),
    StageSpec(
        "quote_sent",
        ("quote sent",),
        keywords=("quote", "quotation", "proposal", "fee letter"),
        folder_hints=(FOLDER_QUOTATIONS,),
    ),
    StageSpec(
        "quote_approved",
        ("quote approved",),
        keywords=("quote approved", "signed quote", "quote acceptance", "purchase order"),
        folder_hints=(FOLDER_QUOTATIONS,),
    ),
    StageSpec("docs_received", ("files / docs", "files/docs", "city email")),
    StageSpec("project_assigned", ("project assigned",)),
    StageSpec("calculations", ("calculation",)),
    StageSpec("design", ("design",)),
    StageSpec("drafting", ("drafting",)),
    StageSpec("senior_review", ("review by sr",)),
    StageSpec(
        "issued_for_coordination",
        ("issued for coord",),
        keywords=("issued for coordination", "issued for coord", "ifc", "coordination set"),
    ),
    StageSpec("revisions", ("revision",)),
    StageSpec(
        "issued_stamped",
        ("issued stamped",),
        keywords=("stamped", "signed", "sealed", "stamped and signed", "issued stamped"),
    ),
    StageSpec(
        "city_comments",
        ("city comments",),
        keywords=("city comments", "plan check", "comments response", "correction"),
    ),
    StageSpec(
        "inspection",
        ("inspection",),
        keywords=("inspection", "field review", "site review", "site visit"),
        folder_hints=(FOLDER_INSPECTIONS,),
    ),
    StageSpec(
        "sch_cb",
        ("sch cb", "schedule cb", "schedule c-b"),
        keywords=("schedule cb", "sch cb", "schedule c-b", "cb"),
        folder_hints=(FOLDER_INSPECTIONS,),
    ),
)


def spec_for(activity: str) -> StageSpec | None:
    """Find the spec whose patterns appear in the sheet's activity text."""
    text = " ".join(activity.lower().split())
    for spec in STAGE_SPECS:
        if any(pattern in text for pattern in spec.activity_patterns):
            return spec
    return None
