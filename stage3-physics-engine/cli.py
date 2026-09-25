#!/usr/bin/env python3
"""
CLI du moteur physique vulgarisé — Stage 3 (Quark & Cosmos).

Usage :
  python3 cli.py list
  python3 cli.py generate <concept> [--difficulty N] [--out path.json]
  python3 cli.py generate-all [--difficulties 1 2 3] [--out-dir levels/]
  python3 cli.py validate <path.json>   # lit aussi meta/<nom>.meta.json (must_contact)
  python3 cli.py solve <path.json> [--max N]
  python3 cli.py report [--difficulties 1 2 3] [--concepts ...] [--out-dir reports/]
"""
import argparse
import json
import sys

from engine.generator import make_level, ALL_CONCEPTS
from engine.validator import validate, solve
from engine.export import write_level, read_level
from engine.report import build_report, write_report


def _stars_line(meta):
    """Part des lancers valides à >=1/>=2/3 étoiles, mesurée vs cible."""
    sp = meta.get("star_profile")
    if not sp:
        return ""
    got, tgt = sp["shares"], sp["target_shares"]
    return "  étoiles " + " ".join(
        f"{k}★ {got[k]:.0%}/{tgt[k]:.0%}" for k in ("1", "2", "3")
    ) + f"  ({sp['distinct_paths']} chemins)"


def cmd_list(args):
    print("Concepts disponibles (monde Quantique) :")
    for c in ALL_CONCEPTS:
        print(f"  - {c}")


def cmd_generate(args):
    level = make_level(args.concept, args.difficulty)
    out = args.out or f"levels/quantique_{args.concept}_{args.difficulty}.json"
    _, meta = write_level(level, out)
    status = "SOLVABLE" if meta["solvable"] else "NON SOLVABLE"
    print(f"[{status}] {out} (max Photons atteignables: {meta['max_photons_reachable']}/{len(level.get('photons', []))})"
          + _stars_line(meta))


def cmd_generate_all(args):
    out_dir = args.out_dir or "levels"
    import os
    os.makedirs(out_dir, exist_ok=True)
    all_ok = True
    for concept in ALL_CONCEPTS:
        for difficulty in args.difficulties:
            level = make_level(concept, difficulty)
            out = f"{out_dir}/quantique_{concept}_{difficulty}.json"
            _, meta = write_level(level, out)
            ok = meta["solvable"] and meta["bypass_solutions"] == 0
            all_ok = all_ok and ok
            print(f"[{'OK' if ok else 'ECHEC':5}] {concept:15} d{difficulty} -> {out}  "
                  f"(tolérance {meta['tolerance']:.0%}, contournements {meta['bypass_solutions']})"
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
        print("Aucune solution trouvée.")
        sys.exit(1)
    print(f"{len(solutions)} solution(s) trouvée(s). Meilleure :")
    best = solutions[0]
    print(f"  params = {best.params}")
    print(f"  Photons collectés = {best.photons} {best.photon_ids}")


def cmd_report(args):
    def progress(e):
        s, t = e["shares"], e["target_shares"]
        flag = "  ⚠ plancher 3★" if e["ceiling"] else ""
        print(f"  {e['concept']:15} diff {e['difficulty']}  "
              + " ".join(f"{k}★ {s[k]:.0%}/{t[k]:.0%}" for k in ("1", "2", "3"))
              + f"  ({e['distinct_paths']} chemins){flag}", flush=True)

    print("Mesuré / cible (part des lancers valides à >= k étoiles) :")
    data = build_report(args.concepts or ALL_CONCEPTS, args.difficulties, progress)
    paths = write_report(data, args.out_dir)
    for kind, path in paths.items():
        print(f"{kind:4} -> {path}")


def main():
    parser = argparse.ArgumentParser(description="Moteur physique vulgarisé — Quark & Cosmos")
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

    p_rep = sub.add_parser("report", help="stats de progression des étoiles + rapport HTML")
    p_rep.add_argument("--difficulties", type=int, nargs="+", default=[1, 2, 3])
    p_rep.add_argument("--concepts", nargs="+", choices=ALL_CONCEPTS, default=None)
    p_rep.add_argument("--out-dir", type=str, default="reports")
    p_rep.set_defaults(func=cmd_report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
