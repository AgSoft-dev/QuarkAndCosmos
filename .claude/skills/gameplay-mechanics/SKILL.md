---
name: gameplay-mechanics
description: Mécaniques de jeu validées pour Quark & Cosmos — boucle physique lancer/rebond, contrôle d'orientation et de puissance des objets (expérience de labo), et système de notation à 3 étoiles par collecte de Photons sur la trajectoire (modèle Cut the Rope). Charger avant toute spécification de niveau, UI de réglage d'objet, ou logique de scoring.
---

# Gameplay Mechanics — Quark & Cosmos

## Boucle de base (établie en Stage 2)

Glisser-relâcher façon fronde : le joueur tire Quarky en arrière puis relâche, la physique (gravité + éventuels champs) fait le reste jusqu'à la cible ou un échec. Cf. maquette [`stage2-mockup/index.html`](../../../stage2-mockup/index.html).

## Contrôle des objets — paradigme "expérience de labo"

Cohérent avec la prémisse du skill `storytelling` (Quarky né d'une expérience de labo) : avant de lancer, le joueur peut régler certains objets de la scène comme des instruments de laboratoire, pas seulement les positionner.

- **Orientation** : rotation de l'objet (miroir, aimant, électro-aimant...) pour changer l'angle de réflexion/déviation.
- **Puissance/intensité** : curseur ou molette réglant la force d'un champ (intensité d'un électro-aimant, angle d'un ressort, etc.) plutôt qu'un simple on/off.
- Ces réglages font partie de la résolution du puzzle au même titre que le lancer — un niveau peut n'avoir qu'une seule combinaison valide (précision) ou plusieurs solutions (plage de tolérance), selon la difficulté voulue.

**Dépendance bloquante** : cette mécanique ne peut être implémentée/testée sérieusement qu'une fois le moteur physique du Stage 3 construit, car c'est lui qui doit générer et valider les niveaux (vérifier qu'au moins une combinaison orientation/puissance résout le niveau). Ne pas coder de vraie UI de réglage avant cette brique — la maquette Stage 2 peut rester en objets fixes/non réglables en attendant.

## Règle de base — action en vol (tout concept, dès la beta)

Constat (retour design) : un lancer où tout est réglé avant le tir (angle, puissance, dials) se résout comme un problème de trajectoire idéale — proche d'Angry Birds, mais sans la tension "temps réel" de Cut the Rope (timing de la découpe, obstacles mouvants, ordre des actions). Décision : **chaque concept du monde Quantique intègre au moins une variable qui dépend du temps pendant le vol**, pas seulement des réglages pré-tir. Deux briques génériques, réutilisables par tous les concepts :

1. **Élément oscillant** — la position d'un obstacle (ou de la cible) varie dans le temps (ex. va-et-vient sinusoïdal). Le joueur doit alors viser correctement ET faire coïncider son temps de vol avec le bon moment de l'oscillation, pas juste viser un point fixe.
2. **Action déclenchée en vol (« tap »)** — un seul geste du joueur pendant le vol (pas un contrôle continu) qui bascule un état à l'instant choisi : ouvrir une porte liée, basculer onde/particule, inverser une polarité. C'est l'équivalent de la découpe de corde au bon moment dans Cut the Rope — un geste, mais dont le *timing* fait toute la difficulté. Le solveur Stage 3 traite l'instant du tap comme un paramètre de plus (recherché sur une grille), donc la solvabilité reste garantie et vérifiable comme pour l'angle/la puissance.

Les réglages pré-tir (dials façon labo, cf. section suivante) restent valides et se cumulent avec ces mécaniques — l'objectif est d'ajouter des variables, pas de remplacer celles qui existent déjà. Répartition retenue pour les 7 concepts de la beta (cf. `CLAUDE.md`) : voir Stage 3 (`stage3-physics-engine/engine/generator.py`) pour le détail par concept — chacun a désormais soit un élément oscillant, soit un déclenchement en vol, parfois les deux.

## Structure de progression par monde

Trois phases, dans cet ordre, pour l'organisation des niveaux au sein d'un même monde (échelle) :

1. **Introduction séquentielle** — chaque concept physique du monde (cf. liste dans `CLAUDE.md`, 7 concepts pour le Quantique en beta) est présenté un par un, dans son propre niveau d'intro, jamais deux concepts nouveaux en même temps.
2. **Progression de difficulté intra-concept** — plusieurs niveaux qui font monter la difficulté sur un même concept avant de passer au suivant (cf. règle déjà posée dans `art-direction` : même vocabulaire visuel, on ajoute des contraintes plutôt que de changer le style).
3. **Mix inter-concepts** — des niveaux combinant 2+ concepts déjà appris du même monde, pour des puzzles plus riches/complexes.

### Difficulté = disposition, jamais seulement la place des Photons (décision Stage 3)

Retour design : déplacer les Photons sur une disposition identique ne rend pas un niveau plus riche, seulement plus exigeant en précision. **Chaque cran de difficulté change la disposition pour explorer la mécanique plus loin**, avec le même vocabulaire visuel :

1. **Découverte** — une seule instance de la mécanique, effet visible immédiatement.
2. **Séquence** — la mécanique utilisée **deux fois, dans deux sens** au cours du même vol. C'est là que le tap devient un vrai timing (une fenêtre *entre* deux contacts), façon découpe de corde dans Cut the Rope.
3. **Enchaînement** — trois instances, ou deux plus un élément mobile : visée, puissance et timing interagissent.

Monde Quantique (générateur `stage3-physics-engine/engine/generator.py`, une fonction par concept et par difficulté) :

| Concept | 1 — découverte | 2 — séquence | 3 — enchaînement |
|---|---|---|---|
| Effet tunnel | une barrière (fenêtre dans une paroi), seuil oscillant | deux barrières en série : une vitesse qui tombe dans un creux aux deux (« résonance ») | barrière → miroir → barrière |
| Superposition | un séparateur | deux mesures en cascade (bras haut puis bas) | trois mesures, le 2e séparateur dérive |
| Intrication | une porte ouverte par le tap | paire **anti-corrélée** : franchir A (ouverte avant le tap), taper, franchir B | la porte M sert de **miroir** tant qu'elle est fermée, puis le même tap ouvre B |
| Incertitude | précision vs vitesse, cible mobile | une fente étroite (précision → lenteur) devant une cible qui dérive | deux fentes alignées, cible plus rapide |
| Quantification | crans d'énergie, une barrière | deux barrières : seuls 2 crans passent | trois barrières + miroir : un seul cran passe |
| Spin | un pôle | deux pôles + : attiré en A, inverser le spin **entre** A et B | pôles +, −, + : lire le signe de chaque pôle pour savoir où inverser |
| Dualité | une surface traversée en onde | rebond en **particule** sur s1, puis traversée en **onde** de s2 | deux rebonds en particule puis traversée en onde, cible mobile |

Chaque niveau déclare `must_contact` (la séquence d'interactions attendue). Le validateur rejette tout niveau où un lancer gagnant contourne la mécanique (`bypass_solutions` doit valoir 0).

Surfaces planes (miroirs, portes, fenêtres) plutôt que disques pour tout rebond voulu : « angle d'incidence = angle de réflexion » est prévisible pour le joueur (et c'est de l'optique de lycée), alors qu'un rebond sur un disque amplifie la moindre erreur de visée.

**Portée beta vs full release** : la phase 3 (mix inter-concepts) et la progression de difficulté complète de la phase 2 sont réservées à la **full release**. La **beta/test fermé** peut se limiter à une version allégée : moins de niveaux par concept (voire un seul par concept), peu ou pas de montée en difficulté intra-concept, et **aucun niveau de mix**. Cf. `CLAUDE.md` pour la portée exacte retenue pour le build de test fermé actuel.

## Système de notation — 3 étoiles par collecte (modèle Cut the Rope)

Décision actuelle (remplace la version "efficacité/essais" précédente) : 3 collectibles sont placés le long d'un tracé plausible entre le lanceur et la cible. Chaque collectible touché pendant le vol de Quarky, dans la **même tentative** que celle qui atteint la cible, rapporte 1 étoile. Rater la cible ou devoir relancer annule les collectibles ramassés lors de cette tentative — il faut tout faire en un seul vol réussi.

- **Nom retenu pour le collectible : "Photon"** — pas "Quark", pour éviter la confusion avec le nom du jeu et celui de la mascotte (Quarky). À réévaluer si besoin, mais tenir ce nom par défaut dans tous les textes/assets.
- Rendu visuel : petite particule lumineuse, couleur de l'échelle en cours, cohérente avec la couche "matière" de `art-direction` (dégradé, pas un simple point plat) — mais plus petite et plus discrète que Quarky ou la cible, pour ne pas polluer la lisibilité de la trajectoire prévue.
- Un niveau reste "réussi" (cible atteinte) même à 0 Photon collecté — les Photons ne conditionnent que le nombre d'étoiles, jamais la complétion du niveau elle-même.
- **Distribution 1-2-3 étoiles (décision Stage 3)** : on mesure par « lancer de rayons » (éventail dense de lancers sur angle/puissance/instant du tap) l'ensemble des lancers valides d'un niveau. Parmi eux, la part qui rapporte au moins *k* étoiles suit une **gaussienne tronquée** `exp(−k²/2σ²)`, k = 1..3 : beaucoup de lancers valides donnent 1 étoile, peu en donnent 3. **σ diminue avec la difficulté** (2.2 / 1.6 / 1.2 pour les difficultés 1 / 2 / 3), donc le nombre de chemins/timings qui rapportent 3 étoiles se resserre. Le générateur place les Photons pour coller à cette cible ; un Photon peut osciller (brique "élément oscillant") quand les chemins valides se superposent et que seul le timing peut les départager. Rapport de revue : `python3 cli.py report` (JSON + CSV + HTML avec mini-cartes), cf. `stage3-physics-engine/README.md`.
- **La 3e étoile récompense une route plus maligne, pas seulement plus précise.** Plusieurs dispositions font émerger des routes alternatives qui utilisent davantage la mécanique (ex : ping-pong entre deux portes intriquées, particule qui rebondit entre deux barrières avant de passer par effet tunnel, seconde chance en onde après un rebond raté). Le placement essaie comme référence le meilleur chemin de chaque route : une route rare et riche est le candidat naturel pour le 3e Photon. Principe Cut the Rope : on gagne facilement, puis on voit un Photon qui suggère qu'il existe une plus belle trajectoire.
- **Pourquoi revenir chercher les 3 étoiles** (à implémenter côté jeu, Stage 5) : relance instantanée ; fantôme du meilleur essai précédent ; après une première réussite, le Photon manquant « pulse » pour signaler qu'un autre chemin existe ; la page Codex « Dans la vraie physique… » du concept ne se débloque qu'avec 3 étoiles (la récompense est de comprendre plus, cohérent avec le ton du skill `storytelling`).
- **Les étoiles ouvrent la suite (full release)** : le total d'étoiles débloque les niveaux et les mondes suivants. Seuils à calibrer sur les données du test fermé, avec la règle de base : on n'exige jamais 3 étoiles partout (seuil d'un monde ≈ 2 étoiles de moyenne sur le monde précédent), pour que la curiosité, pas la frustration, fasse revenir sur un niveau. La beta n'a pas de verrou.
- **Dépendance Stage 3** : le placement des 3 Photons par niveau doit être vérifié solvable par le générateur/validateur de niveaux (au moins une trajectoire capable de les collecter tous les 3 puis d'atteindre la cible) — c'est lui qui déterminera leur position définitive, pas un placement à la main.

## Statut

Direction validée pour les trois mécaniques ci-dessus (boucle de lancer, réglages d'objets façon labo, notation par Photons). Réglages d'objets et placement définitif des Photons différés au Stage 3 (moteur physique) — ne pas construire l'UI de réglage ni le placement final des collectibles avant que le moteur existe. La maquette Stage 2 peut illustrer la collecte de Photons avec un placement arbitraire à titre de preuve de concept.
