"""FORGE pollution recipe (A1 entity replacement): regenerate the polluted bundle locally.

The materialized polluted documents are not distributed; you regenerate them LOCALLY from:
  (1) a CLEAN evidence bundle whose document `content` you reconstructed with
      `forge.fetch` (the shipped index carries no full page body), and
  (2) a synthetic fake brand that YOU supply.

The fake brand must be synthetic and collision-free with real entities (see the paper's
lexical-collision audit).
"""
from __future__ import annotations

from copy import deepcopy

_TEXT_FIELDS = ("title", "snippet", "summary", "content", "body")


def replace_in_document(doc: dict, real: str, fake: str) -> dict:
    """A1 on one document: rewrite the dominant real-brand mention to the fake brand in
    title / snippet / content, preserving url / rank. Case-sensitive (brands are
    proper nouns)."""
    d = deepcopy(doc)
    for field in _TEXT_FIELDS:
        if isinstance(d.get(field), str) and real:
            d[field] = d[field].replace(real, fake)
    anchor = d.get("anchor")
    if isinstance(anchor, dict) and anchor.get("brand") == real:
        d["anchor"] = {**anchor, "brand": fake}
    return d


def regenerate_polluted(clean_bundle: dict, fake_brand: str | None = None,
                        brand_swap: dict[str, str] | None = None,
                        ranks: tuple[int, ...] = (1, 2, 3)) -> dict:
    """Regenerate the A1-polluted bundle from a clean bundle.

    Run ``forge.fetch`` first so each document has a ``content`` field (the shipped index
    carries no full page body). Then pollute the documents at ``ranks`` by rewriting their
    dominant real brand to a synthetic fake brand. Provide EITHER:

      * ``fake_brand`` — the real brand of each polluted doc is taken from
        ``doc['anchor']['brand']`` and swapped to this fake brand; or
      * ``brand_swap = {real_brand: fake_brand}`` — an explicit map.

    Documents outside ``ranks`` pass through verbatim. Returns a polluted bundle of the
    same shape, plus ``polluted_ranks`` and ``brands_swapped``.
    """
    if (fake_brand is None) == (brand_swap is None):
        raise ValueError("pass exactly one of fake_brand=... or brand_swap={real: fake}")
    out = deepcopy(clean_bundle)
    rank_set = set(ranks)
    swapped: dict[str, str] = {}
    for doc in out.get("docs", []):
        if doc.get("rank") not in rank_set:
            continue
        if brand_swap is not None:
            pairs = list(brand_swap.items())
        else:
            real = (doc.get("anchor") or {}).get("brand")
            pairs = [(real, fake_brand)] if real else []
        for real, fake in pairs:
            if not real:
                continue
            doc.update(replace_in_document(doc, real, fake))
            swapped[real] = fake
    out["polluted_ranks"] = sorted(rank_set)
    out["brands_swapped"] = swapped
    return out


__all__ = ["regenerate_polluted", "replace_in_document"]
