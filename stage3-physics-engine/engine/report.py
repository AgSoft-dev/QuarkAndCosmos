"""
Rapport de progression de difficulté (cf. stars.py) : pour chaque concept
et chaque difficulté, génère le niveau puis écrit
  - <out>/difficulty_report.json : toutes les stats (à relire / comparer),
  - <out>/difficulty_report.csv  : une ligne par niveau × difficulté,
  - <out>/difficulty_report.html : courbes de progression + mini-carte de
    chaque niveau (éventail des chemins valides coloré par nb d'étoiles).
Le HTML charge Plotly depuis un CDN ; les données sont embarquées.
"""
import csv
import json
import os

from .generator import make_level
from .stars import PHOTONS_PER_LEVEL, sigma_for, target_shares, trace, _shares
from .validator import validate

# Écart (part de rayons) au-delà duquel la part 3 étoiles est jugée
# "bloquée" au-dessus de la cible : les chemins valides du niveau sont trop
# uniformes pour que des Photons les départagent à cette difficulté.
CEILING_GAP = 0.05
# Nombre max de chemins valides dessinés par mini-carte, et un point sur
# TRAIL_STRIDE conservé par chemin (poids du HTML).
MAX_DRAWN_PATHS = 60
TRAIL_STRIDE = 4


def _sample(paths, photons):
    """Chemins à dessiner : échantillon régulier + au moins un chemin par
    nombre d'étoiles présent, triés pour dessiner les 3 étoiles au-dessus."""
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
