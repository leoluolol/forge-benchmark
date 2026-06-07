"""FORGE: Fake Online Recommendations in Generative Environments.

A benchmark for measuring whether search-augmented LLMs recommend fake brands
when retrieval evidence is poisoned.

Open-tier API:
    from forge import rec, fooled_rate, load_queries, load_results
    from forge.pollute import regenerate_polluted
"""
from forge.metric import rec, fooled_rate, top1_rate
from forge.loaders import load_queries, load_results, MODELS

__version__ = "0.1.0"
__all__ = ["rec", "fooled_rate", "top1_rate", "load_queries", "load_results", "MODELS"]
