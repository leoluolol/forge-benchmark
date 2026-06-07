"""Rebuild FORGE clean evidence bundles from their URL index.

FORGE ships an INDEX (url + anchor span + short excerpts), not full page bodies (the source
pages are third-party copyrighted content). This module reconstructs the content on the user's
machine: re-fetch each URL, extract visible text, and fall back to the Wayback Machine on
link-rot. The reconstructed text is a best-effort approximation — live pages drift over time, so
the Wayback snapshot gives the closest-to-original version.

Usage:
    python -m forge.fetch                       # rebuild every bundle in data/clean_bundles/
    python -m forge.fetch --bundle <query_id>   # rebuild one query

Status per document: refetched | refetched_from_wayback | dead.

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

BUNDLES_DIR = Path(__file__).resolve().parent.parent / "data" / "clean_bundles"
USER_AGENT = "forge-benchmark/0.1 (+https://github.com/leoluolol/forge-benchmark)"


class _HTMLText(HTMLParser):
    """Minimal stdlib HTML -> visible-text extractor (drops script/style)."""
    _SKIP = {"script", "style", "noscript", "template"}

    def __init__(self):
        super().__init__()
        self._parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self._parts.append(data)

    def text(self) -> str:
        return "".join(self._parts)


def html_to_text(html: str) -> str:
    parser = _HTMLText()
    try:
        parser.feed(html)
    except Exception:
        pass
    return parser.text()


def normalize(text: str) -> str:
    """Apply the dataset text normalization (NFKC + whitespace-collapse) to the extracted page
    text, so the reconstructed `content` matches the form the anchor brand is stored in."""
    return " ".join(unicodedata.normalize("NFKC", text).split())


def _fetch(url: str, timeout: int = 20) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        return html_to_text(raw.decode("utf-8", errors="replace"))
    except Exception:
        return None


def _wayback(url: str) -> str:
    """Wayback 'closest snapshot to 2026' redirect for a source URL — derived here, not stored
    per-doc (the bundle index carries only the live `url`)."""
    return "https://web.archive.org/web/2026/" + url


def rebuild_doc(doc: dict) -> dict:
    """Re-fetch one document (live, then Wayback on link-rot), extract + normalize its text.
    Returns the doc with `content` (rebuilt text or None) and `rebuild_status`
    (refetched | refetched_from_wayback | dead)."""
    live = doc.get("url")
    for url, via in ((live, "live"), (_wayback(live) if live else None, "wayback")):
        if not url:
            continue
        text = _fetch(url)
        if text is None:
            continue
        status = "refetched_from_wayback" if via == "wayback" else "refetched"
        return {**doc, "content": normalize(text), "rebuild_status": status}
    return {**doc, "content": None, "rebuild_status": "dead"}


def rebuild_bundle(path: Path) -> dict:
    bundle = json.loads(path.read_text(encoding="utf-8"))
    bundle["docs"] = [rebuild_doc(d) for d in bundle.get("docs", [])]
    return bundle


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Rebuild FORGE clean evidence bundles from the URL index.")
    ap.add_argument("--bundles-dir", default=str(BUNDLES_DIR))
    ap.add_argument("--bundle", default=None, help="rebuild only this query_id")
    ap.add_argument("--out", default=None, help="output dir (default: alongside, as *.rebuilt.json)")
    args = ap.parse_args(argv)

    base = Path(args.bundles_dir)
    files = [base / f"{args.bundle}.json"] if args.bundle else sorted(base.glob("*.json"))
    files = [f for f in files if f.name != "README.md" and f.exists()]
    if not files:
        print(f"No bundle index files in {base} (the index is populated in the data drop).", file=sys.stderr)
        return 1

    n_ok = n_doc = 0
    for f in files:
        rebuilt = rebuild_bundle(f)
        for doc in rebuilt["docs"]:
            n_doc += 1
            n_ok += doc["rebuild_status"] != "dead"
        out_path = (Path(args.out) / f.name) if args.out else f.with_suffix(".rebuilt.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(rebuilt, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"rebuilt {len(files)} bundle(s); {n_ok}/{n_doc} documents reconstructed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
