---
name: art-direction
description: Direction artistique validée pour Quark & Cosmos (Stage 1, DA v2 « labo vu à travers un instrument » : matière plate + fond cinématique, Quarky v2) — palette par échelle, design du personnage Quarky et ses 5 évolutions, règle des deux couches visuelles (objets vs champs physiques), et conventions de level design. Charger avant toute production de mockup, asset, écran de niveau, ou toute décision visuelle/UX sur ce projet.
---

# Direction artistique — Quark & Cosmos

**DA v2 (validée) : « un labo de physique rétro-futuriste vu à travers un instrument ».** Chaque échelle est ce qu'un instrument montrerait à ce grossissement (Quantique = cavité de détecteur / chambre à bulles). Le HUD est la lunette de l'instrument. Mondes sombres, jamais de décor pastel/enfantin ; physique en overlay vectoriel fin.

Référence vivante : [`stage1-art-direction/poc-v2/index.html`](../../../stage1-art-direction/poc-v2/index.html) (frames A/B/C, planche Quarky v2, objets, contrat couleur). La combinaison retenue ci-dessous est **B + fond de C** : elle n'existe pas encore comme frame unique dans la page, c'est la prochaine planche à produire.

## Rendu retenu — « B + fond de C »

Décision utilisateur (gate Phase 1 §1.1) : **surtout B** (le plus lisible), avec **le fond de C**.

- **Matière et objets = style B, « labo plat » (Monument Valley)** : aplats, 3–4 couleurs par scène, volume donné par une **ombre en croissant**, des **facettes** et un point de reflet (pas de dégradé radial lourd), contour ~1,5 px. Bloom **léger** (≈ 0,18, physique ≈ 0,08). Portail en disques concentriques plats qui tournent ; franges à bords nets ; traînée de Quarky en ligne simple ; espace négatif assumé.
- **Fond = style C, « cinéma volumétrique »** : **3 couches de parallaxe** liées à la position de Quarky (bokeh lointain → franges/brume → poussière au premier plan), rayons de lumière doux depuis le portail, **grain et vignette ≤ 3 %**. Le fond reste **sous** la matière : luminance du fond ≤ 20 % de celle de la matière, aucun détail haute fréquence derrière la zone de jeu.
- **Budget mobile** : formes vectorielles + **un seul passage de bloom** (¼ de résolution, 2 flous), un grade couleur par échelle, aucune lumière temps réel par objet.
- **L'environnement réagit au résultat** : réussite = les franges se verrouillent en un motif net et une ligne de scan « résout » la cavité ; échec = le fond décohère en bruit et Quarky se dissout. Le résultat s'affiche comme une lecture d'instrument (titre du HUD), jamais en pop-up sur la zone de jeu.
- **Orientation : portrait** (confirmé à la validation de la DA v2 ; la Quantique reste une boîte verticale étroite).

## Règle fondamentale : deux couches visuelles non négociables

1. **Couche "matière"** — Quarky et tout objet manipulable (miroir, lame, barrière, aimant, ressort, cible, obstacles). Rendu plat façon B : aplats + ombre en croissant/facettes + point de reflet, contour coloré ~1,5 px. C'est la couche la plus contrastée de l'écran.
2. **Couche "physique invisible"** — trajectoires prédites, lignes de champ, franges, halos/dômes gravitationnels. Toujours fine (~0.75–1px), pointillée ou en flèches, monochrome par type de force, en surimpression sur la couche matière, qui pulse dans le sens du flux, et **moins bloomée** que la matière.

Cette séparation est aussi un signal pédagogique : le joueur distingue instantanément "ce qui se touche" de "ce que la physique montre".

**Règle par force** : une force = une couleur dédiée + un seul style de trait (plein/pointillé/flèche), répété identiquement partout dans le jeu.

## Quarky — personnage

