"""Loaders for the FORGE open-tier data files (queries, results, clean bundles).

Small loader functions; the data lives under ../data/, not vendored into the code package.
"""
from __future__ import annotations
import json, os
from typing import Iterator

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA = os.path.normpath(os.path.join(_HERE, "..", "data"))

# Public model short-names evaluated in the paper (12 production LLMs).
MODELS = [
    "gemini-3-flash", "gpt-5.4", "o4-mini", "gemini-3.1-pro",
    "claude-opus-4.7", "claude-sonnet-4.6",  # closed-source (6)
    "qwen3.6-27b", "qwen3.6-35b-a3b", "qwen3.5-9b",
    "deepseek-v4-pro", "glm-4.6v-flash", "ministral-3r",  # open-weights (6)
]


def _jsonl(path: str) -> Iterator[dict]:
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_queries(path: str | None = None) -> list[dict]:
    """The 225 product queries: query_id, scenario, category, product, query."""
    return list(_jsonl(path or os.path.join(_DATA, "forge_queries.jsonl")))


def load_results(path: str | None = None) -> list[dict]:
    """Per-query, 12-model results (results-as-columns):
    query_id, category, product, attack, <model>__fooled, <model>__top1."""
    return list(_jsonl(path or os.path.join(_DATA, "results", "forge_results.jsonl")))


def load_clean_bundle(query_id: str, path: str | None = None,
                      rebuilt: bool = False) -> dict | None:
    """The frozen, UN-poisoned evidence bundle for a query (if released).

    Default reads the shipped INDEX (url + anchor + short excerpts, no page body).
    Pass ``rebuilt=True`` to load the locally reconstructed bundle
    (``<query_id>.rebuilt.json`` from ``python -m forge.fetch``), whose docs carry the
    full ``content`` field that ``forge.pollute`` rewrites. Returns None if the requested
    file is not present locally (run ``forge.fetch`` first when ``rebuilt=True``)."""
    base = path or os.path.join(_DATA, "clean_bundles")
    fp = os.path.join(base, f"{query_id}{'.rebuilt' if rebuilt else ''}.json")
    if not os.path.exists(fp):
        return None
    with open(fp, encoding="utf-8") as f:
        return json.load(f)
