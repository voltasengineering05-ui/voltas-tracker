# voltas-tracker

AI document-tracking agent for Voltas Engineering.

It reads each project's **Project Design Delivery Checklist** workbook (the
21-stage sheet: Intake → Quote Sent → … → Inspections → Sch CB), scans the
P: drive, and reports where every project actually stands: which stages are
**done** (dated in the sheet), which have **evidence found** on the drive but
no date yet (the sheet is behind reality), and which are truly **pending**.
Outlook (via Microsoft Graph) can optionally catch documents that arrived by
email but were never filed.

Everything runs locally on the office Windows PC. **Read-only by design**: it
never moves, renames, or deletes files, and never sends email without approval.

## How it works

1. **Checklist reader** — parses one workbook per project: the header block
   (project number, address, client) plus the numbered stage table with its
   Date and By columns (`excel_reader.py`).
2. **P: drive scan** — walks the folder tree (quotations, project-year
   folders, inspections) and matches filenames to stages using the drive's
   naming conventions: discipline codes (AR, EL, ME, PL, SP, BE, PM, DC) and
   city codes (SRY, BBY, VAN, LGY, CGY)
   (`pdrive_scanner.py`, `matcher.py`, `conventions.py`).
3. **Outlook check** — looks for documents that arrived by email but were
   never filed (`outlook_graph.py`, optional).
4. **AI fallback** — only when a filename is too messy for fuzzy matching, a
   small local model via Ollama is asked to classify it (`ai_fallback.py`,
   optional). No cloud, no training required.
5. **Learning loop** — every correction a reviewer makes ("no, that file
   belongs to project X") is saved and applied on future runs
   (`feedback.py`). This is the guided AI session: the agent gets more
   accurate the more it's corrected, with zero GPU training.
6. **Report** — a colour terminal report plus a CSV/Excel export
   (`report.py`).

## Install (on the office Windows PC)

```bash
pip3 install git+https://github.com/kirpajeet12/voltas-tracker.git
```

Or clone and install locally:

```bash
git clone https://github.com/kirpajeet12/voltas-tracker.git
cd voltas-tracker
pip3 install -e .
```

## Usage

```bash
# one-time interactive setup: where is the tracker, where is the P: drive
voltas-tracker setup

# scan and report (read-only)
voltas-tracker run

# review the agent's uncertain matches and teach it
voltas-tracker review
```

## Status

Early scaffold. The matcher is built against sample data first; it is only
pointed at the real P: drive and Outlook after accuracy is proven on copies.

## Development

```bash
pip3 install -e ".[outlook,ai]"
python3 -m voltas_tracker.cli --help
```
