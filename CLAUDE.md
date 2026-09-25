# Quark & Cosmos

Jeu mobile Android de puzzle physique (nom de code provisoire). Le joueur traverse 5 échelles de l'univers (Quantique → Atomique/Moléculaire → Macro → Spatiale → Cosmologique), chaque loi physique devenant une mécanique de puzzle tactile.

## Méthodologie

Avancer strictement stage par stage (1: DA/UI-UX, 2: mockup HTML/JS, 3: moteur physique Python/CLI, 4: audio, 5: architecture Android). Ne jamais produire de code ou de spec pour une étape future tant que l'étape en cours n'est pas validée par l'utilisateur.

## Portée de la version test fermée

Le premier build jouable (test fermé) se limite au **premier monde uniquement (échelle Quantique)**, ~1 niveau par concept ci-dessous (7 concepts → 7 niveaux, dans la fourchette 5-10). C'est une version allégée du modèle de progression complet (cf. `gameplay-mechanics`) : pas ou peu de montée en difficulté intra-concept, et **aucun niveau mixant plusieurs concepts** — cette richesse (progression complète + niveaux de mix inter-concepts) est réservée à la full release, pas à la beta.

Ordre d'introduction (numéros = ordre de jeu, pas de découverte physique) : on ouvre sur le concept le plus immédiat à lire (un seuil à franchir ou non) pour habituer le joueur au lancer en boîte fermée sans gravité, avant de lui demander de comprendre un choix de chemin.

1. Effet tunnel (barrière franchie sous condition de timing/jauge)
2. Superposition d'états (une lame sépare Quarky en deux copies fantômes qui volent en même temps ; le tap « mesure » et Quarky devient la copie la plus proche du détecteur — la cible n'accepte qu'un Quarky mesuré, donc l'interaction n'est jamais optionnelle)
3. Intrication quantique (paire liée à distance : agir sur l'un modifie l'autre instantanément)
4. Principe d'incertitude de Heisenberg (précision de visée vs contrôle de vitesse)
5. Quantification de l'énergie (lanceur à crans fixes, pas de réglage continu)
6. Spin quantique (bascule binaire influençant l'interaction avec certains champs)
7. Dualité onde-particule (bascule onde/particule ; le rebond en mode onde préfigure — sans la dupliquer — la réflexion classique qui sera pleinement enseignée en Macro avec les miroirs)

Décohérence a été retirée du périmètre de la beta (retour design : redondante avec la superposition/le détecteur n'apportait pas assez de valeur pédagogique propre). Elle reste une piste possible pour la full release si un angle plus distinct est trouvé.

Les 4 autres échelles restent hors périmètre de ce build. Toute décision de scope (Stage 3 génération de niveaux, Stage 5 architecture) doit prioriser cette portée avant d'étendre aux autres échelles.

## Skills

- `art-direction` — direction artistique validée (palette, personnage Quarky, règles visuelles, level design). À charger avant toute production visuelle ou mockup.
- `storytelling` — univers narratif validé (prémisse, ton, rôle du/de la scientifique, intégration au Codex, ordre de progression Quantique → Cosmologique). À charger avant tout texte in-game.
- `gameplay-mechanics` — boucle de jeu, contrôle d'orientation/puissance des objets, système à 3 étoiles. À charger avant toute spec de niveau ou de scoring.

D'autres skills/agents seront ajoutés au fil des stages (moteur physique, architecture Android, etc.) — le détail de chaque domaine vit dans son propre skill, pas ici.
