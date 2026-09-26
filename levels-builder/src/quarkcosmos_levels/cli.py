"""
Command line of the Quark & Cosmos level builder.

Usage (from anywhere, after `pip install -e levels-builder`):
  python3 -m quarkcosmos_levels list
  python3 -m quarkcosmos_levels generate <concept> [--difficulty N] [--out path.json]
  python3 -m quarkcosmos_levels generate-all [--difficulties 1 2 3] [--out-dir DIR]
  python3 -m quarkcosmos_levels validate <path.json>   # also reads its meta (must_contact)
  python3 -m quarkcosmos_levels solve <path.json> [--max N]
  python3 -m quarkcosmos_levels report [--difficulties 1 2 3] [--concepts ...] [--out-dir DIR]
  python3 -m quarkcosmos_levels golden [--out-dir DIR]   # reference trajectories for the Kotlin port
  python3 -m quarkcosmos_levels check-codex             # every concept has a Codex line in every language

Defaults: levels go to content/levels/quantique/, metas to levels-builder/meta/,
reports to levels-builder/reports/, goldens to levels-builder/tests/golden/.
`qc-levels` is the same command as an installed script.
"""
import argparse
import json
import os
import sys

from . import paths
from .concepts.generator import ALL_CONCEPTS, make_level
from .export.codex import missing_codex_lines
from .export.golden import write_goldens
from .export.levels import read_level, write_level
from .export.report import build_report, write_report
from .solver.validator import solve, validate


def _stars_line(meta):
    """Share of valid launches with >=1/>=2/3 stars, measured vs target."""
    sp = meta.get("star_profile")
    if not sp:
        return ""
    got, tgt = sp["shares"], sp["target_shares"]
    return "  stars " + " ".join(
        f"{k}★ {got[k]:.0%}/{tgt[k]:.0%}" for k in ("1", "2", "3")
    ) + f"  ({sp['distinct_paths']} paths)"


def cmd_list(args):
    print("Available concepts (Quantum world):")
    for c in ALL_CONCEPTS:
        print(f"  - {c}")


def cmd_generate(args):
    level = make_level(args.concept, args.difficulty)
    out = args.out or os.path.join(paths.LEVELS_DIR, f"quantique_{args.concept}_{args.difficulty}.json")
    _, meta = write_level(level, out)
    status = "SOLVABLE" if meta["solvable"] else "UNSOLVABLE"
    print(f"[{status}] {out} (max reachable Photons: {meta['max_photons_reachable']}/{len(level.get('photons', []))})"
          + _stars_line(meta))


def cmd_generate_all(args):
    out_dir = args.out_dir or str(paths.LEVELS_DIR)
    os.makedirs(out_dir, exist_ok=True)
    all_ok = True
    for concept in ALL_CONCEPTS:
        for difficulty in args.difficulties:
            level = make_level(concept, difficulty)
            out = os.path.join(out_dir, f"quantique_{concept}_{difficulty}.json")
            _, meta = write_level(level, out)
            ok = meta["solvable"] and meta["bypass_solutions"] == 0
            all_ok = all_ok and ok
            print(f"[{'OK' if ok else 'FAIL':4}] {concept:15} d{difficulty} -> {os.path.relpath(out)}  "
                  f"(tolerance {meta['tolerance']:.0%}, bypasses {meta['bypass_solutions']})"
                  + _stars_line(meta), flush=True)
    sys.exit(0 if all_ok else 1)


def cmd_validate(args):
    level = read_level(args.path)
    report = validate(level)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(0 if report["solvable"] else 1)


def cmd_solve(args):
    level = read_level(args.path)
    solutions = solve(level, max_solutions=args.max)
    if not solutions:
        print("No solution found.")
        sys.exit(1)
    print(f"{len(solutions)} solution(s) found. Best:")
    best = solutions[0]
    print(f"  params = {best.params}")
    print(f"  Photons collected = {best.photons} {best.photon_ids}")


def cmd_report(args):
    def progress(e):
        s, t = e["shares"], e["target_shares"]
        flag = "  ⚠ 3★ ceiling" if e["ceiling"] else ""
        print(f"  {e['concept']:15} diff {e['difficulty']}  "
              + " ".join(f"{k}★ {s[k]:.0%}/{t[k]:.0%}" for k in ("1", "2", "3"))
              + f"  ({e['distinct_paths']} paths){flag}", flush=True)

    print("Measured / target (share of valid launches with >= k stars):")
    data = build_report(args.concepts or ALL_CONCEPTS, args.difficulties, progress)
    written = write_report(data, args.out_dir or str(paths.REPORTS_DIR))
    for kind, path in written.items():
        print(f"{kind:4} -> {os.path.relpath(path)}")


def cmd_golden(args):
    for path in write_goldens(args.levels_dir or str(paths.LEVELS_DIR), args.out_dir or str(paths.GOLDEN_DIR)):
        print(f"golden -> {os.path.relpath(path)}")


def cmd_check_codex(args):
    missing = missing_codex_lines(ALL_CONCEPTS)
    for lang, concept in missing:
        print(f"missing Codex line: {lang}/{concept}")
    print("Codex complete." if not missing else f"{len(missing)} missing line(s).")
    sys.exit(0 if not missing else 1)


def main():
    parser = argparse.ArgumentParser(prog="qc-levels", description="Quark & Cosmos level builder")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list").set_defaults(func=cmd_list)

    p_gen = sub.add_parser("generate")
    p_gen.add_argument("concept", choices=ALL_CONCEPTS)
    p_gen.add_argument("--difficulty", type=int, default=1)
    p_gen.add_argument("--out", type=str, default=None)
    p_gen.set_defaults(func=cmd_generate)

    p_all = sub.add_parser("generate-all")
    p_all.add_argument("--out-dir", type=str, default=None)
    p_all.add_argument("--difficulties", type=int, nargs="+", default=[1, 2, 3])
    p_all.set_defaults(func=cmd_generate_all)

    p_val = sub.add_parser("validate")
    p_val.add_argument("path")
    p_val.set_defaults(func=cmd_validate)

    p_solve = sub.add_parser("solve")
    p_solve.add_argument("path")
    p_solve.add_argument("--max", type=int, default=200)
    p_solve.set_defaults(func=cmd_solve)

    p_rep = sub.add_parser("report", help="star progression stats + HTML report")
    p_rep.add_argument("--difficulties", type=int, nargs="+", default=[1, 2, 3])
    p_rep.add_argument("--concepts", nargs="+", choices=ALL_CONCEPTS, default=None)
    p_rep.add_argument("--out-dir", type=str, default=None)
    p_rep.set_defaults(func=cmd_report)

    p_gold = sub.add_parser("golden", help="golden trajectories for the Kotlin runtime")
    p_gold.add_argument("--levels-dir", type=str, default=None)
    p_gold.add_argument("--out-dir", type=str, default=None)
    p_gold.set_defaults(func=cmd_golden)

    sub.add_parser("check-codex", help="check the Codex lines exist in every language").set_defaults(
        func=cmd_check_codex)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
