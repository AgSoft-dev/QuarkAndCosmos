# Spécification de la simulation — monde Quantique

Contrat déterministe que **toute** implémentation de la physique du jeu (runtime Android, visionneuse HTML, futures maquettes) doit reproduire pour que la solvabilité validée par le générateur reste vraie en jeu. Référence : `stage3-physics-engine/engine/` (`simulate.py`, `shapes.py`, `concepts.py`, `vec.py`). En cas d'écart entre ce document et le code Python, **le code fait foi** et ce document doit être corrigé dans la même PR.

La maquette Stage 2 (`stage2-mockup/index.html`) a sa propre physique JS écrite à la main : elle **n'est pas** une implémentation de cette spec (cf. § « Écarts connus »).

Ce document décrit le comportement **actuel** du moteur, y compris ses simplifications. Les corrections prévues (effet tunnel, quantification à crans, rebond seulement en approche, collision continue) sont des décisions [GATE] de `todo.md` : elles modifieront cette spec quand elles seront validées.

## 1. Repère et unités

- Boîte fermée normalisée `[0, 1] × [0, 1]`, **sans gravité**. `y` croît vers le bas (convention écran : `wTop` a un `y` plus petit que `wBot`).
- Temps en secondes simulées. Vitesses en unités de boîte par seconde.
- Angles en degrés : `from_angle(a, m) = (m·cos a, m·sin a)`, `angle_of(v) = atan2(v.y, v.x)` en degrés. Avec `y` vers le bas, un angle positif vise vers le bas.
- Flottants double précision (IEEE 754).

## 2. Constantes

