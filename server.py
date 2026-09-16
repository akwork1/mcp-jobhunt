"""MCP server over a job-application tracker.

Exposes the application history kept in a markdown TRACKER.md as tools that
any MCP client (Claude Code, Claude Desktop, the MCP Inspector) can discover
and call, instead of the model re-reading a 40,000-token file every session.

Data file: set JOBHUNT_TRACKER to the path of your real tracker. If unset,
the sample data in examples/tracker.sample.md is used so the repo runs
without private data. The real tracker is never committed.

Run:  uv run server.py            (stdio transport, for Claude Code / Inspector)
Test: uv run pytest
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

DEFAULT_TRACKER = Path(__file__).parent / "examples" / "tracker.sample.md"
TRACKER_PATH = Path(os.environ.get("JOBHUNT_TRACKER", DEFAULT_TRACKER))

# Columns returned by list_applications. Enough to pick a row, not the notes.
SUMMARY_COLUMNS = ("Date", "Company", "Role", "Location", "Status")

mcp = MCPServer(
    name="jobhunt",
    instructions=(
        "Application history for one person's job search. Call "
        "list_applications to find rows by status or location, then "
        "get_application for a single row's full notes."
    ),
)


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

# A pipe that is NOT preceded by a backslash. Markdown lets a cell contain a
# literal pipe as `\|`, and the tracker's notes cells do this.
_UNESCAPED_PIPE = re.compile(r"(?<!\\)\|")


def _split_row(line: str) -> list[str]:
    """Split one `| a | b | c |` table line into stripped cell strings."""
    inner = line.strip()[1:-1]  # drop the leading and trailing pipe
    return [cell.replace(r"\|", "|").strip() for cell in _UNESCAPED_PIPE.split(inner)]


def parse_tracker(text: str) -> list[dict[str, str]]:
    """Parse the first application table in a tracker file into row dicts.

    Keys are the header cells ("Date", "Company", ...). Everything outside
    the table is ignored: prose, headings, the |---| separator, and any
    later table (the tracker has a second, usually empty, pipeline table).
    Markdown inside cells (bold, backticks) is left as text.
    """
    header: list[str] | None = None
    rows: list[dict[str, str]] = []

    for raw in text.splitlines():
        line = raw.strip()
        if header is None:
            if line.startswith("| Date"):
                header = _split_row(line)
            continue
        if not line.startswith("|"):
            break  # first non-table line after the header ends the table
        cells = _split_row(line)
        if cells and cells[0].startswith("-"):
            continue  # the |---|---| separator
        if len(cells) != len(header):
            continue  # malformed row; skip rather than misalign columns
        rows.append(dict(zip(header, cells)))

    return rows


def _load_rows() -> list[dict[str, str]]:
    """Read the tracker fresh on every call so edits show up without a restart."""
    try:
        return parse_tracker(TRACKER_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ToolError(f"Tracker file not found: {TRACKER_PATH}") from None


# --------------------------------------------------------------------------
# Tools
# --------------------------------------------------------------------------


@mcp.tool()
def list_applications(status: str | None = None, location: str | None = None) -> list[dict[str, str]]:
    """Find job applications in the tracker, optionally filtered.

    Use this first to see what has been applied for, then get_application
    for one row's detail. Returns a compact summary per row (date, company,
    role, location, status) without the long notes field.

    status: exact match, case-insensitive. One of drafted, applied,
        acknowledged, interview, offer, rejected, no reply, withdrawn.
    location: case-insensitive substring, e.g. "perth" matches "Perth WA".
    """
    out = []
    for row in _load_rows():
        if status and row["Status"].lower() != status.lower():
            continue
        if location and location.lower() not in row["Location"].lower():
            continue
        out.append({col: row[col] for col in SUMMARY_COLUMNS})
    return out


@mcp.tool()
def get_application(company: str) -> dict[str, str]:
    """Get the full tracker row for one company, including the notes.

    The notes hold the reasoning behind the application: which through-line
    the letter used, gaps named, salary answered, what to do before sending.
    Use this when you need that detail for a specific application.

    company: case-insensitive substring of the company name; the first
        match is returned. Raises an error if nothing matches.
    """
    needle = company.lower()
    for row in _load_rows():
        if needle in row["Company"].lower():
            return row
    raise ToolError(f"No application found for company matching {company!r}")


if __name__ == "__main__":
    mcp.run(transport="stdio")
