"""Tests for fetch_ad.py.

A throwaway local HTTP server serves examples/, so these run offline and never
touch a real job board. Each fetch launches headless Chromium.

Run: uv run pytest -q
"""

import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

import fetch_ad

EXAMPLES = Path(__file__).parent.parent / "examples"


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def base_url():
    handler = partial(_QuietHandler, directory=str(EXAMPLES))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


@pytest.fixture(scope="module")
def ad(base_url):
    return fetch_ad.fetch_ad(f"{base_url}/ad.sample.html")


# ---- fetch_ad ------------------------------------------------------------


def test_returns_url_title_and_text(ad, base_url):
    assert ad["url"] == f"{base_url}/ad.sample.html"
    assert ad["title"] == "AI Platform Engineer - Corvid Labs"
    assert "Perth WA (4 days in office)" in ad["text"]


def test_captures_text_rendered_by_javascript(ad):
    # This exact string is not in the HTML file. Only a browser that runs the
    # page's script produces it, which is why a plain HTTP fetch is not enough.
    assert "Salary: $110,000 to $120,000" in ad["text"]


def test_excludes_script_source(ad):
    assert "tracking-id-7f3a" not in ad["text"]


def test_http_error_raises_instead_of_returning_the_error_page(base_url):
    with pytest.raises(fetch_ad.FetchError, match="404"):
        fetch_ad.fetch_ad(f"{base_url}/missing.html")


def test_unreachable_url_raises_fetch_error():
    # Port 1 refuses connections, so this fails fast without a real network.
    with pytest.raises(fetch_ad.FetchError, match="could not load"):
        fetch_ad.fetch_ad("http://127.0.0.1:1/")



# ---- fetch_ads (several links, one browser) ------------------------------


def test_fetch_ads_returns_one_result_per_url_in_input_order(base_url):
    urls = [f"{base_url}/ad.sample.html?n=1", f"{base_url}/ad.sample.html?n=2"]
    results = fetch_ad.fetch_ads(urls)
    assert [r["url"] for r in results] == urls
    assert all(r["title"] == "AI Platform Engineer - Corvid Labs" for r in results)


def test_one_failing_url_does_not_stop_the_batch(base_url):
    results = fetch_ad.fetch_ads([f"{base_url}/missing.html", f"{base_url}/ad.sample.html"])
    assert "404" in results[0]["error"]
    assert "title" not in results[0]
    assert results[1]["title"] == "AI Platform Engineer - Corvid Labs"


# ---- command line --------------------------------------------------------


def test_cli_prints_a_json_list_for_one_or_more_urls(base_url, capsys):
    assert fetch_ad.main([f"{base_url}/ad.sample.html", f"{base_url}/ad.sample.html?n=2"]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert len(printed) == 2
    assert printed[0]["title"] == "AI Platform Engineer - Corvid Labs"


def test_cli_exits_nonzero_if_any_url_failed_but_still_prints_the_rest(base_url, capsys):
    assert fetch_ad.main([f"{base_url}/missing.html", f"{base_url}/ad.sample.html"]) == 1
    printed = json.loads(capsys.readouterr().out)
    assert "error" in printed[0] and "title" in printed[1]
