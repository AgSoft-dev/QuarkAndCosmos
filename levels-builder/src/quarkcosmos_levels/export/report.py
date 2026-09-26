"""
Difficulty progression report (see stars.py): for each concept and each
difficulty, generate the level then write
  - <out>/difficulty_report.json: every stat (to review / compare),
  - <out>/difficulty_report.csv: one row per level × difficulty,
  - <out>/difficulty_report.html: progression curves + a mini-map of each
    level (fan of valid paths coloured by star count).
The HTML loads Plotly from a CDN; the data is embedded.
"""
import csv
import json
import os

from ..concepts.generator import make_level
from ..solver.stars import PHOTONS_PER_LEVEL, sigma_for, target_shares, trace, _shares
from ..solver.validator import validate

# Gap (share of rays) beyond which the 3-star share counts as "stuck" above
# target: the level's valid paths are too uniform for Photons to tell them
# apart at this difficulty.
CEILING_GAP = 0.05
# Max number of valid paths drawn per mini-map, and one point out of
# TRAIL_STRIDE kept per path (HTML weight).
MAX_DRAWN_PATHS = 60
TRAIL_STRIDE = 4


def _sample(paths, photons):
    """Paths to draw: a regular sample + at least one path per star count
    present, sorted so that 3-star paths are drawn on top."""
    scored = [(sum(1 for ph in photons if p.collects(ph)), p) for p in paths]
    picked = {id(p): (s, p) for s, p in scored[::max(1, len(scored) // MAX_DRAWN_PATHS)]}
    for stars in range(PHOTONS_PER_LEVEL + 1):
        for s, p in scored:
            if s == stars:
                picked.setdefault(id(p), (s, p))
                break
    out = []
    for s, p in sorted(picked.values(), key=lambda sp: sp[0]):
        pts = p.trail[::TRAIL_STRIDE] + [p.trail[-1]]
        out.append({
            "stars": s,
            "weight": p.weight,
            "params": p.rays[0],
            "x": [round(q[0], 3) for q in pts],
            "y": [round(q[1], 3) for q in pts],
        })
    return out


def _routes(paths):
    """Valid routes (obstacle:event sequence) and their share of rays."""
    n = sum(p.weight for p in paths) or 1
    counts = {}
    for p in paths:
        key = " → ".join(f"{o}:{e}" for o, e in p.route) or "(no contact)"
        counts[key] = counts.get(key, 0) + p.weight
    return [{"route": k, "share": round(v / n, 4)} for k, v in sorted(counts.items(), key=lambda kv: -kv[1])]


def level_entry(concept: str, difficulty: int) -> dict:
    level = make_level(concept, difficulty)
    report = validate(level)
    total, paths = trace(level)
    shares = _shares(paths, level["photons"])
    targets = target_shares(difficulty)
    gap3 = shares[3] - targets[3]
    return {
        "id": level["id"],
        "concept": concept,
        "difficulty": difficulty,
        "sigma": sigma_for(difficulty),
        "solvable": report["solvable"],
        "tolerance": report["tolerance"],
        "bypass_solutions": report["bypass_solutions"],
        "routes": _routes(paths),
        "rays": total,
        "valid_rays": sum(p.weight for p in paths),
        "distinct_paths": len(paths),
        "shares": {str(k): round(v, 4) for k, v in shares.items()},
        "target_shares": {str(k): v for k, v in targets.items()},
        "gap_3_stars": round(gap3, 4),
        "ceiling": gap3 > CEILING_GAP,
        "moving_photons": sum(1 for ph in level["photons"] if "motion" in ph),
        "geometry": {
            "launcher": level["launcher"],
            "target": level["target"],
            "obstacles": level["obstacles"],
            "photons": level["photons"],
        },
        "paths": _sample(paths, level["photons"]),
    }


def build_report(concepts, difficulties, progress=None) -> dict:
    entries = []
    for concept in concepts:
        for d in difficulties:
            entry = level_entry(concept, d)
            entries.append(entry)
            if progress:
                progress(entry)
    return {
        "difficulties": list(difficulties),
        "sigma": {str(d): sigma_for(d) for d in difficulties},
        "ceiling_gap": CEILING_GAP,
        "levels": entries,
    }


CSV_FIELDS = [
    "id", "concept", "difficulty", "sigma", "tolerance", "rays", "valid_rays",
    "distinct_paths", "share_1", "share_2", "share_3", "target_1", "target_2",
    "target_3", "gap_3_stars", "ceiling", "moving_photons",
]


def write_report(data: dict, out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    paths = {
        "json": os.path.join(out_dir, "difficulty_report.json"),
        "csv": os.path.join(out_dir, "difficulty_report.csv"),
        "html": os.path.join(out_dir, "difficulty_report.html"),
    }
    with open(paths["json"], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    with open(paths["csv"], "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for e in data["levels"]:
            row = {k: e[k] for k in CSV_FIELDS if k in e}
            for k in range(1, PHOTONS_PER_LEVEL + 1):
                row[f"share_{k}"] = e["shares"][str(k)]
                row[f"target_{k}"] = e["target_shares"][str(k)]
            w.writerow(row)
    template = open(os.path.join(os.path.dirname(__file__), "report_template.html"), encoding="utf-8").read()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    with open(paths["html"], "w", encoding="utf-8") as f:
        f.write(template.replace("/*__DATA__*/null", payload))
    return paths
