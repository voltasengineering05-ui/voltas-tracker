"""End-to-end tests against a fixture that mirrors the real checklist.

The workbook layout copies "Copy of Project Design Delivery Checklist.xlsx"
(header block, Sl. No. / Activity / Date / By table, footer path note); the
fake P: drive tree uses the folder roots and naming conventions from the
Company RAG Implementation Plan.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from openpyxl import Workbook

from voltas_tracker.excel_reader import load_checklists, read_checklist
from voltas_tracker.feedback import FeedbackStore
from voltas_tracker.matcher import Status, match_project, project_files
from voltas_tracker.pdrive_scanner import scan

ACTIVITIES = [
    "Intake (Call / Email) ",
    "Quote Sent ",
    "Quote Approved",
    "Files / Docs / City Email (All) Received",
    "Project Assigned ",
    "Calculations ",
    "Design ",
    "Drafting ",
    "Review by Sr. Engineer",
    "Issued for Coord",
    "Revisions (if any) ",
    "Issued Stamped & Signed ",
    "City Comments ",
    "Revision ",
    "Review by Sr. Engineer",
    "Issued for Coordination ",
    "Issued Stamped & Signed ",
    "Inspection 1",
    "Inspection 2",
    "Inspection 3",
    "Sch CB ",
]


def make_checklist(path: Path, project="26-4021", address="12345 88 Ave SRY",
                   dates: dict[int, date] | None = None) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Discipline"
    ws.append(["Voltas Engineering Ltd. "])
    ws.append(["Project Design Delivery Check List "])
    ws.append([])
    ws.append(["Project Number:", project])
    ws.append(["Project Address:", address])
    ws.append(["Client Name:", "Pizza 64 Holdings"])
    ws.append(["Client Number: ", "604-555-0199"])
    ws.append(["Clients Email: ", "owner@example.com"])
    ws.append([])
    ws.append(["Sl. No. ", "Activity ", "", "Date ", "By "])
    for i, activity in enumerate(ACTIVITIES, start=1):
        done = (dates or {}).get(i)
        ws.append([str(i), activity, "", done, "KG" if done else ""])
    ws.append([])
    ws.append(["P:\\04 Voltas Templates and Schedules\\Templates"])
    wb.save(path)
    return path


@pytest.fixture
def pdrive(tmp_path: Path) -> Path:
    root = tmp_path / "P"
    files = [
        "02 Quotations/2026/26-4021 - 12345 88 Ave SRY - Quotation.pdf",
        "2026 Projects/26-4021 - 12345 88 Ave SRY - EL/26-4021 Issued Stamped and Signed EL.pdf",
        "2026 Projects/26-4021 - 12345 88 Ave SRY - EL/26-4021 City Comments Response.pdf",
        "09 Inspections/26-4021 Inspection 1 Field Review.pdf",
        "2026 Projects/26-9999 - 5500 Kingsway BBY - ME/26-9999 Quotation.pdf",
        "2026 Projects/26-4021 - 12345 88 Ave SRY - EL/photo.jpg",
        "2026 Projects/26-4021 - 12345 88 Ave SRY - EL/~$temp.docx",
    ]
    for rel in files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")
    return root


def test_reads_real_layout(tmp_path):
    chk = read_checklist(make_checklist(tmp_path / "chk.xlsx", dates={1: date(2026, 8, 1)}))
    assert chk.project_number == "26-4021"
    assert chk.address == "12345 88 Ave SRY"
    assert chk.client_name == "Pizza 64 Holdings"
    assert len(chk.stages) == 21
    assert chk.stages[0].done_on == date(2026, 8, 1)
    assert chk.stages[0].by == "KG"
    assert chk.stages[20].activity.strip() == "Sch CB"


def test_load_folder_skips_lockfiles(tmp_path):
    make_checklist(tmp_path / "a.xlsx")
    make_checklist(tmp_path / "b.xlsx", project="26-9999")
    (tmp_path / "~$a.xlsx").write_text("lock")
    assert len(load_checklists(tmp_path)) == 2


def test_scan_excludes_noise(pdrive):
    names = {f.name for f in scan(pdrive)}
    assert "photo.jpg" not in names
    assert "~$temp.docx" not in names
    assert "26-4021 Inspection 1 Field Review.pdf" in names


def test_project_scoping(pdrive, tmp_path):
    chk = read_checklist(make_checklist(tmp_path / "chk.xlsx"))
    pool = project_files(chk, scan(pdrive))
    assert all("26-4021" in f.path for f in pool)
    assert not any("26-9999" in f.path for f in pool)


def test_stage_matching(pdrive, tmp_path):
    chk = read_checklist(
        make_checklist(tmp_path / "chk.xlsx", dates={1: date(2026, 8, 1), 2: date(2026, 8, 2)})
    )
    results = match_project(chk, scan(pdrive), FeedbackStore(tmp_path / "fb.json"))
    by_stage = {r.stage.number: r for r in results}

    assert by_stage[1].status is Status.DONE
    assert by_stage[2].status is Status.DONE
    # Stamped & Signed has evidence on the drive even though the sheet is blank.
    assert by_stage[12].status is Status.EVIDENCE_FOUND
    assert "Stamped" in by_stage[12].file.name
    assert by_stage[13].status is Status.EVIDENCE_FOUND
    # Inspection 1 exists; Inspections 2 and 3 do not.
    assert by_stage[18].status is Status.EVIDENCE_FOUND
    assert by_stage[19].status is not Status.EVIDENCE_FOUND
    assert by_stage[20].status is not Status.EVIDENCE_FOUND
    # Workflow-only stages with no date stay pending.
    assert by_stage[5].status is Status.PENDING


def test_feedback_pins_a_file(pdrive, tmp_path):
    chk = read_checklist(make_checklist(tmp_path / "chk.xlsx"))
    files = scan(pdrive)
    store = FeedbackStore(tmp_path / "fb.json")
    target = next(f for f in files if "City Comments" in f.name)
    store.record(chk.label, "City Comments", target.path)

    results = match_project(chk, files, store)
    r = next(r for r in results if "City Comments" in r.stage.activity)
    assert r.status is Status.EVIDENCE_FOUND and r.score == 100.0
