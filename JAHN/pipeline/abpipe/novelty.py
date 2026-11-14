"""Fast, exact "is any provided window within d substitutions?" test for fixed-length CDRH3 windows.

The novelty rule says a design must be MORE than 2 point mutations from every provided data point. Comparing each
candidate with the 524,346 FACS windows by brute force is O(N x 524k); this index answers it with sorted-array
look-ups instead. Two length-L windows are within Hamming distance 2 exactly when they agree after masking some
pair of positions, so 45 keyed tables (one per pair) decide it exactly. Singles and the exact table give the
finer classes 0 and 1.

Hamming never under-states Levenshtein, so rejecting Hamming <= 2 here can never reject a design the official
Levenshtein check would pass; the official check (track_check) stays the final word.
"""
from __future__ import annotations

from itertools import combinations

import numpy as np
import polars as pl

from abpipe import _niccolo

AA, L = _niccolo.AA, _niccolo.L
_LUT = np.full(256, 255, np.uint8)
for _i, _c in enumerate(AA):
    _LUT[ord(_c)] = _i
_AA_ARR = np.array(list(AA), dtype="S1")
_W21 = 21 ** np.arange(L - 1, -1, -1, dtype=np.int64)       # 20 residues + one 'masked' symbol
_SINGLES = [(i,) for i in range(L)]
_PAIRS = list(combinations(range(L), 2))
_INDEX: dict = {}


def encode(seqs) -> np.ndarray:
    seqs = list(seqs)
    if not seqs:
        return np.zeros((0, L), np.uint8)
    if any(len(s) != L for s in seqs):
        raise ValueError(f"every window must be exactly {L} residues")
    a = _LUT[np.frombuffer("".join(seqs).encode(), np.uint8).reshape(-1, L)]
    if (a == 255).any():
        raise ValueError("non-standard residue in a window")
    return a


def decode(S: np.ndarray) -> list:
    S = np.ascontiguousarray(S, dtype=np.uint8)
    return _AA_ARR[S].view(f"S{L}").ravel().astype(str).tolist()


def _keys(S: np.ndarray, masked: tuple) -> np.ndarray:
    T = S.astype(np.int64)
    if masked:
        T[:, list(masked)] = 20
    return T @ _W21


def _hit(table: np.ndarray, keys: np.ndarray) -> np.ndarray:
    i = np.searchsorted(table, keys)
    i[i == len(table)] = 0
    return table[i] == keys


class WindowIndex:
    def __init__(self, windows):
        S = encode(windows)
        if not len(S):
            raise ValueError("empty reference set")
        self.n = len(S)
        self._exact = np.unique(_keys(S, ()))
        self._single = [np.unique(_keys(S, m)) for m in _SINGLES]
        self._pair = [np.unique(_keys(S, m)) for m in _PAIRS]

    def within(self, S: np.ndarray, d: int) -> np.ndarray:
        """True where some reference window is within d substitutions (d = 0, 1 or 2)."""
        S = np.asarray(S, np.uint8)
        if d == 0:
            return _hit(self._exact, _keys(S, ()))
        if d not in (1, 2):
            raise ValueError("d must be 0, 1 or 2")
        masks, tables = (_SINGLES, self._single) if d == 1 else (_PAIRS, self._pair)
        hit = np.zeros(len(S), bool)
        for m, t in zip(masks, tables):
            hit |= _hit(t, _keys(S, m))
        return hit

    def distance_class(self, S: np.ndarray) -> np.ndarray:
        """0 = identical to a reference window, 1 or 2 = that many substitutions from the nearest, 3 = three or more."""
        S = np.asarray(S, np.uint8)
        cls = np.full(len(S), 3, np.int8)
        cls[self.within(S, 2)] = 2
        cls[self.within(S, 1)] = 1
        cls[self.within(S, 0)] = 0
        return cls


def provided_windows(ctx) -> list:
    """Every 10-residue window the organisers provided: all FACS variants plus the SPR table's windows."""
    from abpipe import data
    wins = set(data.facs_table(ctx)["cdrh3"].to_list())
    wins |= set(pl.read_csv(ctx.data_dir / _niccolo.SPR_REL)["cdrh3"].to_list())
    ok = set(AA)
    return sorted(w for w in wins if len(w) == L and ok.issuperset(w))


def provided_index(ctx) -> WindowIndex:
    key = str(ctx.data_dir.resolve())
    if key not in _INDEX:
        _INDEX[key] = WindowIndex(provided_windows(ctx))
    return _INDEX[key]
