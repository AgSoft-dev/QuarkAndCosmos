---
name: android-architecture
description: Architecture validée de l'app Android de Quark & Cosmos (POC Stage 5) — modules Gradle (:core-physics Kotlin pur, :game libGDX, :app coque Compose), règle de déterminisme Python ⇄ Kotlin par trajectoires golden, budgets de performance et d'APK, conventions (minSdk 26, portrait, niveaux copiés depuis le moteur). Charger avant toute modification du dossier android/ ou toute spec technique Android.
---

# Architecture Android — Quark & Cosmos

Décision utilisateur (gate todo.md §4.2) : **libGDX pour la vue de jeu + une coque Android native en Kotlin** (menus Compose). Code dans `android/`, ouvert tel quel dans Android Studio. Détail d'usage : `android/README.md`.

## Modules

| Module | Contenu | Ne doit jamais dépendre de |
|---|---|---|
| `:core-physics` | Port du moteur Python : `Level` (JSON livré v2), `Simulation` (un pas = `DT`), `Shapes`, `Handlers`, `ParamGrid` | Android, libGDX |
| `:game` | libGDX (JVM) : `LevelScreen`, rendu procédural `render/` (Canvas, Quarky v2, palette) | Android (passe par `GameHost`) |
| `:app` | `MainActivity` (Compose : accueil, échelles, carte), `GameActivity` (libGDX, implémente `GameHost`), `Progress` (DataStore), `Catalog` | — |

Prévus plus tard (todo.md §4.4) : `:core-content` (chargement niveaux/Codex), `:feature-codex` (Compose).

## Règle de déterminisme (non négociable)

- **Python = création + validation ; Kotlin = exécution.** `docs/physics-spec.md` est le contrat ; en cas d'écart, le code Python fait foi.
- Toute évolution de physique passe par : moteur Python → `python3 cli.py golden` → port Kotlin → `GoldenTest` vert (positions à 1e-6 à chaque pas, même issue, mêmes Photons, mêmes contacts).
- Suivre l'ordre des opérations Python (arrondi IEEE identique) : `Math.hypot`, `Math.toRadians`, `2 * d * n`, `Math.rint` là où Python arrondit.
- La boucle de jeu exécute des **pas entiers** de `DT` (temps réel accumulé) et interpole seulement l'affichage.
- Les réglages du joueur sont **calés sur la grille `param_space`** (`ParamGrid.snap`) : c'est sur cette grille que le validateur a prouvé solvabilité et étoiles.
- Porter un concept = ses handlers dans `Handlers.forType` + ses niveaux dans `GOLDEN_LEVELS` (engine/golden.py). Un type non porté lève `UnsupportedObstacle`.

## Conventions

- `minSdk 26` (Android 8.0), `targetSdk`/`compileSdk` = exigence Play courante, portrait.
- Niveaux : jamais dupliqués dans `android/` ; la tâche `copyLevels` copie `stage3-physics-engine/levels/*.json` (pas `meta/`) dans les assets à chaque build.
- Rendu 100 % procédural (aucune image livrée) ; polices OFL (JetBrains Mono, Fira Sans) dans `app/src/main/assets/fonts/`, partagées par libGDX et Compose.
- Textes in-game en français, ton du skill `storytelling` ; rendu selon le skill `art-direction` (DA v2).
- Résultat d'un niveau = lecture d'instrument dans le panneau du bas, jamais un pop-up sur la zone de jeu.

## Budgets (todo.md §4.4)

- 16,6 ms/frame, physique ≤ 1 ms, ≤ 50 draw calls, overdraw ≤ 2,5×, **aucune allocation dans la boucle** (tableaux préalloués).
- APK < 20 Mo (beta < 12 Mo).

## Statut

POC validé côté structure : Tunnel 1 jouable, 6 autres nœuds verrouillés, pas d'audio ni de Codex. Le vrai bloom (FBO ¼ de résolution, 2 flous) et la mesure sur téléphone d'entrée de gamme restent à faire (spike §4.2).
