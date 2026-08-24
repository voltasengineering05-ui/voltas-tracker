"""Command-line entry point: voltas-tracker {setup,run,review}."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.prompt import IntPrompt, Prompt

from .config import Config
from .excel_reader import read_tracker
from .feedback import FeedbackStore
from .matcher import Status, match
from .pdrive_scanner import scan
from .report import export_csv, print_report

app = typer.Typer(help="Voltas document-tracking agent (read-only).")
console = Console()


@app.command()
def setup() -> None:
    """One-time setup: where the Excel tracker and P: drive live."""
    cfg = Config.load()
    cfg.excel_path = Prompt.ask("Path to the Excel tracker", default=cfg.excel_path or None)
    cfg.pdrive_root = Prompt.ask("Path to the P: drive root", default=cfg.pdrive_root or None)
    cfg.save()
    console.print("[green]Saved.[/green] Run [bold]voltas-tracker run[/bold] to scan.")


@app.command()
def run(csv: str = typer.Option("", help="Also export the report to this CSV path.")) -> None:
    """Scan the P: drive against the tracker and print the report."""
    cfg = Config.load()
    if not cfg.excel_path or not cfg.pdrive_root:
        console.print("[red]Not configured yet — run [bold]voltas-tracker setup[/bold] first.[/red]")
        raise typer.Exit(1)

    console.print(f"Reading tracker: {cfg.excel_path}")
    expected = read_tracker(cfg.excel_path)
    console.print(f"Scanning (read-only): {cfg.pdrive_root}")
    files = scan(cfg.pdrive_root)
    console.print(f"{len(expected)} expected documents · {len(files)} files found\n")

    results = match(expected, files, FeedbackStore(), cfg.review_threshold)
    print_report(results)
    if csv:
        export_csv(results, csv)
        console.print(f"Exported: {csv}")


@app.command()
def review() -> None:
    """The guided AI session: confirm or correct ambiguous matches."""
    cfg = Config.load()
    if not cfg.excel_path or not cfg.pdrive_root:
        console.print("[red]Not configured yet — run [bold]voltas-tracker setup[/bold] first.[/red]")
        raise typer.Exit(1)

    feedback = FeedbackStore()
    expected = read_tracker(cfg.excel_path)
    files = scan(cfg.pdrive_root)
    results = match(expected, files, feedback, cfg.review_threshold)

    ambiguous = [r for r in results if r.status is Status.AMBIGUOUS and r.candidates]
    if not ambiguous:
        console.print("[green]Nothing to review — no ambiguous matches.[/green]")
        return

    for r in ambiguous:
        console.print(f"\n[bold]{r.expected.project}[/bold] — {r.expected.name}")
        for i, (f, score) in enumerate(r.candidates):
            console.print(f"  {i}: {f.name}  ({f.folder}, score {score:.0f})")
        choice = IntPrompt.ask("Which file is it? (-1 = none of these)", default=-1)
        if 0 <= choice < len(r.candidates):
            feedback.record(r.expected, r.candidates[choice][0].path)
            console.print("[green]Saved — the agent will remember this.[/green]")


if __name__ == "__main__":
    app()
