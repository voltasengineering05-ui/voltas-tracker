"""Outlook via Microsoft Graph (optional, off by default).

Finds documents that arrived by email but were never filed on the P: drive.
Read-only: it searches messages and lists attachments; it never sends,
moves, or deletes mail. Wired up after the matcher is proven on local files.

Requires the `outlook` extra: pip3 install "voltas-tracker[outlook]"
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EmailAttachment:
    subject: str
    sender: str
    received: str
    filename: str
    message_id: str


def search_attachments(query: str) -> list[EmailAttachment]:
    """Search the mailbox for attachments matching `query`.

    Not implemented yet — needs an Azure app registration (device-code flow)
    for the Voltas Microsoft 365 tenant. Deliberately a stub until the
    read-only P: drive matcher is accurate.
    """
    raise NotImplementedError(
        "Outlook integration is scheduled after the P: drive matcher is proven. "
        "Run with use_outlook=false for now."
    )
