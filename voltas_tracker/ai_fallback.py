"""Local-AI fallback for messy filenames (optional, off by default).

Only consulted for AMBIGUOUS matches the fuzzy matcher couldn't settle.
Uses a small local model through Ollama (e.g. llama3.2:3b, or a small
Nemotron variant if the PC's GPU allows) — fully offline, no client data
leaves the machine, no training required.

Requires the `ai` extra: pip3 install "voltas-tracker[ai]"
"""

from __future__ import annotations

from .excel_reader import ExpectedDocument
from .pdrive_scanner import ScannedFile


def classify(
    doc: ExpectedDocument,
    candidates: list[ScannedFile],
    model: str = "llama3.2:3b",
) -> str | None:
    """Ask the local model which candidate file (if any) is `doc`.

    Returns the chosen file path, or None if the model is unsure — unsure
    answers stay in the human review queue rather than being guessed.
    """
    try:
        import ollama
    except ImportError:
        return None

    prompt = (
        "You match engineering project documents to files.\n"
        f"Expected document: {doc.name!r} for project {doc.project!r}.\n"
        "Candidate files:\n"
        + "\n".join(f"{i}: {c.name} (in {c.folder})" for i, c in enumerate(candidates))
        + "\nReply with ONLY the number of the matching file, or NONE."
    )
    reply = ollama.generate(model=model, prompt=prompt)["response"].strip()
    if reply.isdigit() and int(reply) < len(candidates):
        return candidates[int(reply)].path
    return None