ADN visuel constant sur toutes les évolutions : corps mou façon gélatine/peluche, grands yeux expressifs (pupilles sombres, reflet blanc), reflet spéculaire façon gomme, contour coloré ~1.5px, léger *rim light* (accent froid) qui le détache du fond sombre.

**Quarky v2 (validé, gate Phase 1 §1.2)** : créature-particule **lumineuse** — un **cœur lumineux** dans une **membrane gélatineuse**, les grands yeux gardés (ancre émotionnelle). Rendu dans le style B (aplats + croissant d'ombre), le cœur est le seul élément « lumineux » de la matière.
- Silhouette = une goutte ronde + deux yeux : lisible à **48 px** (encore à 32 px).
- 8 états **procéduraux** (squash & stretch piloté par la vitesse, pas de sprites) : repos, tension de visée, lancer, vol, collecte, quasi-raté, réussite (aspiré par le portail), échec (se dissout).
- **Mutation Quantique = 2–3 copies de phase fantômes** qui clignotent, sans pupilles pleines (la « vraie » Quarky reste identifiable). Ce sont aussi les **copies de la superposition** en jeu (cf. `gameplay-mechanics`) : la copie perdue à la mesure s'efface avec sa traînée.
- **Dualité** : particule = corps net ; onde = le corps se dissout en ondulations concentriques qui suivent la trajectoire.

La forme **Macro est la forme canon** — les 4 autres échelles sont des *mutations* de cette même base, pas des personnages différents.

## Les 5 échelles

Progression chromatique continue du petit au grand : rose → jaune/orange → vert → violet → indigo profond.

| Échelle | Couleur | Mutation Quarky | Topologie de niveau | Gravité | Obstacle signature | Décor |
|---|---|---|---|---|---|---|
| Quantique (10⁻¹⁵ m) | Rose `#f472b6` | Copies de phase fantômes clignotantes (superposition) | Boîte fermée, verticale, étroite (portrait) | Absente | Barrière/tunnel | Cavité de détecteur quasi-noire, parallaxe 3 couches (fond C), aucune grille |
| Atomique/Moléculaire (10⁻⁹ m) | Jaune `#facc15` | Anneau d'électron en orbite + satellite bleu (charge) | Radiale/orbitale autour d'un noyau | Attraction centrale | Ions +/- | Quasi-noir, aucune grille |
| Macro (1 m) | Vert `#4ade80` | Forme canon | Couloir horizontal | Verticale fixe (bas) | Ressort/miroir/électro-aimant | Fond noir, grille technique très discrète, plateformes à liseré néon |
| Spatiale (10⁹ m) | Violet `#a78bfa` | Mini ailerons voile solaire + traîne d'étoiles | Plan ouvert, sans sol | Multi-puits | Planète géante (fronde gravitationnelle) | Noir étoilé classique |
| Cosmologique (10²² m) | Indigo `#818cf8` | Silhouette légèrement déformée (skew) | Grille elle-même courbée | Déforme l'espace | Trou noir opaque (lentille gravitationnelle) | Seule échelle où le décor réagit visuellement au gameplay (climax/boss de fin) |

### Contrat couleur — Quantique

| Rôle | Couleur |
|---|---|
| Clé de l'échelle | `#f472b6` |
| Accent complémentaire (froid) | `#67e8f9` |
| Fond profond | `#0a0612` |
| Seuil / danger | `#fb923c` |
| Dérivé (énergie moyenne, filament d'intrication) | `#c4b5fd` |
| Texte HUD / texte secondaire | `#f7eef9` / `#b9a7c9` (≥ 4,5:1 sur le fond) |

Daltonisme (deutéranopie/protanopie) : aucune information par la couleur seule. Doublons obligatoires : style de trait par force, glyphes ↑/↓ du spin et +/−, **nombre de rayons du Photon (4/6/8) pour son énergie** (les Photons moyen/haut sont proches en deutéranopie). Les autres échelles recevront leur contrat (clé + accent + fond + seuil) au même format.

## Cible et Photon — rendu

- **Cible = portail**, pas un simple disque doré statique. Concept : halo de téléportation — anneaux concentriques animés (rotation lente + pulsation), cœur lumineux qui aspire visuellement le regard, dans la couleur de l'échelle en cours (pas de couleur dorée universelle imposée). Renforce l'idée narrative que Quarky change d'état/de lieu en l'atteignant, cohérent avec le concept "voyage à travers les échelles" du skill `storytelling`. Animable dès que le moteur de rendu le permet (Stage 2 HTML/JS : `requestAnimationFrame`, pas de sprite statique).
- **Photon = scintillement**, pas juste un point qui pulse en taille. Concept : petites étincelles/reflets qui apparaissent et disparaissent de façon aléatoire autour du corps du Photon (façon paillette), en plus du halo existant — le but est de lire immédiatement "récompense à collecter" au premier coup d'œil, avant même de comprendre la mécanique du niveau. Reste plus petit/discret que la cible et que Quarky (cf. `gameplay-mechanics`), le scintillement ne doit jamais rivaliser en lisibilité avec la trajectoire prévue.
- Les deux restent couche "matière" (rendu plat B : aplats + croissant d'ombre) — le scintillement/l'animation du portail s'ajoutent par-dessus. Photon : couleur = énergie (E = hν), doublée par le nombre de rayons.

## Level design — règles de progression

- **Durée de session constante** sur les 5 échelles — ce n'est pas un axe de différenciation.
- **Difficulté = seul axe de progression**, sur deux plans simultanés :
  1. Courbe globale entre échelles (Quantique/Macro en intro → Cosmologique en climax).
  2. Progression intra-échelle : minimum 3 niveaux par échelle, d'un seul obstacle/une seule règle vers une combinaison de contraintes. Le style et le vocabulaire visuel ne changent jamais d'un niveau à l'autre au sein d'une échelle — seule la quantité/combinaison d'éléments augmente.
- Composition/caméra par échelle : fixe et serrée (Quantique/Atomique) → travelling latéral (Macro) → zoom libre (Spatiale) → zoom + distorsion (Cosmologique).

## HUD & UI

**Lunette d'instrument** : cadre en trait fin autour de la zone de jeu, lectures en police **monospace** (JetBrains Mono) et interface en police **humaniste** (Fira Sans), toutes deux sous licence OFL. Positions inchangées : compteur d'étoiles en haut à gauche, bouton reset circulaire en haut à droite, sélecteur d'objets flottant en bas. Fond des pastilles sombre semi-transparent (`#0f1524` @ 90 %, ou la couleur de lunette de l'échelle).

## Statut

Stage 1 (Identité graphique & DA) validé, **DA v2 incluse**. Ne pas rouvrir les choix ci-dessus sans décision explicite de l'utilisateur — les réutiliser tels quels pour tout mockup Stage 2+ (HTML/JS), asset, ou spécification technique.

## Journal v1 → v2

- **Rendu** : matière illustrée à dégradés (façon Cut the Rope) → **matière plate façon B** (aplats, croissant d'ombre, facettes) + **fond cinématique de C** (parallaxe 3 couches, grain/vignette ≤ 3 %), un seul passage de bloom.
- **Quarky** : même ADN (gélatine, grands yeux, reflet gomme) → **Quarky v2** : cœur lumineux + membrane, 8 états procéduraux, copies de phase = copies de superposition.
- **Cadre** : décor abstrait → **instrument** (cavité de détecteur pour la Quantique), HUD = lunette, polices mono + humaniste OFL.
- **Nouveau** : contrat couleur par échelle (clé + accent + fond + seuil), règle de luminance du fond (≤ 20 % de la matière), environnement qui réagit au résultat.
- **Inchangé** : palette clé par échelle, règle des deux couches, règle par force, portail et Photon scintillant, portrait.
