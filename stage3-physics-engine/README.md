# Moteur physique vulgarisé — Stage 3

Génère, valide et exporte en JSON les niveaux du monde Quantique : 7 concepts (cf. `CLAUDE.md`) × 3 difficultés. Python ≥ 3.10, aucune dépendance à l'exécution.

Chaque difficulté est une **disposition différente** qui pousse la mécanique plus loin (1 découverte, 2 séquence, 3 enchaînement ; tableau par concept dans le skill `gameplay-mechanics`), pas la même disposition avec d'autres Photons.

```bash
python3 cli.py list                          # concepts disponibles
python3 cli.py generate-all                  # régénère levels/*.json + levels/meta/*.meta.json (7 concepts × 3 difficultés, ~2-3 min)
python3 cli.py validate levels/<niveau>.json # rapport de solvabilité (lit aussi la méta voisine)
python3 cli.py solve levels/<niveau>.json    # meilleure solution

pip install -e ".[dev]" && python3 -m pytest -q
```

## Format d'export (`schema_version` 2)

Chaque niveau est exporté en **deux fichiers** (`engine/export.py`) :

| Fichier | Pour qui | Contenu |
|---|---|---|
| `levels/<nom>.json` | **le jeu** (livré) | `schema_version`, `id`, `scale`, `concept`, `difficulty`, `codex_text`, `launcher`, `target`, `obstacles`, `photons`, `max_wall_bounces` (toujours explicite), `param_space` (plages publiques des dials), `hint.params` (paramètres de la solution de référence, pour l'indice « premier segment » après 5 échecs) |
| `levels/meta/<nom>.meta.json` | outils de dev uniquement | `schema_version`, `id`, `must_contact`, `solvable`, `reference_solution` (avec les ids des Photons collectés), `max_photons_reachable`, `tolerance`, `three_star_tolerance`, `bypass_solutions`, `star_profile` |

`must_contact` ne sert qu'au validateur : il vit dans la méta. `validate`/`solve` lisent le niveau via `read_level`, qui recolle `must_contact` depuis `meta/<nom>.meta.json` ; sans méta, le niveau reste simulable mais les contournements ne sont plus vérifiés (avertissement sur stderr). Le contrat de simulation que le jeu doit reproduire est dans [`docs/physics-spec.md`](../docs/physics-spec.md).

## Ce que garantit un niveau exporté

- **Solvable** : au moins une combinaison de la grille `param_space` atteint la cible.
- **Sans contournement** : chaque niveau déclare `must_contact`, la séquence ordonnée (obstacle, événement) qui définit l'usage de la mécanique (ex : `[["s1", "bounce"], ["s2", "wave"]]`). Tout lancer gagnant qui ne la respecte pas est compté dans `bypass_solutions`, qui doit valoir 0.
- **3 Photons** placés automatiquement (pas à la main, cf. section suivante). Les 3 sont collectables en un seul vol.
- **Tolérance** ≥ 5 % : la part de la grille qui réussit (`tolerance`, `three_star_tolerance` dans la méta). En dessous, le niveau est injouable au doigt.
- **Tap en vol réel** : un tap avant `TAP_MIN_TIME` (0,1 s) n'est pas recherché. Taper au lancer reviendrait à un réglage pré-tir.
- **`schema_version`** en tête des deux fichiers : à incrémenter à chaque changement incompatible du format (v2 : séparation niveau livré / méta).

Les tests vérifient aussi que les JSON commités (niveaux **et** méta) sont identiques à la sortie du générateur, qu'aucun champ de dev n'est livré et qu'il n'y a pas de fichier orphelin. Après toute modification du moteur ou d'un gabarit, relancer `generate-all`.

## Distribution des étoiles et rapport de difficulté

Les Photons sont placés par `engine/stars.py` : un éventail dense de lancers (« lancer de rayons ») mesure tous les lancers valides, et la part qui rapporte au moins *k* étoiles doit suivre une gaussienne tronquée `exp(−k²/2σ²)`. σ baisse avec la difficulté (`SIGMA_BY_DIFFICULTY`), donc la fenêtre 3 étoiles se resserre. Quand les chemins valides se superposent, un Photon peut osciller pour que seul le bon timing le collecte.

```bash
python3 cli.py report                          # difficultés 1 2 3, tous les concepts
python3 cli.py report --concepts tunnel spin --difficulties 1 2 3 4
```

Écrit dans `reports/` :
- `difficulty_report.csv` / `.json` : mesuré vs cible par niveau × difficulté (parts ≥1/≥2/3★, tolérance, nb de chemins distincts, Photons oscillants, écart 3★) ;
- `difficulty_report.html` : courbes de progression par concept, mini-carte de chaque niveau (chemins valides colorés par nb d'étoiles, sélecteur de difficulté, survol = paramètres du lancer) et tableau complet. Plotly est chargé depuis un CDN.

**⚠ plancher 3★** : la part 3 étoiles reste > 5 pts au-dessus de la cible. Les chemins valides du niveau sont trop semblables pour que des Photons les départagent : c'est la géométrie du niveau qu'il faut enrichir (plus de chemins possibles), pas le placement.

Réglages : `SIGMA_BY_DIFFICULTY`, `PHOTON_MOTIONS`, `MOTION_PENALTY`, `TIER_WEIGHTS` dans `engine/stars.py` ; `CEILING_GAP` dans `engine/report.py`.

## Simulation

Pas fixe `DT = 0.01`, 300 pas max, boîte fermée sans gravité. Rebonds « subis » (parois de la boîte + obstacles `wall`) limités à `max_wall_bounces` (1 par défaut, 0 pour la plupart des niveaux 2-3 : toucher une paroi = particule perdue). Un handler d'obstacle (`engine/concepts.py`) se déclenche **une fois par contact** et son événement (`bounce`, `deflect`, `pass`, `wave`) est consigné dans `SimResult.contacts`.

Formes (`engine/shapes.py`) : disque (`x, y, r`) ou segment plat (`x, y, length, angle_deg`) pour les miroirs, portes, fenêtres et parois. Types d'obstacles : `wall`, `mirror` (rebond voulu, non compté), `barrier`, `splitter`, `gate` (fermée avant le tap), `gate_anti` (ouverte avant le tap), `pole`, `surface`.

Les oscillations (obstacles, cible, Photons) sont calées sur l'instant du lancer : le dispositif « démarre » quand Quarky part. Le jeu doit reproduire cette convention, sinon la solvabilité validée ici ne tient plus.

## Trajectoires golden (contrat avec le runtime Android)

Le runtime Android (`android/core-physics`, Kotlin) porte ce moteur à l'identique. Pour qu'ils ne divergent jamais, `engine/golden.py` enregistre quelques lancers par niveau porté (solution de référence, victoire partielle, rebond de trop, timeout) avec la position à chaque pas :

```bash
python3 cli.py golden        # écrit tests/golden/<niveau>.golden.json
```

`tests/test_golden.py` échoue si ces fichiers ne correspondent plus au moteur (les régénérer après tout changement de physique ou de niveau Tunnel), et le test JUnit `GoldenTest` du module Kotlin les rejoue à 1e-6 près. Niveaux couverts : `GOLDEN_LEVELS` (Tunnel 1-3 pour le POC) — à étendre en même temps que les handlers Kotlin.
