"""BM25, the lexical ranker the walk and the refined path use internally.

It shortlists pages for the shortlist walk, pre-ranks passages before they are judged,
and finds the closest answers offered as links. It is not a decision backend.
"""

from __future__ import annotations

import math
import re

# Question filler ("how do I get a ...") carries no topic, but on short docs BM25 still
# counts it, so a leaf full of `... get` commands wins every "how do I get X" question.
_STOPWORDS = frozenset(
    "a an and are as at be by can could do does for from get got how i i'm im in is it its me "
    "my of on or please should so that the this to want wanna we what when where which who "
    "why will with would you your".split()
)


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOPWORDS]


class BM25:
    """Okapi BM25 over a fixed set of short documents."""

    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75) -> None:
        self.docs = [_tokens(d) for d in docs]
        self.k1, self.b = k1, b
        self.avgdl = sum(len(d) for d in self.docs) / len(self.docs)
        df: dict[str, int] = {}
        for doc in self.docs:
            for term in set(doc):
                df[term] = df.get(term, 0) + 1
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def __call__(self, query: str) -> list[float]:
        terms = [t for t in _tokens(query) if t in self.idf]
        scores = []
        for doc in self.docs:
            norm = self.k1 * (1 - self.b + self.b * len(doc) / self.avgdl)
            score = 0.0
            for term in terms:
                tf = doc.count(term)
                score += self.idf[term] * tf * (self.k1 + 1) / (tf + norm)
            scores.append(score)
        return scores
