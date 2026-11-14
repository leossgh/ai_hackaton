#!/usr/bin/env python3
"""One AMASS autoresearch pass: gather evidence, propose theory updates, stop.

This is step 2 and step 5 of the cycle in PROMPT.md. It is the *data layer* of
the loop: it chooses the scope, spends AMASS searches, caches everything, and
extracts candidate evidence with citations. It deliberately does NOT decide what
to believe -- it writes proposals into research/pass-NNN.md and the matching
.json, and the agent driving the loop applies them to THEORIES.md / IDEAS.md.
That split is on purpose: a regex can find a KD value, it cannot weigh evidence.

Usage
  python -I research_pass.py                      # auto scope, <=10 new searches
  python -I research_pass.py --scope TH-003        # one theory
  python -I research_pass.py --scope IDEA-007      # one backlog idea
  python -I research_pass.py --scope EXP-004       # post-result re-check
  python -I research_pass.py --max-new 0           # cache only, zero spend
  python -I research_pass.py --dry-run             # show the plan, fetch nothing

Key resolution, in order: $AMASS_API_KEY, --key-file, ../../amass_key.txt
(git-ignored). The key is never written to any file, logged, or printed.

Cost: $0.05 per 20 results. Rate limit 60/60s, so we sleep 1.1s between calls.
Spend is tracked cumulatively in research/spend.json against a team budget.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# `python -I` implies -E, so PYTHONIOENCODING is ignored and Windows falls back
# to cp1252, which blows up on any abstract containing a diaeresis. Force UTF-8.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
RESEARCH = os.path.join(HERE, "research")
THEORIES = os.path.join(HERE, "THEORIES.md")
IDEAS = os.path.join(HERE, "IDEAS.md")
EXPERIMENTS = os.path.join(HERE, "experiments.csv")
SPEND = os.path.join(RESEARCH, "spend.json")

BASE = "https://api.amass.tech/api/v1"
TEAM_BUDGET_SEARCHES = 2000
DEFAULT_MAX_NEW = 10

# Sentences carrying one of these are worth quoting back: they hold a measured
# number rather than a claim about one.
NUMBER_PATTERNS = [
    r"\b\d+(?:\.\d+)?\s*(?:[-]|to)\s*\d+(?:\.\d+)?\s*fold\b",
    r"\b\d+(?:\.\d+)?\s*fold\b",
    r"\bK\s*[dD]\b[^.]{0,40}?\d",
    r"\b\d+(?:\.\d+)?\s*(?:p|n|u|µ)M\b",
    r"\b\d+(?:\.\d+)?\s*[xX]\s*10\(?-?\d+\)?\b",
    r"\bT\s*m\b[^.]{0,30}?\d",
    r"\b\d+(?:\.\d+)?\s*(?:°|deg)\s*C\b",
    r"\bTS50\b",
    r"\bRMSD\b[^.]{0,20}?\d",
]
NUMBER_RE = re.compile("|".join(NUMBER_PATTERNS), re.I)


# --------------------------------------------------------------------------
# parsing the human-readable state files
# --------------------------------------------------------------------------
# [ \t]* not \s*: \s matches newlines, so an empty field
# ("- **evidence_against:**") would swallow the line below it.
FIELD_RE = re.compile(r"^[ \t]*-[ \t]+\*\*([a-z_]+):\*\*[ \t]*(.*)$", re.M)


def parse_fields(body: str) -> dict[str, str]:
    """Field lines, each absorbing any indented continuation beneath it.

    `history` and `notes` carry their value as indented sub-bullets, so a
    single-line match would read them as empty.
    """
    fields: dict[str, str] = {}
    matches = list(FIELD_RE.finditer(body))
    for i, fm in enumerate(matches):
        stop = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        tail = body[fm.end():stop]
        extra = " ".join(
            line.strip().lstrip("-").strip()
            for line in tail.splitlines() if line.strip()
        )
        value = fm.group(2).strip()
        fields[fm.group(1)] = f"{value} {extra}".strip() if extra else value
    return fields


def parse_blocks(path: str, id_prefix: str) -> list[dict]:
    """Parse '### ID -- claim' blocks with '- **field:** value' lines beneath."""
    if not os.path.exists(path):
        return []
    text = open(path, encoding="utf-8").read()
    blocks = []
    pattern = re.compile(
        rf"^###\s+({id_prefix}-\d+)\s*(?:--|—|-)\s*(.+?)$", re.M
    )
    matches = list(pattern.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():end]
        fields = parse_fields(body)
        blocks.append({"id": m.group(1), "claim": m.group(2).strip(), **fields})
    return blocks


def split_terms(value: str) -> list[str]:
    return [t.strip() for t in re.split(r"[;,]", value or "") if t.strip()]


# --------------------------------------------------------------------------
# scope selection
# --------------------------------------------------------------------------
def select_scope(scope: str, theories: list[dict], ideas: list[dict]) -> tuple[list[dict], str]:
    """Return (targets, rationale)."""
    if scope and scope != "auto":
        for coll in (theories, ideas):
            for b in coll:
                if b["id"].lower() == scope.lower():
                    return [b], f"explicit scope {b['id']}"
        if scope.upper().startswith("EXP-"):
            return [{"id": scope.upper(), "claim": f"re-check after {scope.upper()}",
                     "query_terms": ""}], f"post-result re-check of {scope.upper()}"
        raise SystemExit(f"scope {scope!r} not found in THEORIES.md or IDEAS.md")

    # auto: weakest beliefs first, then unbacked ideas.
    weak = [t for t in theories
            if t.get("status", "active") == "active"
            and (t.get("confidence") in {"low", "medium"}
                 or not t.get("evidence_against"))]
    weak.sort(key=lambda t: {"low": 0, "medium": 1}.get(t.get("confidence"), 2))
    unbacked = [i for i in ideas
                if i.get("status") == "open" and not i.get("evidence")]
    targets = weak[:3] + unbacked[:2]
    if not targets:
        targets = theories[:2]
    return targets, ("auto: low/untested theories first (%d), then unbacked ideas (%d)"
                     % (len(weak), len(unbacked)))


# --------------------------------------------------------------------------
# AMASS fetch, always cached
# --------------------------------------------------------------------------
def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60]


def cache_path(core: str, query: str) -> str:
    return os.path.join(CACHE, f"{core}__{slug(query)}.json")


def read_key(key_file: str | None) -> str:
    key = os.environ.get("AMASS_API_KEY", "").strip()
    if key:
        return key
    candidates = [key_file] if key_file else []
    candidates += [os.path.join(HERE, "..", "..", "amass_key.txt"),
                   os.path.expanduser("~/.amass_key")]
    for c in candidates:
        if c and os.path.exists(c):
            value = open(c, encoding="utf-8").read().strip()
            if value:
                return value
    raise SystemExit(
        "no AMASS key: set $AMASS_API_KEY or pass --key-file (never commit it)"
    )


def fetch(core: str, query: str, limit: int, key: str) -> tuple[str, str | None]:
    """Return (status, error). status is 'cached', 'fetched' or 'failed'."""
    out = cache_path(core, query)
    if os.path.exists(out) and os.path.getsize(out) > 0:
        return "cached", None
    url = f"{BASE}/cores/{core}/records?" + urllib.parse.urlencode(
        {"query": query, "limit": limit}
    )
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "User-Agent": "experiment-ledger-autoresearch/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = resp.read()
        json.loads(payload)  # reject anything that is not valid JSON
        with open(out, "wb") as fh:
            fh.write(payload)
        return "fetched", None
    except urllib.error.HTTPError as exc:
        return "failed", f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001
        return "failed", type(exc).__name__


# --------------------------------------------------------------------------
# evidence extraction
# --------------------------------------------------------------------------
def load_records() -> dict[str, dict]:
    records: dict[str, dict] = {}
    for path in sorted(glob.glob(os.path.join(CACHE, "*.json"))):
        try:
            data = json.load(open(path, encoding="utf-8"))["data"]
        except Exception:  # noqa: BLE001
            continue
        core = os.path.basename(path).split("__", 1)[0]
        for rec in data:
            key = str(rec.get("pmid") or rec.get("amassId")
                      or rec.get("publicationNumber") or "")
            if not key:
                continue
            rec.setdefault("_core", core)
            records.setdefault(key, rec)
    return records


def sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text or "").strip()
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text) if s.strip()]


# Words that carry no topical signal, so they must not count toward overlap.
STOPWORDS = {
    "antibody", "antibodies", "protein", "proteins", "prediction", "predicted",
    "using", "based", "with", "from", "that", "this", "these", "their", "which",
    "been", "have", "has", "also", "into", "onto", "than", "then", "when",
    "study", "studies", "results", "method", "methods", "approach", "approaches",
    "show", "shown", "shows", "here", "both", "between", "within", "while",
}
MIN_KEYWORD_HITS = 3


def keywords(terms: list[str]) -> set[str]:
    """Topical words from the query terms, for word-level overlap.

    Matching whole query phrases as substrings finds nothing — an abstract
    never contains "scFv thermostability prediction machine learning
    validation Tm" verbatim. Overlap has to be counted per word.
    """
    words: set[str] = set()
    for term in terms:
        for w in re.findall(r"[a-z0-9]+", term.lower()):
            if len(w) >= 4 and w not in STOPWORDS:
                words.add(w)
    return words


def score_record(rec: dict, kws: set[str]) -> tuple[int, list[str], list[str]]:
    """Keyword-overlap score, the matched words, and quotable measured numbers."""
    blob = f"{rec.get('title','')} {rec.get('abstract','')}".lower()
    hits = sorted(w for w in kws if w in blob)
    if len(hits) < MIN_KEYWORD_HITS:
        return 0, [], []
    quotes = [s for s in sentences(rec.get("abstract", "")) if NUMBER_RE.search(s)]
    return len(hits), quotes[:3], hits


def year_of(rec: dict) -> str:
    d = rec.get("publicationDate") or rec.get("createDate") or ""
    return str(d)[:4] or "?"


# --------------------------------------------------------------------------
# spend tracking
# --------------------------------------------------------------------------
def load_spend() -> dict:
    if os.path.exists(SPEND):
        try:
            return json.load(open(SPEND, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
    return {"searches": 0, "usd": 0.0, "passes": 0}


def save_spend(state: dict) -> None:
    os.makedirs(RESEARCH, exist_ok=True)
    with open(SPEND, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)
        fh.write("\n")


def next_pass_number() -> int:
    existing = glob.glob(os.path.join(RESEARCH, "pass-*.md"))
    nums = [int(m.group(1)) for p in existing
            if (m := re.search(r"pass-(\d+)\.md$", p))]
    return max(nums, default=0) + 1


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scope", default="auto",
                    help="auto | TH-nnn | IDEA-nnn | EXP-nnn")
    ap.add_argument("--max-new", type=int, default=DEFAULT_MAX_NEW,
                    help="cap on new (uncached) searches this pass; 0 = cache only")
    ap.add_argument("--limit", type=int, default=20, help="results per search")
    ap.add_argument("--key-file", default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan and exit without fetching")
    args = ap.parse_args()

    os.makedirs(CACHE, exist_ok=True)
    os.makedirs(RESEARCH, exist_ok=True)

    theories = parse_blocks(THEORIES, "TH")
    ideas = parse_blocks(IDEAS, "IDEA")
    targets, rationale = select_scope(args.scope, theories, ideas)

    # Build the query plan: core|query pairs, deduped, cached ones free.
    plan: list[tuple[str, str, str]] = []  # (target_id, core, query)
    seen = set()
    skipped_no_terms = []
    for t in targets:
        terms = split_terms(t.get("query_terms", ""))
        if not terms:
            # Never spend a paid search on a truncated claim sentence: it reads
            # as prose, not as a query, and returns noise. Demand real terms.
            skipped_no_terms.append(t["id"])
            continue
        for term in terms:
            core = "patentcore" if term.lower().startswith("patent:") else "biomedcore"
            query = re.sub(r"^patent:\s*", "", term, flags=re.I)
            key = (core, slug(query))
            if key in seen:
                continue
            seen.add(key)
            plan.append((t["id"], core, query))

    cached_plan = [p for p in plan if os.path.exists(cache_path(p[1], p[2]))]
    new_plan = [p for p in plan if not os.path.exists(cache_path(p[1], p[2]))]
    allowed_new = new_plan[:max(0, args.max_new)]
    deferred = new_plan[len(allowed_new):]

    print(f"scope      : {args.scope}  ({rationale})")
    print(f"targets    : {', '.join(t['id'] for t in targets)}")
    print(f"queries    : {len(cached_plan)} cached, {len(allowed_new)} new, "
          f"{len(deferred)} deferred by --max-new={args.max_new}")
    if skipped_no_terms:
        print(f"SKIPPED    : {', '.join(skipped_no_terms)} have no query_terms "
              "— add them or these targets can never be researched")
    if args.dry_run:
        for tid, core, q in allowed_new:
            print(f"  would fetch [{tid}] {core}: {q}")
        return 0

    key = read_key(args.key_file) if allowed_new else ""
    fetched, failed = [], []
    for i, (tid, core, q) in enumerate(allowed_new):
        status, err = fetch(core, q, args.limit, key)
        if status == "fetched":
            fetched.append((tid, core, q))
            print(f"  ok     [{tid}] {core}: {q}")
        elif status == "failed":
            failed.append((tid, core, q, err))
            print(f"  FAIL   [{tid}] {core}: {q} -> {err}")
        if i < len(allowed_new) - 1:
            time.sleep(1.1)

    spend = load_spend()
    spend["searches"] += len(fetched)
    spend["usd"] = round(spend["usd"] + len(fetched) * 0.05 * args.limit / 20, 4)
    spend["passes"] += 1
    save_spend(spend)

    # Extract evidence per target from the full cache (old and new alike).
    records = load_records()
    n = next_pass_number()
    today = dt.date.today().isoformat()
    findings: dict[str, list[dict]] = {}
    for t in targets:
        kws = keywords(split_terms(t.get("query_terms", "")) or [t["claim"]])
        scored = []
        for rid, rec in records.items():
            hits, quotes, matched = score_record(rec, kws)
            if hits and quotes:
                scored.append({
                    "id": rid, "core": rec.get("_core", ""), "year": year_of(rec),
                    "title": (rec.get("title") or "").strip(),
                    "hits": hits, "quotes": quotes, "matched": matched,
                    "cites": rec.get("citationCount") or 0,
                })
        scored.sort(key=lambda r: (-r["hits"], -int(r["cites"] or 0)))
        findings[t["id"]] = scored[:6]

    # --- write the machine-readable pass record
    jpath = os.path.join(RESEARCH, f"pass-{n:03d}.json")
    with open(jpath, "w", encoding="utf-8") as fh:
        json.dump({
            "pass": n, "date": today, "scope": args.scope, "rationale": rationale,
            "targets": [t["id"] for t in targets],
            "queries": {"cached": len(cached_plan), "fetched": len(fetched),
                        "failed": [list(f) for f in failed],
                        "deferred": [list(d) for d in deferred]},
            "spend_this_pass_usd": round(len(fetched) * 0.05 * args.limit / 20, 4),
            "spend_total": spend,
            "findings": findings,
        }, fh, indent=2)
        fh.write("\n")

    # --- write the human-readable pass record
    mpath = os.path.join(RESEARCH, f"pass-{n:03d}.md")
    with open(mpath, "w", encoding="utf-8") as fh:
        w = fh.write
        w(f"# Research pass {n:03d} — {today}\n\n")
        w(f"- **scope:** `{args.scope}` ({rationale})\n")
        w(f"- **targets:** {', '.join(t['id'] for t in targets)}\n")
        w(f"- **searches:** {len(cached_plan)} cache hits, {len(fetched)} new, "
          f"{len(failed)} failed, {len(deferred)} deferred\n")
        w(f"- **cost this pass:** ${len(fetched) * 0.05 * args.limit / 20:.2f}\n")
        w(f"- **cumulative:** {spend['searches']} searches, ${spend['usd']:.2f}, "
          f"{spend['searches'] * 100 // TEAM_BUDGET_SEARCHES}% of the "
          f"{TEAM_BUDGET_SEARCHES}-search team budget\n\n")
        if failed:
            w("## Failed searches\n\n")
            for tid, core, q, err in failed:
                w(f"- `{core}` {q} — {err}\n")
            w("\n")
        if deferred:
            w("## Deferred to a later pass (hit `--max-new`)\n\n")
            for tid, core, q in deferred:
                w(f"- [{tid}] `{core}` {q}\n")
            w("\n")
        w("## Candidate evidence\n\n")
        w("Term-overlap matches that carry a measured number. These are "
          "*candidates*: the agent applying this pass judges them, and only "
          "quotes that name an assay become evidence.\n\n")
        for t in targets:
            w(f"### {t['id']} — {t['claim']}\n\n")
            rows = findings.get(t["id"], [])
            if not rows:
                w("No cached record matched with a measured number. Either the "
                  "terms are wrong or this needs a new search.\n\n")
                continue
            for r in rows:
                w(f"- **{r['id']}** ({r['year']}, {r['cites']} cites, "
                  f"{r['hits']} keyword hits: {', '.join(r['matched'][:8])}) — "
                  f"{r['title']}\n")
                for q in r["quotes"]:
                    w(f"  - > {q}\n")
            w("\n")
        w("## Proposed updates\n\n")
        w("The agent driving this pass fills this in and applies it, then "
          "records the move in each theory's history with this pass id.\n\n")
        w("| Target | Proposed change | Justified by |\n|---|---|---|\n")
        for t in targets:
            w(f"| {t['id']} | _pending_ | _pending_ |\n")
        w("\n")

    print(f"\nwrote {os.path.relpath(mpath, HERE)} and "
          f"{os.path.relpath(jpath, HERE)}")
    print(f"spend: +${len(fetched) * 0.05 * args.limit / 20:.2f} this pass, "
          f"${spend['usd']:.2f} total ({spend['searches']}/{TEAM_BUDGET_SEARCHES} searches)")
    if failed:
        print(f"WARNING: {len(failed)} search(es) failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
