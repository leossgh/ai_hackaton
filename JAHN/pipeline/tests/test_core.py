"""Contract tests that need neither abguard nor the organiser data: they prove the modules are swappable."""
import json
import sys
import textwrap

import polars as pl
import pytest

from abpipe import config, registry, runner, schema
from abpipe.aggregators.ranking import Borda

PLUGIN = textwrap.dedent("""
    import polars as pl
    from abpipe.base import Filter, Generator, Scorer
    from abpipe.registry import register

    @register("generator", "t_gen")
    class TGen(Generator):
        \"\"\"toy sequences of increasing length\"\"\"
        def generate(self, n, seed, ctx):
            return pl.DataFrame([dict(sequence_id=f"t{seed}_{i}", kind="paired", heavy_sequence="E" * (10 + i),
                                      light_sequence="D" * 5, design_description="toy") for i in range(n)])

    @register("filter", "t_min_len")
    class TMinLen(Filter):
        def __init__(self, min_len: int = 12):
            self.min_len = min_len
        def check(self, df, ctx):
            return df.select("sequence_id", reason=pl.when(pl.col("heavy_sequence").str.len_chars() < self.min_len)
                             .then(pl.lit("too short")).otherwise(None))

    @register("filter", "t_bad")
    class TBad(Filter):
        def check(self, df, ctx):
            return df.head(1).select("sequence_id", reason=pl.lit(None, dtype=pl.String))

    @register("scorer", "t_len")
    class TLen(Scorer):
        outputs = {"score__len": "higher"}
        def score(self, df, ctx):
            return df.select("sequence_id", score__len=pl.col("heavy_sequence").str.len_chars().cast(pl.Float64))

    @register("scorer", "t_mod3")
    class TMod3(Scorer):
        outputs = {"score__mod3": "higher"}
        def score(self, df, ctx):
            return df.select("sequence_id", score__mod3=(pl.col("heavy_sequence").str.len_chars() % 3).cast(pl.Float64))
""")


@pytest.fixture(scope="module")
def plugin(tmp_path_factory):
    d = tmp_path_factory.mktemp("plugin")
    (d / "abpipe_test_plugin.py").write_text(PLUGIN)
    sys.path.insert(0, str(d))
    yield "abpipe_test_plugin"
    sys.path.remove(str(d))


def cfg(tmp_path, plugin, *, scorer="t_len", agg="borda", on_fail="drop", name="t", filt="t_min_len", agg_params=None):
    return config.load({
        "run": {"name": name, "out_dir": str(tmp_path / "runs"), "seed": 1},
        "data_dir": str(tmp_path), "repo_root": str(tmp_path), "plugins": [plugin],
        "generators": [{"name": "t_gen", "n": 8}],
        "filters": [{"name": filt, "on_fail": on_fail}],
        "scorers": [{"name": scorer}],
        "aggregator": {"name": agg, "params": agg_params or {}}})


def ranked_ids(c):
    return pl.read_parquet(c.out_dir / c.name / "04_ranked.parquet")["sequence_id"].to_list()


def test_schema_rejects_duplicates_and_bad_kind():
    ok = pl.DataFrame({"sequence_id": ["a", "b"], "kind": ["paired", "vhh"], "heavy_sequence": ["EV", "EV"],
                       "light_sequence": ["D", None], "design_description": ["x", "y"]})
    schema.validate(ok)
    with pytest.raises(schema.SchemaError, match="duplicate"):
        schema.validate(pl.concat([ok, ok]))
    with pytest.raises(schema.SchemaError, match="kind"):
        schema.validate(ok.with_columns(kind=pl.lit("fab")))
    with pytest.raises(schema.SchemaError, match="missing"):
        schema.validate(ok.drop("light_sequence"))


def test_end_to_end_with_plugin_modules(tmp_path, plugin):
    c = cfg(tmp_path, plugin)
    man = runner.run(c, log=lambda m: None)
    rd = c.out_dir / c.name
    ranked = pl.read_parquet(rd / "04_ranked.parquet")
    assert ranked["rank"].to_list() == list(range(1, ranked.height + 1))
    assert ranked.height == 6                                     # lengths 10 and 11 were filtered out
    rej = pl.read_parquet(rd / "02_rejections.parquet")
    assert rej.height == 2 and set(rej["reason"]) == {"too short"} and set(rej["module"]) == {"t_min_len"}
    assert ranked["sequence_id"][0] == "t1_7"                     # longest wins under score__len
    assert set(man["stages"]) == {"generate", "filter", "score", "rank"}
    assert man["stages"]["filter"]["rejections"]["t_min_len"]["count"] == 2
    assert (rd / "ranked.csv").exists() and man["totals"]["cost_usd"] == 0


def test_swapping_a_scorer_by_config_changes_the_ranking(tmp_path, plugin):
    a, b = cfg(tmp_path, plugin, scorer="t_len", name="a"), cfg(tmp_path, plugin, scorer="t_mod3", name="b")
    runner.run(a, log=lambda m: None); runner.run(b, log=lambda m: None)
    assert set(ranked_ids(a)) == set(ranked_ids(b)) and ranked_ids(a) != ranked_ids(b)
    cols = pl.read_parquet(b.out_dir / "b" / "04_ranked.parquet").columns
    assert "score__mod3" in cols and "score__len" not in cols


