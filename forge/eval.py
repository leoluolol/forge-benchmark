"""FORGE evaluation harness (CLI).

Two entry points:

  # Reproduce the 12-model leaderboard from the released results (paper Table 2):
  python -m forge.eval leaderboard

  # Score your OWN model outputs (after regenerating the polluted bundle locally
  # with forge.pollute and querying your model):
  python -m forge.eval score --outputs my_outputs.jsonl
      # my_outputs.jsonl: one JSON object per line with keys
      #   response (str), fake_brand (str), [prefix (str)]
"""
from __future__ import annotations
import argparse, json, sys
from forge.loaders import load_results, MODELS
from forge.metric import fooled_rate, score_outputs


def cmd_leaderboard(args):
    rows = load_results(args.results)
    print(f"FORGE leaderboard — {len(rows)} queries, {len(MODELS)} models, "
          f"attack={rows[0].get('attack', 'A1-top3') if rows else 'n/a'}\n")
    print(f"{'model':20s} {'fooled%':>8s} {'top1%':>7s} {'n':>5s}")
    print("-" * 44)
    table = []
    for m in MODELS:
        fooled = [r.get(f"{m}__fooled") for r in rows]
        top1 = [r.get(f"{m}__top1") for r in rows]
        n = sum(1 for v in fooled if v is not None)
        table.append((m, fooled_rate(fooled), fooled_rate(top1), n))
    for m, fr, tr, n in table:  # paper order (closed-source then open-weights)
        print(f"{m:20s} {fr:8.1f} {tr:7.1f} {n:5d}")
    grand = fooled_rate([v for r in rows for m in MODELS
                         for v in [r.get(f'{m}__fooled')]])
    print("-" * 44)
    print(f"{'grand mean':20s} {grand:8.1f}")
    print("\nNote: this is a measurement table, not a competitive leaderboard — "
          "a higher fooled rate means MORE vulnerable.")


def cmd_score(args):
    recs = [json.loads(l) for l in open(args.outputs, encoding="utf-8") if l.strip()]
    out = score_outputs(recs)
    print(f"scored {out['n']} outputs")
    print(f"fooled rate: {out['fooled_rate']:.1f}%")


def main(argv=None):
    p = argparse.ArgumentParser(prog="forge.eval", description="FORGE evaluation harness")
    sub = p.add_subparsers(dest="cmd", required=True)
    lb = sub.add_parser("leaderboard", help="reproduce the released 12-model results")
    lb.add_argument("--results", default=None, help="path to forge_results.jsonl")
    lb.set_defaults(func=cmd_leaderboard)
    sc = sub.add_parser("score", help="score your own model outputs")
    sc.add_argument("--outputs", required=True, help="jsonl with response/fake_brand per line")
    sc.set_defaults(func=cmd_score)
    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
