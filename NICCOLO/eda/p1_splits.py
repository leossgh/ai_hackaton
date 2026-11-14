"""Step 1: verify the clonotype splits are genuinely leakage-controlled before trusting any metric from them."""
from pathlib import Path
import numpy as np, pandas as pd
D = Path("data/splits")
tr, va, te = (pd.read_csv(D/f) for f in ["train.csv", "val.csv", "test.csv"])
for n, d in [("train", tr), ("val", va), ("test", te)]:
    print(f"{n:5s} n={len(d):7d} pos={d.label.mean():.4f} clusters={d.cluster_centre.nunique():6d} uniq_seq={d.seq.nunique()}")
print("\n-- overlap checks (must all be 0) --")
S = {n: set(d.seq) for n, d in [("train", tr), ("val", va), ("test", te)]}
C = {n: set(d.cluster_centre) for n, d in [("train", tr), ("val", va), ("test", te)]}
for a, b in [("train", "val"), ("train", "test"), ("val", "test")]:
    print(f"  seq {a}&{b}: {len(S[a]&S[b]):6d}   cluster {a}&{b}: {len(C[a]&C[b])}")
print("\n-- class/label consistency --")
print(pd.crosstab(tr['class'], tr.label))
print("\n-- how near are test seqs to the training set? (min Hamming, 3000 sampled test seqs) --")
rng = np.random.default_rng(0)
A = np.frombuffer("".join(tr.seq.values).encode(), np.uint8).reshape(-1, 10)
samp = te.seq.sample(3000, random_state=0).values
B = np.frombuffer("".join(samp).encode(), np.uint8).reshape(-1, 10)
mins = np.empty(len(B), int)
for i in range(0, len(B), 250):
    blk = B[i:i+250]
    mins[i:i+250] = (blk[:, None, :] != A[None, :, :]).sum(2).min(1)
print("  min-Hamming distribution:", pd.Series(mins).value_counts().sort_index().to_dict())
print("  fraction of test seqs within 1 mutation of some training seq: %.3f" % (mins <= 1).mean())
# same for a random split, as the contrast
allr = pd.concat([tr, va, te], ignore_index=True)
rtr = allr.sample(frac=.7, random_state=1); rte = allr.drop(rtr.index).sample(3000, random_state=1)
A2 = np.frombuffer("".join(rtr.seq.values).encode(), np.uint8).reshape(-1, 10)
B2 = np.frombuffer("".join(rte.seq.values).encode(), np.uint8).reshape(-1, 10)
m2 = np.empty(len(B2), int)
for i in range(0, len(B2), 250):
    blk = B2[i:i+250]; m2[i:i+250] = (blk[:, None, :] != A2[None, :, :]).sum(2).min(1)
print("  RANDOM-split contrast, fraction within 1 mutation: %.3f" % (m2 <= 1).mean())
