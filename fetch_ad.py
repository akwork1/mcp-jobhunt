"""Fetch job ad pages and return their rendered text.

Opens each URL in headless Chromium so any client-side rendering runs, then
takes the page's visible text. This is the first stage of slice 2: the text
goes on to extraction, and nothing here tries to understand the ad.

Run:   uv run fetch_ad.py <url> [<url> ...]    (prints a JSON list)
Setup: uv run playwright install chromium      (once per machine)
"""

from __future__ import annotations

import json
import sys

from playwright.sync_api import Browser
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright


class FetchError(Exception):
    """The page could not be fetched as an ad."""


def _load(browser: Browser, url: str, timeout_ms: int) -> dict[str, str]:
    """Open url in a fresh page of an already running browser."""
    page = browser.new_page()
    try:
        try:
            response = page.goto(url, timeout=timeout_ms)
        except PlaywrightError as e:
            raise FetchError(f"could not load {url}: {e.message}") from e
        if response is not None and not response.ok:
            raise FetchError(f"HTTP {response.status} fetching {url}")
        return {
            "url": page.url,
            "title": page.title(),
            "text": page.locator("body").inner_text(),
        }
    finally:
        page.close()


def fetch_ads(urls: list[str], timeout_ms: int = 30_000) -> list[dict[str, str]]:
    """Fetch several ad pages with one browser: one result per URL, in order.

    Each result is {"url", "title", "text"}. url is the final address after
    any redirects. text is the body's innerText, meaning what a reader sees:
    script and style contents and hidden elements are left out.

    A URL that fails gives {"url", "error"} instead of stopping the batch, so
    one expired or blocked ad does not lose the rest. Failures include HTTP
    error statuses: Playwright's goto() does not raise on a 404 or 500, so
    without that check an error page would come back looking like an ad.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            results = []
            for url in urls:
                try:
                    results.append(_load(browser, url, timeout_ms))
                except FetchError as e:
                    results.append({"url": url, "error": str(e)})
            return results
        finally:
            browser.close()


def fetch_ad(url: str, timeout_ms: int = 30_000) -> dict[str, str]:
    """Fetch one ad page. Same result as fetch_ads, but raises FetchError."""
    (result,) = fetch_ads([url], timeout_ms)
    if "error" in result:
        raise FetchError(result["error"])
    return result


def main(argv: list[str] | None = None) -> int:
    urls = sys.argv[1:] if argv is None else argv
    if not urls:
        print("usage: uv run fetch_ad.py <url> [<url> ...]", file=sys.stderr)
        return 2
    results = fetch_ads(urls)
    failed = [r for r in results if "error" in r]
    for r in failed:
        print(f"error: {r['error']}", file=sys.stderr)
    # ASCII-escaped JSON: a Windows console or redirected file can't always
    # encode the bullets and dashes real ads are full of.
    print(json.dumps(results, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
