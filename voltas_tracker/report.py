"""Terminal + CSV report of per-project stage results."""

from __future__ import annotations

import csv
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .matcher import StageResult, Status

STATUS_STYLE = {
    Status.DONE: "green",
    Status.EVIDENCE_FOUND: "cyan",
    Status.PENDING: "red",
    Status.AMBIGUOUS: "yellow",
}


def print_report(results: list[StageResult]) -> None:
    console = Console()
    by_project: dict[str, list[StageResult]] = {}
    for r in results:
        by_project.setdefault(r.project.label, []).append(r)

    for label, stages in by_project.items():
        chk = stages[0].project
        subtitle = " · ".join(p for p in (chk.address, chk.client_name) if p)
        table = Table(title=f"{label}" + (f"  ({subtitle})" if subtitle else ""))
        table.add_column("#", justify="right")
        table.add_column("Activity")
        table.add_column("Date")
        table.add_column("By")
        table.add_column("Status")
        table.add_column("Evidence on P:")
        for r in stages:
            style = STATUS_STYLE[r.status]
            table.add_row(
                str(r.stage.number),
                r.stage.activity,
                r.stage.done_on.isoformat() if r.stage.done_on else "—",
                r.stage.by or "—",
                f"[{style}]{r.status.value}[/{style}]",
                r.file.name if r.file else "—",
            )
        console.print(table)

    counts = {s: sum(1 for r in results if r.status is s) for s in Status}
    console.print(
        f"\n[green]{counts[Status.DONE]} done[/green] · "
        f"[cyan]{counts[Status.EVIDENCE_FOUND]} evidence found (sheet behind)[/cyan] · "
        f"[red]{counts[Status.PENDING]} pending[/red] · "
        f"[yellow]{counts[Status.AMBIGUOUS]} need review[/yellow]"
    )


def export_csv(results: list[StageResult], path: str | Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            ["project", "stage_no", "activity", "date", "by", "status", "evidence_file", "score"]
        )
        for r in results:
            w.writerow(
                [
                    r.project.label,
                    r.stage.number,
                    r.stage.activity,
                    r.stage.done_on.isoformat() if r.stage.done_on else "",
                    r.stage.by,
                    r.status.value,
                    r.file.path if r.file else "",
                    f"{r.score:.0f}" if r.score else "",
                ]
            )
