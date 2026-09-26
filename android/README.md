# Quark & Cosmos — POC Android

Premier build jouable : **accueil → échelles → carte du monde Quantique → niveau Effet tunnel 1**. Portrait, Android 8.0+ (`minSdk 26`), DA v2 (« B + fond de C », Quarky v2).

## Ouvrir et lancer dans Android Studio

1. **File ▸ Open…** et choisir ce dossier `android/` (pas la racine du dépôt).
2. Laisser la synchronisation Gradle se faire. Si Android Studio le demande, installer la plateforme **Android 16 (API 36)** proposée.
   - JDK : celui d'Android Studio convient (Settings ▸ Build Tools ▸ Gradle ▸ Gradle JDK = JDK 17 ou plus).
   - Si l'assistant propose de passer à AGP 9, **refuser pour l'instant** : AGP 9 intègre Kotlin autrement et demande d'adapter les scripts.
3. Créer un émulateur si besoin (Device Manager) : un téléphone en portrait, image **API 26 ou plus** (x86_64).
4. Configuration **app** ▸ Run.

Les niveaux ne sont pas copiés dans ce dossier : la tâche `copyLevels` les prend dans `../stage3-physics-engine/levels/` à chaque build (seulement les fichiers livrés, jamais `meta/`). Garder la structure du dépôt telle quelle.

En ligne de commande : `./gradlew :app:installDebug` (téléphone ou émulateur branché), `./gradlew :core-physics:test`.

## Modules

| Module | Rôle | Dépendances |
|---|---|---|
| `:core-physics` | Port Kotlin **pur** du moteur Python (`stage3-physics-engine/engine`) : niveau JSON v2, pas fixe, handlers. Testé contre les trajectoires golden. | kotlinx-serialization-json |
| `:game` | Vue de jeu **libGDX** (JVM) : `LevelScreen` (visée fronde, boucle à pas entiers de `DT`, rendu, lecture de résultat), rendu procédural (`render/`). | `:core-physics`, libGDX, FreeType |
| `:app` | Coque Android : `MainActivity` (menus Compose), `GameActivity` (libGDX), `Progress` (DataStore), haptique. | `:game`, Compose, DataStore |

La physique ne connaît ni libGDX ni Android ; la vue de jeu ne connaît ni les activités ni la sauvegarde (interface `GameHost`).

## Ce que le POC couvre

- **Accueil** : Quarky v2 au repos dans la lunette de l'instrument, « Jouer ».
- **Échelles** : les 5 échelles dans l'ordre du voyage ; seule la Quantique est ouverte (étoiles / 21 et niveaux faits / 7), les autres affichent « Bientôt ».
- **Carte Quantique** : 7 nœuds (ordre de `CLAUDE.md`), Quarky sur le nœud courant, étoiles par niveau ; seul Effet tunnel est jouable, les 6 autres sont verrouillés.
- **Effet tunnel 1** :
  - glisser vers l'arrière n'importe où dans la boîte, relâcher pour tirer ; l'angle et l'énergie sont calés sur la grille `param_space` validée par le moteur Python ;
  - le panneau du bas montre l'énergie de Quarky face au seuil oscillant de la barrière (PASSE / BLOQUE) ;
  - 3 Photons = 3 étoiles, en un seul vol ; résultat lu comme une lecture d'instrument, avec la réplique du carnet du labo ;
  - fantôme du tir précédent, indice « premier segment » après 5 échecs ;
  - haptique : cran de visée, tir, Photon, réussite/échec.
- **Sauvegarde** : meilleures étoiles par niveau, conservées entre deux lancements.

## Limites connues (volontaires pour un POC)

- Un seul niveau jouable ; les handlers des 6 autres concepts ne sont pas encore portés (un obstacle non porté lève `UnsupportedObstacle`).
- Pas de vrai bloom (halos additifs à la place) ; budget de frame à mesurer sur un téléphone d'entrée de gamme (todo.md §4.2, spike).
- Pas d'audio (Stage 4), pas de Codex, pas de réglages.
- La boîte de jeu est carrée (la physique est dans une boîte unité) : la « boîte verticale étroite » de la DA demandera une boîte non carrée côté moteur.
- Les oscillations démarrent au lâcher (spec §3) : avant le tir, le dispositif est à l'arrêt.
