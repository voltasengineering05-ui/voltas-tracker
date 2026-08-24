"""Read the Excel tracker: one ExpectedDocument per row.

The real column mapping is configured during `voltas-tracker setup` once we
have the actual sheet; this module only defines the shape the rest of the
agent works with.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from openpyxl import load_workbook


@dataclass
class ExpectedDocument:
    project: str
    name: str
    due: date | None = None
    row: int = 0
    notes: str = ""


def read_tracker(path: str | Path) -> list[ExpectedDocument]:
    """Parse the tracker workbook into a list of expected documents.

    Placeholder mapping: assumes columns A=project, B=document name, C=due
    date. Replaced with the real mapping once the actual sheet is provided.
    """
    wb = load_workbook(filename=str(path), read_only=True, data_only=True)
    ws = wb.active
    docs: list[ExpectedDocument] = []
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not row or not row[0]:
            continue
        due = row[2] if len(row) > 2 else None
        docs.append(
            ExpectedDocument(
                project=str(row[0]).strip(),
                name=str(row[1]).strip() if len(row) > 1 and row[1] else "",
                due=due.date() if hasattr(due, "date") else due,
                row=i,
            )
        )
    return docs
