"""abpipe list | validate CONFIG | run CONFIG | stage STAGE CONFIG | iterate CONFIG"""
from __future__ import annotations

import argparse
import dataclasses
import sys
from pathlib import Path

from abpipe import config as cfgmod
from abpipe import registry, runner


def _load(path: str, args) -> cfgmod.Config:
    cfg = cfgmod.load(path)
    if getattr(args, "name", None):
        cfg.name = args.name
    if getattr(args, "out", None):
        cfg.out_dir = Path(args.out)
        cfg.cache_dir = cfg.out_dir / "_cache"
    if getattr(args, "seed", None) is not None:
        cfg.seed = args.seed
    if getattr(args, "n", None):
        for g in cfg.generators:
            g.n = args.n
    return cfg


def cmd_list(_args) -> int:
    for kind, names in registry.available().items():
        print(f"\n{kind}s")
        for n in names:
            cls = registry.get(kind, n)
            print(f"  {n:<24} {cls.summary()}")
            print(f"  {'':<24} params {cls.signature()}")
    return 0


def cmd_validate(args) -> int:
    cfg = _load(args.config, args)
    registry.load_plugins(cfg.plugins)
    n = 0
    for kind, specs in (("generator", cfg.generators), ("filter", cfg.filters),
                        ("scorer", cfg.scorers), ("aggregator", [cfg.aggregator])):
        for s in specs:
            registry.get(kind, s.name)(**s.params)   # raises on unknown module or parameter
            n += 1
    print(f"OK: {n} modules resolve ({len(cfg.generators)} generator, {len(cfg.filters)} filter, "
          f"{len(cfg.scorers)} scorer, 1 aggregator)")
    return 0


def cmd_run(args) -> int:
    man = runner.run(_load(args.config, args))
    return 1 if man.get("stopped") else 0


def cmd_stage(args) -> int:
    man = runner.run(_load(args.config, args), stages=(args.stage,))
    return 1 if man.get("stopped") else 0


def cmd_iterate(args) -> int:
    from abpipe import iterate
    summary = iterate.run_loop(args.config, rounds=args.rounds, n_select=args.select, out_dir=args.out,
                               seed=args.seed, n=args.n, pool_frac=args.pool_frac, propose_next=args.propose_next)
    return 1 if summary.get("stopped") else 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="abpipe", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="show registered modules and their parameters").set_defaults(fn=cmd_list)
    for name, fn, extra in (("validate", cmd_validate, False), ("run", cmd_run, False), ("stage", cmd_stage, True)):
        sp = sub.add_parser(name)
        if extra:
            sp.add_argument("stage", choices=runner.STAGES)
        sp.add_argument("config")
        sp.add_argument("--out"); sp.add_argument("--name"); sp.add_argument("--seed", type=int)
        sp.add_argument("--n", type=int, help="override n for every generator (smoke tests)")
        sp.set_defaults(fn=fn)
    ip = sub.add_parser("iterate", help="several rounds; each round's best feeds the next generator")
    ip.add_argument("config")
    ip.add_argument("--rounds", type=int, default=3)
    ip.add_argument("--select", type=int, default=60, help="windows kept (and fed forward) per round")
    ip.add_argument("--out", default="runs/loop")
    ip.add_argument("--pool-frac", type=float, default=0.10,
                    help="selection looks only at the best fraction of the ranking (fewer rows are returned rather than padding)")
    ip.add_argument("--seed", type=int)
    ip.add_argument("--n", type=int, help="override n for every generator (smoke tests)")
    ip.add_argument("--propose-next", action="store_true",
                    help="after the last round, also generate and filter the next round's proposals (unscored)")
    ip.set_defaults(fn=cmd_iterate)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
