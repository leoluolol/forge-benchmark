# Clean evidence bundles (rebuildable index)

This directory holds, per query, a **rebuildable index** of the search results retrieved for
that query — **not** the page text. The source pages are third-party copyrighted web content,
so FORGE ships only:

- the **URL** of each document (canonical, tracking parameters stripped),
- the real-brand **`anchor`** on each of the three attacked documents (ranks 1–3) — the real brand the A1 top-3 attack replaces, and
- short display metadata.

The full document text is **rebuilt locally** by `forge/fetch.py`, which re-fetches each URL and
extracts the text, falling back to the Wayback Machine on link-rot.

## Schema — one `<query_id>.json` per query

```json
{
  "query_id": "electronics_accessories_05",
  "query": "数据线 推荐",
  "retrieved_at": "2026-04",
  "recipe_version": "A1-top3-v1",
  "docs": [
    {
      "rank": 1,
      "url": "https://example.com/p/123",
      "title": "(display only, ≤~70 chars)",
      "snippet": "(display only, ≤200 chars, PII-scrubbed)",
      "anchor": {"brand": "闪魔"}
    }
  ]
}
```

- **Normalization**: `forge.fetch.normalize` applies **NFKC + whitespace-collapse** to the
  reconstructed page text, so it matches the form the `anchor.brand` is stored in.
- **Wayback fallback**: `forge.fetch` derives the archive URL from each `url` as
  `https://web.archive.org/web/2026/<url>`; it is not stored per document.
- `anchor` marks the real brand the top-3 attack replaces (present on ranks 1–3); `anchor.brand`
  is what `forge.pollute` swaps. `title` and `snippet` (each ≤200 chars, PII-scrubbed) are the
  **only** text shipped.
- Regenerate the **polluted** documents with `forge.pollute.regenerate_polluted` over the
  re-fetched text.

`forge.loaders.load_clean_bundle(query_id)` reads this shape and returns `None` if the bundle is
not present locally.
