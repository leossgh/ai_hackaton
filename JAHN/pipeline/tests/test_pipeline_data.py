"""Tests against the real abguard checks and organiser data (skipped when they are not present)."""
import polars as pl
import pytest

from abpipe import config, registry, runner
from abpipe.generators.cdrh3_mutagenesis import Cdrh3Mutagenesis

pytestmark = pytest.mark.needs_data


@pytest.fixture(scope="module")
def baseline(pipeline_dir, data_dir, repo_root, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("run")
    cfg = config.load(pipeline_dir / "configs" / "baseline.yaml")
    cfg.data_dir, cfg.repo_root = data_dir, repo_root
    cfg.out_dir, cfg.cache_dir = tmp / "runs", tmp / "cache"
    cfg.generators[0].n = 200
    return cfg


def _row(sid, heavy, light):
    return {"sequence_id": sid, "kind": "paired", "heavy_sequence": heavy, "light_sequence": light, "design_description": "control"}


def _apply(name, df, ctx, **params):
    res = registry.get("filter", name)(**params).check(df, ctx)
    return dict(zip(res["sequence_id"].to_list(), res["reason"].to_list())), res


def test_parent_is_trastuzumab(baseline):
    p = runner.build_context(baseline).parent
    assert p.cdrh3 == "SRWGGDGFYAMDY" and p.window == "WGGDGFYAMD"
    assert p.heavy[p.window_start:p.window_start + 10] == p.window


def test_controls_are_rejected_for_the_right_reasons(baseline):
    ctx = runner.build_context(baseline)
    p, s = ctx.parent, ctx.parent.window_start
    sub3 = p.heavy[:s] + "KKDDGFYAMD" + p.heavy[s + 10:]           # 3 substitutions in the window
    df = pl.DataFrame([_row("wt", p.heavy, p.light), _row("sub3", sub3, p.light)])
    assert all(v is None for v in _apply("framework_integrity", df, ctx)[0].values())
    assert all(v is None for v in _apply("abguard_hard", df, ctx)[0].values())
    reasons, _ = _apply("track_check", df, ctx)
    assert reasons["wt"] and "CDRH3" in reasons["wt"]               # identical to trastuzumab
    assert reasons["sub3"] and "CDRH3" in reasons["sub3"]           # too close to trastuzumab / known CDRH3s


def test_framework_and_liability_filters_catch_what_they_should(baseline):
    ctx = runner.build_context(baseline)
    p, s = ctx.parent, ctx.parent.window_start
    framework_hit = p.heavy[:5] + "W" + p.heavy[6:]                  # change outside the window
    ng = p.heavy[:s] + "N" + p.heavy[s + 1:]                         # W->N makes an NG deamidation motif
    df = pl.DataFrame([_row("wt", p.heavy, p.light), _row("fw", framework_hit, p.light), _row("ng", ng, p.light)])
    assert _apply("framework_integrity", df, ctx)[0]["fw"]
    assert _apply("framework_integrity", df, ctx)[0]["wt"] is None
    liab, _ = _apply("new_liabilities", df, ctx)
    assert liab["wt"] is None, "the parent must never be rejected for liabilities it already has"
    assert liab["ng"] and "introduces" in liab["ng"]


def test_generator_output_passes_the_cheap_filters_and_some_pass_everything(baseline):
    ctx = runner.build_context(baseline)
    df = Cdrh3Mutagenesis(min_subs=5, max_subs=6).generate(60, 7, ctx)
    assert all(v is None for v in _apply("framework_integrity", df, ctx)[0].values())
    ok = sum(v is None for v in _apply("abguard_hard", df, ctx)[0].values())
    assert ok == 60
    passed = sum(v is None for v in _apply("track_check", df, ctx)[0].values())
    assert passed >= 1


def test_baseline_pipeline_end_to_end(baseline):
    man = runner.run(baseline, log=lambda m: None)
    rd = baseline.out_dir / baseline.name
    ranked = pl.read_parquet(rd / "04_ranked.parquet")
    assert ranked.height > 0 and ranked["rank"].to_list() == list(range(1, ranked.height + 1))
    assert (ranked["info__track"].is_not_null()).all()
    assert {"score__parent_distance", "score__binder_distance", "score__neighbor_binder_frac"} <= set(ranked.columns)
    assert man["stages"]["generate"]["rows_out"] == 200


def test_swapping_aggregator_and_generator_by_yaml_text_only(pipeline_dir, data_dir, repo_root, tmp_path):
    text = (pipeline_dir / "configs" / "baseline.yaml").read_text()
    swapped = text.replace("aggregator: {name: borda}", "aggregator: {name: pareto}").replace("prior: uniform", "prior: facs")
    assert swapped != text
    ids = {}
    for tag, body in (("a", text), ("b", swapped)):
        p = tmp_path / f"{tag}.yaml"; p.write_text(body)
        c = config.load(p)
        c.data_dir, c.repo_root, c.out_dir, c.cache_dir = data_dir, repo_root, tmp_path / "runs", tmp_path / "cache"
        c.name, c.generators[0].n = tag, 120
        runner.run(c, log=lambda m: None)
        ids[tag] = pl.read_parquet(c.out_dir / tag / "04_ranked.parquet")
    assert ids["a"].height > 0 and ids["b"].height > 0
    assert "rank__parent_distance" in ids["b"].columns


def test_fast_levenshtein_equals_the_scripts_python_dp(repo_root):
    """The drop-in distance must give identical numbers to the team's pure-Python implementation."""
    import random, sys
    scripts = next(p for p in (repo_root / "NICCOLO" / "scripts", repo_root / "scripts") if (p / "_track_common.py").exists())
    sys.path.insert(0, str(scripts))
    import _track_common
    from rapidfuzz.distance import Levenshtein
    rng, aa = random.Random(0), "ACDEFGHIKLMNPQRSTVWY"
    for _ in range(1500):
        a = "".join(rng.choices(aa, k=rng.randint(0, 40)))
        b = "".join(rng.choices(aa, k=rng.randint(0, 40)))
        assert _track_common.levenshtein(a, b) == Levenshtein.distance(a, b), (a, b)


def test_fast_track_check_gives_the_same_verdicts_as_the_stock_scripts(baseline):
    """Run both modes on the same small table: reasons, tracks and distances must be identical."""
    ctx = runner.build_context(baseline)
    p, s = ctx.parent, ctx.parent.window_start
    sub3 = p.heavy[:s] + "KKDDGFYAMD" + p.heavy[s + 10:]
    gen = Cdrh3Mutagenesis(min_subs=3, max_subs=6).generate(4, 5, ctx)
    df = pl.concat([pl.DataFrame([_row("wt", p.heavy, p.light), _row("sub3", sub3, p.light)]), gen.select(
        "sequence_id", "kind", "heavy_sequence", "light_sequence", "design_description")])
    import re
    fast = registry.get("filter", "track_check")(fast_distance=True).check(df, ctx).sort("sequence_id")
    stock = registry.get("filter", "track_check")(fast_distance=False).check(df, ctx).sort("sequence_id")
    # abguard names an arbitrary one of several equally near known CDRH3s (the stock script does this
    # against itself run to run), so mask the named sequence and compare everything else exactly.
    mask = lambda d: d.with_columns(pl.col("reason").map_elements(
        lambda s: re.sub(r"\([A-Z]+\)", "(<nearest>)", s) if s else s, return_dtype=pl.String))
    assert mask(fast).equals(mask(stock)), f"fast and stock verdicts differ:\n{fast}\n{stock}"
    assert fast["info__track"].to_list() == stock["info__track"].to_list()
    assert fast["info__cdrh3_min_distance"].to_list() == stock["info__cdrh3_min_distance"].to_list()


def test_hamming_scorer_never_underestimates_and_runs_on_real_candidates(baseline):
    ctx = runner.build_context(baseline)
    df = Cdrh3Mutagenesis(min_subs=4, max_subs=8).generate(120, 3, ctx)
    ham = registry.get("scorer", "nearest_known_binder")(metric="hamming").score(df, ctx)
    lev = registry.get("scorer", "nearest_known_binder")(metric="levenshtein").score(df, ctx)
    assert (ham["score__binder_distance"] >= lev["score__binder_distance"]).all()


def test_neighbour_fraction_does_not_depend_on_reference_order(baseline, monkeypatch):
    """Many FACS variants tie at the k-th distance; the score must not depend on which ones come first."""
    from abpipe import data
    ctx = runner.build_context(baseline)
    df = Cdrh3Mutagenesis(min_subs=4, max_subs=6).generate(60, 9, ctx)
    scorer = registry.get("scorer", "nearest_known_binder")
    a = scorer().score(df, ctx)
    real = data.facs_table
    monkeypatch.setattr(data, "facs_table", lambda c: real(c).sample(fraction=1.0, shuffle=True, seed=123))
    b = scorer().score(df, ctx)
    assert a.equals(b)