@pytest.mark.parametrize("agg", ["borda", "weighted_sum", "pareto"])
def test_every_aggregator_returns_a_permutation(tmp_path, plugin, agg):
    c = cfg(tmp_path, plugin, agg=agg, name=agg)
    c.scorers = config.load({**c.raw, "scorers": [{"name": "t_len"}, {"name": "t_mod3"}]}).scorers
    runner.run(c, log=lambda m: None)
    ranked = pl.read_parquet(c.out_dir / agg / "04_ranked.parquet")
    assert sorted(ranked["rank"].to_list()) == list(range(1, ranked.height + 1))
    assert {"rank_score", "rank__len", "rank__mod3"} <= set(ranked.columns)


def test_flag_mode_keeps_rows_and_marks_them(tmp_path, plugin):
    c = cfg(tmp_path, plugin, on_fail="flag", name="flag")
    runner.run(c, log=lambda m: None)
    ranked = pl.read_parquet(c.out_dir / "flag" / "04_ranked.parquet")
    assert ranked.height == 8
    assert ranked.filter(pl.col("flag__t_min_len") == "too short").height == 2


def test_second_run_hits_the_cache(tmp_path, plugin):
    c = cfg(tmp_path, plugin, name="cache")
    runner.run(c, log=lambda m: None)
    man = runner.run(c, log=lambda m: None)
    for stage in ("generate", "filter", "score"):
        assert all(m["cached"] for m in man["stages"][stage]["modules"]), stage


def test_helpful_errors(tmp_path, plugin):
    with pytest.raises(KeyError, match="available"):
        registry.get("scorer", "does_not_exist")
    with pytest.raises(config.ConfigError, match="unknown top-level"):
        config.load({"data_dir": "x", "bogus": 1, "generators": [{"name": "g", "n": 1}], "aggregator": {"name": "borda"}})
    with pytest.raises(config.ConfigError, match="on_fail"):
        config.load({"data_dir": "x", "generators": [{"name": "g", "n": 1}], "filters": [{"name": "f", "on_fail": "maybe"}],
                     "aggregator": {"name": "borda"}})
    bad = cfg(tmp_path, plugin)
    bad.filters[0].params = {"nope": 1}
    with pytest.raises(TypeError, match="unexpected"):
        runner.run(bad, log=lambda m: None)


def test_filter_that_breaks_the_contract_is_caught(tmp_path, plugin):
    with pytest.raises(ValueError, match="exactly one row"):
        runner.run(cfg(tmp_path, plugin, filt="t_bad", name="bad"), log=lambda m: None)


def test_missing_scores_rank_worst():
    df = pl.DataFrame({"sequence_id": ["a", "b", "c"], "score__x": [1.0, None, 3.0]})
    out = Borda().combine(df, {"score__x": "higher"}, None)
    assert out["sequence_id"].to_list() == ["c", "a", "b"]


def test_distance_uses_hamming_only_when_it_is_exact():
    import random
    from abpipe import distance as dist
    assert dist.distance("ABCD", "BCDA", "levenshtein") == 2          # a shifted loop is 2 edits ...
    assert dist.distance("ABCD", "BCDA", "auto") == 4                 # ... but 4 substituted positions
    assert dist.distance("ABCD", "ABC", "auto") == 1                  # different lengths fall back to Levenshtein
    assert dist.distance("ABCD", "ABC", "hamming") is None
    rng = random.Random(0)
    for _ in range(500):
        a = "".join(rng.choices("ACDEFGHIK", k=12)); b = "".join(rng.choices("ACDEFGHIK", k=12))
        ham, lev = dist.distance(a, b, "hamming"), dist.distance(a, b, "levenshtein")
        assert ham >= lev                                              # Hamming never underestimates
        if ham <= 2:
            assert ham == lev                                          # and is exact for 0-2 substitutions
    with pytest.raises(ValueError, match="metric"):
        dist.check_metric("euclid")


def test_nearest_picks_the_right_metric_per_length_bucket():
    from abpipe.distance import nearest
    buckets = {4: (["AAAA", "ABCD"], ["x", "y"]), 3: (["BCD"], ["z"])}
    assert nearest("BCDA", buckets, "auto") == (1, "z")              # Levenshtein to the shorter bucket wins
    assert nearest("BCDA", buckets, "hamming")[1] in ("x", "y")      # hamming ignores other lengths
    assert nearest("BCDA", {}, "auto") is None


def test_parent_distance_metric_and_fallback(tmp_path):
    from abpipe.base import Context, Parent
    from abpipe.registry import get
    parent = Parent(id="p", heavy="ABCDEFGH", light="IJKL", cdrh3="X", window="CD", window_start=2)
    ctx = Context(data_dir=tmp_path, repo_root=tmp_path, run_dir=tmp_path, cache_dir=tmp_path, parent=parent)
    df = pl.DataFrame({"sequence_id": ["sub", "shift", "short"], "kind": ["paired"] * 3,
                       "heavy_sequence": ["ABXDEFGH", "BCDEFGHA", "ABCDEFG"],
                       "light_sequence": ["IJKL", "IJKL", "IJKL"], "design_description": ["d"] * 3})
    auto = dict(get("scorer", "parent_distance")().score(df, ctx).iter_rows())
    lev = dict(get("scorer", "parent_distance")(metric="levenshtein").score(df, ctx).iter_rows())
    assert auto["sub"] == lev["sub"] == 1                             # substitution-only: identical
    assert auto["shift"] == 8 and lev["shift"] == 2                   # shifted heavy chain: Hamming counts positions
    assert auto["short"] == lev["short"] == 1                         # different length: auto falls back
    with pytest.raises(ValueError, match="hamming"):
        get("scorer", "parent_distance")(metric="hamming").score(df, ctx)
