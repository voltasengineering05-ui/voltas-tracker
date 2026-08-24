"""Command-line entry point: voltas-tracker {setup,run,review}."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.prompt import IntPrompt, Prompt

from .config import Config
from .excel_reader import load_checklists
from .feedback import FeedbackStore
from .matcher import Status, match_project
from .pdrive_scanner import scan
from .report import export_csv, print_report

app = typer.Typer(help="Voltas document-tracking agent (read-only).")
console = Console()


@app.command()
def setup() -> None:
    """One-time setup: where the checklists and the P: drive live."""
    cfg = Config.load()
    cfg.excel_path = Prompt.ask(
        "Path to a Project Design Delivery Checklist (or a folder of them)",
        default=cfg.excel_path or None,
    )
    cfg.pdrive_root = Prompt.ask("Path to the P: drive root", default=cfg.pdrive_root or None)
    cfg.save()
    console.print("[green]Saved.[/green] Run [bold]voltas-tracker run[/bold] to scan.")


def _load_all(cfg: Config):
    checklists = load_checklists(cfg.excel_path)
    console.print(f"Loaded {len(checklists)} checklist(s) from {cfg.excel_path}")
    console.print(f"Scanning (read-only): {cfg.pdrive_root}")
    files = scan(cfg.pdrive_root)
    console.print(f"{len(files)} document files found\n")
    return checklists, files


@app.command()
def run(csv: str = typer.Option("", help="Also export the report to this CSV path.")) -> None:
    """Check every project's stages against the P: drive and report."""
    cfg = Config.load()
    if not cfg.excel_path or not cfg.pdrive_root:
        console.print("[red]Not configured yet — run [bold]voltas-tracker setup[/bold] first.[/red]")
        raise typer.Exit(1)

    checklists, files = _load_all(cfg)
    feedback = FeedbackStore()
    results = []
    for chk in checklists:
        results.extend(match_project(chk, files, feedback, cfg.review_threshold))

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

    checklists, files = _load_all(cfg)
    feedback = FeedbackStore()
    results = []
    for chk in checklists:
        results.extend(match_project(chk, files, feedback, cfg.review_threshold))

    ambiguous = [r for r in results if r.status is Status.AMBIGUOUS and r.candidates]
    if not ambiguous:
        console.print("[green]Nothing to review — no ambiguous matches.[/green]")
        return

    for r in ambiguous:
        console.print(f"\n[bold]{r.project.label}[/bold] — {r.stage.activity}")
        for i, (f, score) in enumerate(r.candidates):
            console.print(f"  {i}: {f.name}  ({f.folder}, score {score:.0f})")
        choice = IntPrompt.ask("Which file proves this stage? (-1 = none of these)", default=-1)
        if 0 <= choice < len(r.candidates):
            feedback.record(r.project.label, r.stage.activity, r.candidates[choice][0].path)
            console.print("[green]Saved — the agent will remember this.[/green]")


if __name__ == "__main__":
    app()
