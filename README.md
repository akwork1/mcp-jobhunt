# mcp-jobhunt

An MCP server over a job-application tracker.

I graduated in June 2026, my contract ended in September, and I was applying to
several AI engineering roles a day. The ads kept asking for the same things I
had never built in the open: an MCP server, webhooks, a vector store, a cloud
deployment, an agent framework, a public repository. So I am rebuilding the
system I already use to run the job hunt, one piece per weekend, in public.
This repo is slice one.

## What it does

My tracker is a markdown table: one row per application, with a long notes
cell recording which argument the letter made, which gaps it named, what salary
was answered, and what to check before sending. It is over 40,000 tokens and
a Claude session used to re-read the whole thing to answer "what did I say to
the last Perth employer?".

This server exposes it as two tools any MCP client can call:

| Tool | Purpose |
|---|---|
| `list_applications(status?, location?)` | Compact list of rows, filtered. Find the row first. |
| `get_application(company)` | One row in full, including the notes. |

The client asks a question, the model calls the tool, the tool reads the file.
The model sees only the rows it asked for.

## Run it

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

    uv sync
    uv run pytest                 # 14 tests against the sample data
    uv run server.py              # starts on stdio with examples/tracker.sample.md

Point it at a real tracker with an environment variable:

    JOBHUNT_TRACKER=/path/to/TRACKER.md uv run server.py

### In Claude Code

    claude mcp add jobhunt -e JOBHUNT_TRACKER=/path/to/TRACKER.md -- uv --directory /path/to/mcp-jobhunt run server.py

Then ask Claude "which Perth roles have I applied to and what did I answer for
salary?" and watch it call `list_applications` then `get_application`.

### In the MCP Inspector

    npx @modelcontextprotocol/inspector uv run server.py

## Design notes

**stdio first.** The server speaks MCP over stdin/stdout, which is what a local
client like Claude Code launches. Streamable HTTP, for a server running
somewhere else, is slice 4 alongside the AWS deployment.

**The data file is configuration, not code.** The repo ships invented sample
data. My real tracker has recruiters' phone numbers in it and is never
committed. The path comes from `JOBHUNT_TRACKER`.

**Two tools, not one.** `list_applications` returns five columns per row;
`get_application` returns everything. A single tool that returned full rows
would hand the model the same 40,000 tokens the server exists to avoid.

**Docstrings are the interface.** The MCP SDK turns each function's signature
into the tool's JSON schema and its docstring into the description the model
reads when deciding which tool to call. They describe what the tool is for,
not what the code does.

**Errors are `ToolError`, not `ValueError`.** The SDK treats an unexpected
exception as a crash and hides the message from the client. A `ToolError`
passes the message through, so the model can see "no application matching
'Acme'" and correct itself.

**The parser splits on unescaped pipes only.** Markdown allows a literal `|`
in a cell as `\|`, and my notes use it. `re.split(r"(?<!\\)\|")` handles that;
`str.split("|")` silently shifts every column after it.

## Built against

`mcp` 2.2.0 (Python SDK). The 2.x release renamed `FastMCP` to `MCPServer`
and changed attribute casing on the client side (`inputSchema` is now
`input_schema`). Most tutorials online still show 1.x.

## Roadmap

1. **This.** MCP server over the tracker, stdio.
2. Webhook endpoint that fires on a new ad, and an n8n workflow that calls it.
3. Playwright fetcher for saved ad pages, LLM extraction into Postgres.
4. pgvector with hybrid search, and an eval harness with a published accuracy number.
5. Deploy to AWS, Streamable HTTP transport.
6. LangGraph apply-or-skip agent against my own rules.
7. Langfuse tracing across the lot.

How the repo is built, and who does what, is in [CLAUDE.md](CLAUDE.md).
