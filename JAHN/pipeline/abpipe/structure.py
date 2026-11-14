"""Minimal mmCIF reading and antibody-antigen contact analysis (numpy only).

Used by the epitope scorer and the calibration script. Contacts are intrinsic to one
structure (residue sets by number), so no superposition is needed to compare an
antigen epitope between a prediction and the crystal structure.
"""
from __future__ import annotations

import numpy as np

THREE = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q", "GLU": "E", "GLY": "G",
         "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P", "SER": "S",
         "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V"}


def read_chains(path, *, auth: bool = False) -> dict:
    """chain id -> list of (residue number, one-letter code, heavy-atom coordinates [n, 3]), in file order."""
    cols, in_loop, chains = [], False, {}
    cur_key = None
    for line in open(path):
        if line.startswith("_atom_site."):
            cols.append(line.strip().split(".", 1)[1]); in_loop = True
            continue
        if in_loop and not cols:
            continue
        if in_loop and (line.startswith("#") or line.startswith("loop_")):
            break
        if not (in_loop and line.startswith(("ATOM", "HETATM"))):
            continue
        t = line.split()
        if len(t) < len(cols):
            continue
        g = dict(zip(cols, t))
        if g.get("group_PDB") != "ATOM" or g.get("type_symbol", "C") == "H":
            continue
        chain = g["auth_asym_id"] if auth and "auth_asym_id" in g else g["label_asym_id"]
        num = int(g["auth_seq_id"] if auth and "auth_seq_id" in g else g["label_seq_id"])
        comp = g["label_comp_id"]
        res = chains.setdefault(chain, [])
        if not res or res[-1][0] != num:
            res.append([num, THREE.get(comp, "X"), []])
        res[-1][2].append((float(g["Cartn_x"]), float(g["Cartn_y"]), float(g["Cartn_z"])))
    return {c: [(n, aa, np.array(xyz)) for n, aa, xyz in r] for c, r in chains.items()}


def sequence(residues) -> str:
    return "".join(aa for _, aa, _ in residues)


def assign_roles(chains: dict, expected: dict, min_identity: float = 0.9) -> dict:
    """Map role -> chain id by sequence identity to the expected sequences (e.g. H, L, A)."""
    seqs = {c: sequence(r) for c, r in chains.items()}
    out = {}
    for role, exp in expected.items():
        best, best_id = None, 0.0
        for c, s in seqs.items():
            same = sum(a == b for a, b in zip(s, exp)) / max(len(s), len(exp))
            if same > best_id:
                best, best_id = c, same
        if best is None or best_id < min_identity:
            raise ValueError(f"no chain matches role {role} (best identity {best_id:.2f})")
        out[role] = best
    if len(set(out.values())) != len(out):
        raise ValueError(f"two roles matched the same chain: {out}")
    return out


def contact_residues(binder, target, cutoff: float = 4.5) -> set:
    """Residue numbers of `target` with any heavy atom within `cutoff` A of any heavy atom of `binder`."""
    A = np.vstack([xyz for _, _, xyz in binder])
    B = np.vstack([xyz for _, _, xyz in target])
    owner = np.concatenate([[i] * len(xyz) for i, (_, _, xyz) in enumerate(target)])
    near = np.zeros(len(B), dtype=bool)
    for lo in range(0, len(B), 400):                       # chunk to bound memory
        d2 = ((B[lo:lo + 400, None, :] - A[None, :, :]) ** 2).sum(-1)
        near[lo:lo + 400] = (d2 <= cutoff ** 2).any(axis=1)
    hit = np.unique(owner[near])
    return {target[i][0] for i in hit}


def epitope(chains: dict, roles: dict, cutoff: float = 4.5) -> set:
    """Antigen residue numbers contacted by the heavy or light chain."""
    ag = chains[roles["A"]]
    ab = chains[roles["H"]] + chains[roles["L"]]
    return contact_residues(ab, ag, cutoff)


def overlap(pred: set, ref: set) -> dict:
    inter = len(pred & ref)
    return {"epitope_recall": inter / len(ref) if ref else np.nan,
            "epitope_precision": inter / len(pred) if pred else 0.0,
            "epitope_jaccard": inter / len(pred | ref) if (pred | ref) else np.nan,
            "n_epitope_residues": len(pred)}
