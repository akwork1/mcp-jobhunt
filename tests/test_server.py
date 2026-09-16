"""Tests for server.py. All of these fail until the three functions are written.

Run: uv run pytest -q
Work through them top to bottom; each one is one thing to get right.
"""

from pathlib import Path

import pytest

import server

SAMPLE = (Path(__file__).parent.parent / "examples" / "tracker.sample.md").read_text()


@pytest.fixture
def rows():
    return server.parse_tracker(SAMPLE)


# ---- parse_tracker -------------------------------------------------------


def test_parses_every_data_row(rows):
    assert len(rows) == 6


def test_keys_come_from_header(rows):
    assert set(rows[0]) == {
        "Date", "Company", "Role", "Location", "Source", "Through-line used",
        "Letter file", "Status", "Last update", "Notes",
    }


def test_cells_are_stripped(rows):
    assert rows[0]["Company"] == "Harbourline Systems"
    assert rows[0]["Status"] == "interview"


def test_separator_line_is_not_a_row(rows):
    assert all(not r["Date"].startswith("-") for r in rows)


def test_escaped_pipe_inside_a_cell_does_not_split_it(rows):
    quill = next(r for r in rows if r["Company"] == "Quillfeather Media")
    assert "no band published" in quill["Notes"]
    assert quill["Status"] == "applied"


def test_markdown_inside_cells_is_left_alone(rows):
    harbour = next(r for r in rows if r["Company"] == "Harbourline Systems")
    assert "**MCP**" in harbour["Notes"]


# ---- list_applications ---------------------------------------------------


def test_list_all_returns_compact_rows():
    out = server.list_applications()
    assert len(out) == 6
    # compact: enough to pick a row, not the whole notes field
    assert "Notes" not in out[0]
    assert {"Company", "Role", "Status"} <= set(out[0])


def test_list_filters_by_status():
    out = server.list_applications(status="applied")
    assert {r["Company"] for r in out} == {"Quillfeather Media", "Bramble & Vane", "Corvid Labs"}


def test_list_filters_by_location_substring_case_insensitive():
    out = server.list_applications(location="perth")
    assert {r["Company"] for r in out} == {"Harbourline Systems", "Bramble & Vane", "Corvid Labs"}


def test_list_filters_combine():
    out = server.list_applications(status="applied", location="Perth")
    assert {r["Company"] for r in out} == {"Bramble & Vane", "Corvid Labs"}


# ---- get_application -----------------------------------------------------


def test_get_returns_full_row_including_notes():
    row = server.get_application("Corvid Labs")
    assert row["Status"] == "applied"
    assert "public repo" in row["Notes"]


def test_get_is_case_insensitive_and_partial():
    assert server.get_application("corvid")["Company"] == "Corvid Labs"


def test_get_unknown_company_raises_a_useful_error():
    with pytest.raises(Exception, match="No application"):
        server.get_application("Nonexistent Pty Ltd")


# ---- the server itself ---------------------------------------------------


@pytest.mark.anyio
async def test_tools_are_registered_with_real_docstrings():
    tools = await server.mcp.list_tools()
    names = {t.name for t in tools}
    assert names == {"list_applications", "get_application"}
    for t in tools:
        assert t.description and "TODO" not in t.description, f"{t.name} still has the placeholder docstring"