| Nom | Valeur | Rôle |
|---|---|---|
| `DT` | `0.01` | pas fixe, **jamais** calé sur le framerate |
| `MAX_STEPS` | `300` | au-delà : échec `timeout` (~3 s de vol) |
| `COLLISION_EPS` | `0.004` | marge ajoutée à tous les tests de contact |
| `TAP_MIN_TIME` | `0.1` | instant minimal d'un tap recherché par le solveur |
| `MAX_WALL_BOUNCES` | `1` | valeur par défaut de `max_wall_bounces` (le JSON v2 l'écrit toujours explicitement) |
| `SEGMENT_HALF_THICKNESS` | `0.012` | demi-épaisseur d'un segment sans `r` |
| rayon disque par défaut | `0.03` | obstacle disque sans `r` |
| rayon cible par défaut | `0.045` | |
| rayon Photon par défaut | `0.02` | |
| seuil d'énergie par défaut | `0.6` | obstacle `barrier` sans `energy_threshold` |

Le rendu peut tourner à n'importe quel framerate : il accumule le temps réel et exécute autant de pas **entiers** de `DT` que nécessaire (le reste est reporté au frame suivant, jamais simulé en pas fractionnaire).

## 3. État initial (lancer)

- Position : `launcher.(x, y)`.
- Vitesse : `from_angle(angle_deg, power)` ; `power` vaut `1.0` s'il est absent des paramètres.
- Cas `precision` (concept incertitude) :
  - `snap = 2 + (1 − precision) · 28` ;
  - `eff_angle = round(angle_deg / snap) · snap`, avec l'**arrondi bancaire** de Python (demi → pair ; en Kotlin `Math.rint`, pas `Math.round`) ;
  - `power = max(0.15, 1.2 − precision)` ;
  - vitesse `= from_angle(eff_angle, power)`.
- `t = 0` au lâcher. **Toutes les oscillations sont calées sur cet instant** : le dispositif « démarre » avec le tir (décision encore ouverte dans `todo.md`, mais c'est la convention validée aujourd'hui).
- État : `tapped = false`, `wall_bounces = 0`, `in_contact = ∅`, `collected = ∅`, `contacts = []`.

## 4. Un pas de simulation — ordre strict

Pour `step = 0 … MAX_STEPS − 1`, avec `t = (step + 1) · DT` :

1. **Déplacement** (Euler explicite, vitesse constante entre deux contacts) : `pos += vel · DT`.
2. **Tap(s)** : les instants `tap_time`, `tap_time_2`… sont traités dans l'ordre ; chaque tap dont l'instant est atteint (`t ≥ tap_time_k`) met `tapped = true` et, si Quarky est en superposition, **mesure** (§7 bis). Un tap prend donc effet au premier pas dont la fin atteint l'instant du geste, **avant** les collisions de ce pas.

Les étapes 3 à 6 s'appliquent à **chaque copie** de Quarky (une seule hors superposition), dans l'ordre de création des copies.
3. **Parois de la boîte** : pour chaque axe, si `x ≤ 0` → `x = 0`, `vel.x = |vel.x|` ; si `x ≥ 1` → `x = 1`, `vel.x = −|vel.x|` (idem en `y`). Un pas qui touche une ou deux parois compte **un** rebond. Si `wall_bounces > max_wall_bounces` → échec `lost:too_many_wall_bounces`, fin immédiate.
4. **Obstacles**, dans l'ordre du tableau `obstacles` (la vitesse sortant d'un handler est l'entrée du suivant) :
   1. position effective `(ox, oy)` = oscillation de `motion` à l'instant `t` (§6) ;
   2. si l'obstacle ne **touche** pas `pos` (§5) : le retirer de `in_contact`, passer au suivant ;
   3. s'il est déjà dans `in_contact` : passer au suivant (**un handler par contact**, pas par pas) ;
   4. sinon l'ajouter à `in_contact`, calculer l'obstacle effectif (position `(ox, oy)` ; `energy_threshold` oscillé par `threshold_motion`, §6) et appeler son handler (§7) → `(vel, event)` ;
   5. si `type ≠ wall` : ajouter `(id, event)` à `contacts` ;
   6. si `type = wall` : `wall_bounces += 1` ; si `> max_wall_bounces` → échec `lost:too_many_wall_bounces`, fin immédiate.
5. **Photons** : pour chaque Photon non collecté, position oscillée à `t` ; collecté si `dist(pos, photon) < r + COLLISION_EPS` (inégalité stricte).
6. **Cible** : position oscillée à `t` ; **succès** si `dist(pos, cible) < r + COLLISION_EPS`. Les Photons collectés à ce même pas comptent.

Après `MAX_STEPS` pas sans succès : échec `timeout`.

`max_wall_bounces` compte les rebonds « subis » (parois de la boîte + obstacles `wall`). Les `mirror` sont des rebonds voulus et ne sont jamais comptés.

## 5. Formes et contact (`shapes.py`)

- **Disque** : `(x, y, r)`. Squelette = son centre.
- **Segment plat** (présence de `length`) : centre `(x, y)`, longueur `length`, orientation `angle_deg` (défaut 0) ; extrémités `centre ± (cos a, sin a) · length/2`. Squelette = ce segment, épaisseur `2 · r` (défaut `SEGMENT_HALF_THICKNESS`).
- `closest_point` : le centre pour un disque ; pour un segment, la projection de `pos` sur `[A, B]` bornée à `[0, 1]`.
- **Contact** : `dist(pos, closest_point) < radius + COLLISION_EPS` (strict). Le rejet préalable par cercle englobant (`radius + EPS + length/2`) n'est qu'une optimisation, sans effet sur le résultat.
- **Normale** : `pos − closest_point` (non normalisée ; `reflect` la normalise, et une normale nulle laisse la vitesse inchangée).
- **Réflexion** : `v' = v − 2 (v·n̂) n̂`. Elle est appliquée **même si la particule s'éloigne déjà** (pas de test `v·n < 0`) et la position n'est **pas** repoussée hors de l'obstacle. Collision discrète (pas de balayage continu) : c'est le pas `DT` + `COLLISION_EPS` qui empêche de traverser les segments fins aux vitesses du jeu (`power ≤ 1`, soit ≤ 0,01 par pas).

## 6. Oscillations (« élément oscillant »)

- `motion = {axis, amplitude, period, phase?}` sur un obstacle, la cible ou un Photon : la coordonnée `axis` (`"x"` ou `"y"`) vaut `base + amplitude · sin(2π · t / period + phase)`, `phase` = 0 par défaut.
- `threshold_motion = {amplitude, period, phase?}` sur un obstacle à seuil : `energy_threshold(t) = base + amplitude · sin(2π · t / period + phase)`.
- Toujours évaluées à `t = (step + 1) · DT` du pas en cours, jamais à l'instant de rendu.

## 7. Handlers (`concepts.py`)

Choix du handler : d'abord par `type` d'obstacle, sinon handler par défaut du concept du niveau, sinon `wall_reflect`.

| `type` | Handler | Effet | Événement |
|---|---|---|---|
| `wall`, `mirror` | `wall_reflect` | réflexion (§5) | `bounce` |
| `splitter` | `superposition_splitter` | lame plate : la copie courante garde sa vitesse (transmise), une nouvelle copie part avec la vitesse réfléchie (§5), cf. §7 bis | `transmit` (copie courante) / `reflect` (nouvelle copie) |
| `detector` | — | aucun contact (Quarky le traverse) ; sert seulement à la mesure, §7 bis | — |
| `barrier` | `tunnel_barrier` | si `‖v‖ ≥ energy_threshold(t)` : vitesse inchangée ; sinon réflexion | `pass` / `bounce` |
| `gate` | `intrication_gate` | `tapped` : traverse ; sinon réflexion | `pass` / `bounce` |
| `gate_anti` | `intrication_gate_anti` | `tapped` : réflexion ; sinon traverse | `bounce` / `pass` |
| `pole` | `spin_pole` | `spin = spin_up` (paramètre, défaut `true`), inversé si `tapped` ; `attire = (spin ∧ pole = "+") ∨ (¬spin ∧ pole = "−")` ; `kick = kick_deg` (défaut 40) si attire, sinon `−kick_deg` ; nouvelle direction `angle_of(v) + kick`, norme conservée | `deflect` |
| `surface` | `dualite_surface` | non `tapped` (particule) : réflexion → `bounce`. `tapped` (onde) : si `interference_offset_deg mod 360 = 180` → vitesse inchangée (transmission) ; sinon direction `angle_of(v_réfléchie) + offset` (défaut 15), norme conservée | `bounce` / `wave` |

Handlers par défaut des concepts (obstacle d'un type non listé) : `superposition` → splitter, `tunnel` → barrier, `intrication` → gate, `spin` → pole, `dualite` → surface, `incertitude` / `quantification` → `wall_reflect`.

### 7 bis. Superposition (copies fantômes)

- Au contact d'une lame `splitter`, Quarky devient deux copies. Chaque copie a sa position, sa vitesse, ses `in_contact`, `contacts`, `wall_bounces` et Photons (copiés au moment de la séparation). Une copie qui touche une autre lame se sépare à son tour.
- **Mesure** = un tap pendant que plusieurs copies existent : on garde la copie la plus proche d'un `detector` (distance au squelette du détecteur, à sa position oscillée ; égalité → la première créée). Les autres disparaissent **avec leurs Photons**. On ajoute `(id du détecteur, "measure")` aux contacts de la survivante. Un tap sans superposition ne mesure rien.
- La **cible** n'accepte qu'un Quarky mesuré : tant qu'il y a plusieurs copies, l'étape 6 est sautée.
- **Décohérence** : si une copie dépasse `max_wall_bounces` pendant la superposition, tout le lancer échoue (`lost:decoherence`).

Le jeu n'a pas besoin de `must_contact` ni du journal `contacts` pour jouer : ils ne servent qu'au validateur (anti-contournement). Les événements restent utiles côté jeu pour déclencher les effets visuels/sonores.

## 8. Tap et paramètres

- **Un tap par vol**, sauf en superposition où chaque lame peut demander sa mesure (`tap_time_2`, strictement après `tap_time`). Chaque instant de tap est un paramètre comme l'angle : le solveur le cherche sur la grille de `param_space`, **sans jamais descendre sous `TAP_MIN_TIME`** (un tap au lancer = réglage pré-tir déguisé). **Décision game design (validée) :** côté jeu, un tap avant `TAP_MIN_TIME` est ignoré (le geste reste disponible pour la suite du vol), ce qui garantit que tout lancer jouable est un lancer que le validateur a vérifié.
- En jeu, l'instant du tap est le temps simulé écoulé depuis le lâcher au moment où l'entrée est traitée ; il est quantifié au pas (§4.2).
- La solvabilité, les tolérances et les étoiles sont **mesurées sur la grille** `param_space` (`range` : de `min` à `max` par `step`, valeurs arrondies à 4 décimales ; `choice` : liste). Des dials continus restent jouables, mais seuls les points de grille sont garantis.

## 9. Données consommées (JSON v2)

Le jeu lit `levels/<nom>.json` (`schema_version` = 2) : `launcher`, `target`, `obstacles`, `photons`, `max_wall_bounces`, `param_space`, `hint.params` (solution de référence, pour l'indice « premier segment » après 5 échecs), plus `id`, `scale`, `concept`, `difficulty`, `codex_text`. Il refuse un `schema_version` qu'il ne connaît pas. `levels/meta/*.meta.json` est réservé aux outils de dev. Détail : `stage3-physics-engine/README.md`.

## 10. Vérifier une implémentation

- Tolérance attendue : positions à `1e-6` près. `sin`, `cos`, `atan2`, `hypot` peuvent différer d'un ulp entre bibliothèques mathématiques ; un tir qui frôle un bord peut donc basculer, d'où l'exigence de tolérance ≥ 5 % par niveau.
- Méthode prévue (§4.3 de `todo.md`) : trajectoires de référence générées par le moteur Python (`tests/golden/*.json` : paramètres → trace échantillonnée) et rejouées par l'implémentation cible. Tant qu'elles n'existent pas, rejouer `hint.params` de chaque niveau doit atteindre la cible avec les Photons de `reference_solution.photon_ids` (méta).

## 11. Écarts connus de la maquette Stage 2

La maquette (`stage2-mockup/index.html`, `quantiqueSubstep`) diverge de ce contrat, entre autres :
- marge Photon/cible `0.012` au lieu de `COLLISION_EPS = 0.004` ;
- murs internes en chaînes de disques, testés **à chaque pas** (pas « une fois par contact ») ;
- dernier sous-pas de chaque frame fractionnaire (`min(SIM_DT, reste)`) au lieu de pas entiers ;
- `max_wall_bounces` codé en dur à 1, niveau codé en dur (pas de lecture du JSON).

Elle reste une maquette d'intention visuelle ; la remplacer par une visionneuse qui lit les JSON exportés est prévu (`todo.md` §4.1, outil « level viewer »).
