"""Edit distances: Hamming where it is exactly the right metric, Levenshtein otherwise.

For strings of equal length Hamming counts substituted positions. It is never smaller than
Levenshtein (a shifted loop is 2 edits by Levenshtein but many by Hamming), so it is used only
for our own scores of substitution-only variants. The official novelty checks keep Levenshtein:
using Hamming there could overstate how far a design is from a known antibody.
"""
from __future__ import annotations

from rapidfuzz import process
from rapidfuzz.distance import Hamming, Levenshtein

METRICS = ("auto", "hamming", "levenshtein")


def check_metric(metric: str) -> str:
    if metric not in METRICS:
        raise ValueError(f"metric must be one of {METRICS}, got {metric!r}")
    return metric


def distance(a: str, b: str, metric: str = "auto") -> int | None:
    """auto: Hamming when the lengths are equal, else Levenshtein.
    hamming: None when the lengths differ (Hamming is undefined there). levenshtein: always defined."""
    if metric == "levenshtein":
        return Levenshtein.distance(a, b)
    if len(a) == len(b):
        return Hamming.distance(a, b)
    return Levenshtein.distance(a, b) if metric == "auto" else None


def nearest(seq: str, buckets: dict, metric: str = "auto"):
    """(distance, id) of the closest reference, or None. `buckets` maps length -> (sequences, ids)."""
    best = None
    for length, (seqs, ids) in buckets.items():
        if metric != "levenshtein" and length == len(seq):
            scorer = Hamming.distance
        elif metric == "hamming":
            continue
        else:
            scorer = Levenshtein.distance
        m = process.extractOne(seq, seqs, scorer=scorer)
        if m is not None and (best is None or m[1] < best[0]):
            best = (m[1], ids[m[2]])
    return best
