#!/usr/bin/env python3
"""
CLI du moteur physique vulgarisé — Stage 3 (Quark & Cosmos).

Usage :
  python3 cli.py list
  python3 cli.py generate <concept> [--difficulty N] [--out path.json]
  python3 cli.py generate-all [--out-dir levels/]
  python3 cli.py validate <path.json>
  python3 cli.py solve <path.json> [--max N]
"""
import argparse
import json
import sys

from engine.generator import make_level, ALL_CONCEPTS
from engine.validator import validate, solve
from engine.export import write_level, read_level


def cmd_list(args):
    print("Concepts disponibles (monde Quantique) :")
    for c in ALL_CONCEPTS:
        print(f"  - {c}")


def cmd_generate(args):
    level = make_level(args.concept, args.difficulty)
    out = args.out or f"levels/quantique_{args.concept}_{args.difficulty}.json"
    payload = write_level(level, out)
    status = "SOLVABLE" if payload["solvable"] else "NON SOLVABLE"
    print(f"[{status}] {out} (max Photons atteignables: {payload['max_photons_reachable']}/{len(level.get('photons', []))})")


def cmd_generate_all(args):
    out_dir = args.out_dir or "levels"
    import os
    os.makedirs(out_dir, exist_ok=True)
    all_ok = True
    for concept in ALL_CONCEPTS:
        level = make_level(concept, args.difficulty)
        out = f"{out_dir}/quantique_{concept}_{args.difficulty}.json"
        payload = write_level(level, out)
        status = "OK" if payload["solvable"] else "ECHEC"
        if not payload["solvable"]:
            all_ok = False
        print(f"[{status:5}] {concept:15} -> {out}  (Photons max: {payload['max_photons_reachable']}/{len(level.get('photons', []))})")
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
    p_all.add_argument("--difficulty", type=int, default=1)
    p_all.set_defaults(func=cmd_generate_all)

    p_val = sub.add_parser("validate")
    p_val.add_argument("path")
    p_val.set_defaults(func=cmd_validate)

    p_solve = sub.add_parser("solve")
    p_solve.add_argument("path")
    p_solve.add_argument("--max", type=int, default=200)
    p_solve.set_defaults(func=cmd_solve)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
