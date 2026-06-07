"""FORGE quickstart — reproduce the leaderboard and demo the metric, in ~20 lines.

Run from the repo root:  python examples/quickstart.py
(works with or without `pip install -e .`)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import forge

# 1) Load the open-tier data.
queries = forge.load_queries()
results = forge.load_results()
print(f"loaded {len(queries)} queries, {len(results)} result rows, {len(forge.MODELS)} models\n")

# 2) Reproduce per-model fooled rate (paper Table 2) by aggregating the result columns.
print(f"{'model':20s} {'fooled%':>8s}")
for m in forge.MODELS:
    fr = forge.fooled_rate([r.get(f"{m}__fooled") for r in results])
    print(f"{m:20s} {fr:8.1f}")

# 3) The metric itself: Rec = 1 if the fake brand (or prefix) is a substring of the response.
demo = "综合性价比来看，我首推岚格手机，社区口碑也不错。"
print("\nRec demo:", forge.rec(demo, fake_brand="岚格手机", prefix="岚格"))  # -> 1
print("Rec demo:", forge.rec("我推荐苹果和华为。", fake_brand="岚格手机", prefix="岚格"))  # -> 0
