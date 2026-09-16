# How this repo is built

This project is built by directing Claude Code, not by hand-typing it. That is
deliberate and it is the skill on show. Read this before doing anything.

## Division of labour

**Atticus owns:** what gets built and why, the order, the scope of each slice,
reading every change before it is committed, running it himself, and deciding
when a slice is done. He is expected to be able to explain any line in this
repo in an interview without notes.

**Claude owns:** the typing. Implementation, tests, docs, dependency wrangling,
reading the primary documentation and reporting back what matters.

## The verification rule

Claude never marks its own work done. Every slice ends with a review in which
Claude asks Atticus questions about the code it wrote, and Atticus answers
without looking. If he cannot answer, the slice is not done; he reads that part
until he can. "Looks right" is not a review. The question being screened for in
every AI engineering interview is whether he can tell correct from merely
plausible in generated code, and this repo is the evidence.

## Rules for Claude

- Read the real documentation before writing against a library. Report the
  version you read against; SDKs move (the MCP Python SDK went 1.x to 2.x in
  2026 and renamed `FastMCP` to `MCPServer`, which broke every tutorial).
- Prefer the smallest thing that works. Do not add tools, endpoints or
  abstractions that were not asked for.
- Tests come with the code, not after. Tests must fail before the code exists.
- Never commit private data. The real tracker, letters, profile and anything
  with a real company, recruiter or salary in it stays out of the repo. Sample
  data is invented and lives in `examples/`.
- When something is a judgement call, stop and ask. Do not pick silently.
- Push back when a request is wrong. Say so plainly and say why.

## Running

    uv sync
    uv run pytest
    uv run server.py                      # stdio, sample data
    JOBHUNT_TRACKER=~/job-hunt/applications/TRACKER.md uv run server.py
