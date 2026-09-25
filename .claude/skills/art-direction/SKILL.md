---
name: art-direction
description: Direction artistique validée pour Quark & Cosmos (Stage 1) — palette par échelle, design du personnage Quarky et ses 5 évolutions, règle des deux couches visuelles (objets vs champs physiques), et conventions de level design. Charger avant toute production de mockup, asset, écran de niveau, ou toute décision visuelle/UX sur ce projet.
---

# Direction artistique — Quark & Cosmos

Style retenu : **personnages dessinés / matière** (façon Cut the Rope) posés sur des **mondes néon sombres** (jamais de décor pastel/enfantin), avec la physique rendue en **overlay vectoriel fin**.

## Règle fondamentale : deux couches visuelles non négociables

1. **Couche "matière"** — Quarky et tout objet manipulable (miroir, aimant, ressort, cible, obstacles). Rendu illustré : dégradé radial, volume, reflet spéculaire, contour coloré épais (~1.5px). Jamais de remplissage plat.
2. **Couche "physique invisible"** — trajectoires prédites, lignes de champ, halos/dômes gravitationnels. Toujours fine (~0.75–1px), pointillée ou en flèches, monochrome par type de force, en surimpression sur la couche matière.

Cette séparation est aussi un signal pédagogique : le joueur distingue instantanément "ce qui se touche" de "ce que la physique montre".

**Règle par force** : une force = une couleur dédiée + un seul style de trait (plein/pointillé/flèche), répété identiquement partout dans le jeu.

## Quarky — personnage

ADN visuel constant sur toutes les évolutions : corps mou façon gélatine/peluche, grands yeux expressifs (pupilles sombres, reflet blanc), reflet spéculaire façon gomme, dégradé radial (clair en haut-gauche → foncé en bas-droite), contour coloré ~1.5px, léger *rim light* qui le détache du fond sombre.

La forme **Macro est la forme canon** — les 4 autres échelles sont des *mutations* de cette même base, pas des personnages différents.

## Les 5 échelles

Progression chromatique continue du petit au grand : rose → jaune/orange → vert → violet → indigo profond.

| Échelle | Couleur | Mutation Quarky | Topologie de niveau | Gravité | Obstacle signature | Décor |
|---|---|---|---|---|---|---|
| Quantique (10⁻¹⁵ m) | Rose `#f472b6` | Dédoublement translucide clignotant (superposition) | Boîte fermée, verticale, étroite | Absente | Barrière/tunnel | Quasi-noir, aucune grille |
| Atomique/Moléculaire (10⁻⁹ m) | Jaune `#facc15` | Anneau d'électron en orbite + satellite bleu (charge) | Radiale/orbitale autour d'un noyau | Attraction centrale | Ions +/- | Quasi-noir, aucune grille |
| Macro (1 m) | Vert `#4ade80` | Forme canon | Couloir horizontal | Verticale fixe (bas) | Ressort/miroir/électro-aimant | Fond noir, grille technique très discrète, plateformes à liseré néon |
| Spatiale (10⁹ m) | Violet `#a78bfa` | Mini ailerons voile solaire + traîne d'étoiles | Plan ouvert, sans sol | Multi-puits | Planète géante (fronde gravitationnelle) | Noir étoilé classique |
| Cosmologique (10²² m) | Indigo `#818cf8` | Silhouette légèrement déformée (skew) | Grille elle-même courbée | Déforme l'espace | Trou noir opaque (lentille gravitationnelle) | Seule échelle où le décor réagit visuellement au gameplay (climax/boss de fin) |

## Cible et Photon — rendu

- **Cible = portail**, pas un simple disque doré statique. Concept : halo de téléportation — anneaux concentriques animés (rotation lente + pulsation), cœur lumineux qui aspire visuellement le regard, dans la couleur de l'échelle en cours (pas de couleur dorée universelle imposée). Renforce l'idée narrative que Quarky change d'état/de lieu en l'atteignant, cohérent avec le concept "voyage à travers les échelles" du skill `storytelling`. Animable dès que le moteur de rendu le permet (Stage 2 HTML/JS : `requestAnimationFrame`, pas de sprite statique).
- **Photon = scintillement**, pas juste un point qui pulse en taille. Concept : petites étincelles/reflets qui apparaissent et disparaissent de façon aléatoire autour du corps du Photon (façon paillette), en plus du halo existant — le but est de lire immédiatement "récompense à collecter" au premier coup d'œil, avant même de comprendre la mécanique du niveau. Reste plus petit/discret que la cible et que Quarky (cf. `gameplay-mechanics`), le scintillement ne doit jamais rivaliser en lisibilité avec la trajectoire prévue.
- Les deux restent couche "matière" (dégradé, volume) — le scintillement/l'animation du portail s'ajoutent par-dessus, ils ne remplacent pas le rendu dégradé de base.

## Level design — règles de progression

- **Durée de session constante** sur les 5 échelles — ce n'est pas un axe de différenciation.
- **Difficulté = seul axe de progression**, sur deux plans simultanés :
  1. Courbe globale entre échelles (Quantique/Macro en intro → Cosmologique en climax).
  2. Progression intra-échelle : minimum 3 niveaux par échelle, d'un seul obstacle/une seule règle vers une combinaison de contraintes. Le style et le vocabulaire visuel ne changent jamais d'un niveau à l'autre au sein d'une échelle — seule la quantité/combinaison d'éléments augmente.
- Composition/caméra par échelle : fixe et serrée (Quantique/Atomique) → travelling latéral (Macro) → zoom libre (Spatiale) → zoom + distorsion (Cosmologique).

## HUD & UI

Pastilles arrondies, fond semi-transparent sombre (`#0f1524` @ 90%), compteur d'étoiles en haut à gauche, bouton reset circulaire en haut à droite, sélecteur d'objets flottant en bas. Rendu illustré cohérent avec la couche matière (pas de HUD purement plat/technique).

## Statut

Stage 1 (Identité graphique & DA) validé. Ne pas rouvrir les choix ci-dessus sans décision explicite de l'utilisateur — les réutiliser tels quels pour tout mockup Stage 2+ (HTML/JS), asset, ou spécification technique.
