"""Terminal + CSV report of match results."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .matcher import MatchResult, Status

STATUS_STYLE = {
    Status.RECEIVED: "green",
    Status.MISSING: "red",
    Status.AMBIGUOUS: "yellow",
}


def is_overdue(r: MatchResult, today: date | None = None) -> bool:
    today = today or date.today()
    return r.status is Status.MISSING and r.expected.due is not None and r.expected.due < today


def print_report(results: list[MatchResult]) -> None:
    console = Console()
    table = Table(title="Voltas document tracker")
    table.add_column("Project")
    table.add_column("Document")
    table.add_column("Status")
    table.add_column("Matched file")
    table.add_column("Score", justify="right")

    for r in results:
        status = "OVERDUE" if is_overdue(r) else r.status.value
        style = "bold red" if status == "OVERDUE" else STATUS_STYLE[r.status]
        table.add_row(
            r.expected.project,
            r.expected.name,
            f"[{style}]{status}[/{style}]",
            r.file.name if r.file else "—",
            f"{r.score:.0f}" if r.score else "—",
        )
    console.print(table)

    counts = {s: sum(1 for r in results if r.status is s) for s in Status}
    overdue = sum(1 for r in results if is_overdue(r))
    console.print(
        f"\n[green]{counts[Status.RECEIVED]} received[/green] · "
        f"[red]{counts[Status.MISSING]} missing ({overdue} overdue)[/red] · "
        f"[yellow]{counts[Status.AMBIGUOUS]} need review[/yellow]"
    )


def export_csv(results: list[MatchResult], path: str | Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["project", "document", "status", "overdue", "matched_file", "score"])
        for r in results:
            w.writerow(
                [
                    r.expected.project,
                    r.expected.name,
                    r.status.value,
                    is_overdue(r),
                    r.file.path if r.file else "",
                    f"{r.score:.0f}",
                ]
            )
