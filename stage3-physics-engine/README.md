# Moteur physique vulgarisé — Stage 3

Génère, valide et exporte en JSON les niveaux du monde Quantique (beta, 7 concepts — cf. `CLAUDE.md`). Python ≥ 3.10, aucune dépendance à l'exécution.

```bash
python3 cli.py list                          # concepts disponibles
python3 cli.py generate-all                  # régénère levels/*.json
python3 cli.py validate levels/<niveau>.json # rapport de solvabilité
python3 cli.py solve levels/<niveau>.json    # meilleure solution

pip install -e ".[dev]" && python3 -m pytest -q
```

## Ce que garantit un niveau exporté

- **Solvable** : au moins une combinaison de la grille `param_space` atteint la cible.
- **3 Photons** placés automatiquement (pas à la main, cf. section suivante). Les 3 sont collectables en un seul vol.
- **Tolérance** ≥ 5 % : la part de la grille qui réussit (`tolerance`, `three_star_tolerance` dans le JSON). En dessous, le niveau est injouable au doigt.
- **Tap en vol réel** : un tap avant `TAP_MIN_TIME` (0,1 s) n'est pas recherché. Taper au lancer reviendrait à un réglage pré-tir.
- **`schema_version`** en tête du JSON : à incrémenter à chaque changement incompatible du format.

Les tests vérifient aussi que les JSON commités sont identiques à la sortie du générateur. Après toute modification du moteur ou d'un gabarit, relancer `generate-all`.

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

Pas fixe `DT = 0.01`, 300 pas max, boîte fermée sans gravité, 1 rebond « subi » max (parois + murs internes). Un handler d'obstacle (`engine/concepts.py`) se déclenche **une fois par contact**, à l'entrée dans son rayon.
