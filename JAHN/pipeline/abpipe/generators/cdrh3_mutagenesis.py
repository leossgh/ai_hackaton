from __future__ import annotations

import json
import random

import polars as pl

from abpipe import data
from abpipe.base import Context, Generator
from abpipe.registry import register

AA = "ACDEFGHIKLMNPQRSTVWY"


@register("generator", "cdrh3_mutagenesis")
class Cdrh3Mutagenesis(Generator):
    """Random substitutions inside the parent's mutable CDRH3 window (no GPU, no network)."""

    version = "1"

    def __init__(self, min_subs: int = 4, max_subs: int = 8, exclude: str = "C",
                 prior: str = "uniform", prior_classes: tuple = ("high",)):
        if not 1 <= min_subs <= max_subs:
            raise ValueError("need 1 <= min_subs <= max_subs")
        if prior not in ("uniform", "facs"):
            raise ValueError("prior must be 'uniform' or 'facs'")
        self.min_subs, self.max_subs, self.prior = min_subs, max_subs, prior
        self.prior_classes = tuple(prior_classes)
        self.alphabet = [a for a in AA if a not in exclude]

    def _weights(self, ctx: Context, length: int) -> list[dict]:
        if self.prior == "uniform":
            return [{a: 1.0 for a in self.alphabet} for _ in range(length)]
        facs = data.facs_table(ctx).filter(pl.col("binding_class").is_in(list(self.prior_classes)))
        seqs = facs["cdrh3"].to_list()
        out = []
        for p in range(length):
            counts = {a: 1.0 for a in self.alphabet}          # +1 smoothing
            for s in seqs:
                if s[p] in counts:
                    counts[s[p]] += 1.0
            out.append(counts)
        return out

    def generate(self, n: int, seed: int, ctx: Context) -> pl.DataFrame:
        parent = ctx.require_parent()
        win, length = parent.window, len(parent.window)
        if self.max_subs > length:
            raise ValueError(f"max_subs {self.max_subs} exceeds the {length}-residue window")
        rng, weights = random.Random(seed), self._weights(ctx, length)
        seen, rows, attempts = set(), [], 0
        while len(rows) < n and attempts < n * 50:
            attempts += 1
            k = rng.randint(self.min_subs, self.max_subs)
            new, subs = list(win), []
            for p in sorted(rng.sample(range(length), k)):
                choices = [a for a in self.alphabet if a != win[p]]
                a = rng.choices(choices, [weights[p][c] for c in choices])[0]
                new[p] = a
                subs.append(f"{win[p]}{p + 1}{a}")
            w2 = "".join(new)
            if w2 in seen:
                continue
            seen.add(w2)
            heavy = parent.heavy[:parent.window_start] + w2 + parent.heavy[parent.window_start + length:]
            rows.append({"sequence_id": f"{self.name}_s{seed}_{len(rows):06d}", "kind": "paired",
                         "heavy_sequence": heavy, "light_sequence": parent.light,
                         "design_description": f"{k} substitutions in the CDRH3 window of {parent.id}",
                         "parent_id": parent.id, "origin": self.name, "seed": seed,
                         "meta": json.dumps({"window": w2, "subs": subs})})
        if len(rows) < n:
            print(f"warning: {self.name} produced {len(rows)} of {n} requested unique variants")
        return pl.DataFrame(rows, schema={"sequence_id": pl.String, "kind": pl.String, "heavy_sequence": pl.String,
                                          "light_sequence": pl.String, "design_description": pl.String,
                                          "parent_id": pl.String, "origin": pl.String, "seed": pl.Int64,
                                          "meta": pl.String})
