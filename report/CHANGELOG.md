# Journal des versions du rapport

Chaque version a un tag git (`v1.0-rapport`, `v2.0-rapport`, `v3.0-rapport`). Le rapport de tests joint à chaque version est `tests/RAPPORT_TESTS.md`, à l'état du tag.

## Version 1 — « Comprendre et démontrer » (tag `v1.0-rapport`)

Première version du rapport scientifique, fondée uniquement sur les travaux réalisés, les modèles implémentés et les résultats obtenus.

### Ajouté

- Rapport complet (`Rapport_V1_FMDS_Eya_Salma.pdf`) : introduction, état de l'art, données, méthodologie, architecture, protocole, résultats, discussion, perspectives, conclusion, bibliographie et annexes.
- Chaîne de construction `build.mjs` (Markdown + KaTeX → HTML → PDF) avec vérifications : valeurs, figures, tableaux, renvois et références tous résolus et tous cités.
- Figures (`report/figures`, ticket A3) et tableaux (`report/tables`, ticket A4) générés depuis `backend/results/*.json`.
- Valeurs citées dans le texte générées depuis les résultats (`report/generated/valeurs.json`) : aucun chiffre tapé à la main.

### Modifié dans le code pour cette version (phase A)

- A1 : B50 exporté et affiché sur le dashboard.
- A2 : description du jeu de données (`results/dataset.json` et `.csv`).
- A5 : reproductibilité — LSTM de référence rechargé par défaut, graines documentées, `results/run_info.json`.
- A6 : calibration des intervalles et du biais du modèle de dégradation (sans modifier le modèle).
- Défauts corrigés avant la rédaction : D1 à D7 (API, README, versions, reproductibilité, navigation et affichage mobile du dashboard).

### Écarts de chiffres par rapport à l'état initial

- Aucun chiffre de la section 1 du prompt maître n'a changé : tous sont reproduits à l'identique par le code.
- Nouvelles valeurs : B50 = 199,9 cycles (jusque-là calculée à la main) ; couvertures empiriques de 35 %, 54 % et 59 % pour les intervalles nominaux de 50 %, 80 % et 90 %.

### Limites identifiées, à traiter dans les versions suivantes

- Biais (+13,5 cycles) et sous-couverture du modèle de dégradation.
- Loi de Weibull 3P ajustée sans les moteurs censurés.
- Temps de réparation et coûts simulés ; un seul sous-ensemble (FD001).

## Version 2 — « Approfondir et améliorer » (prévue)

Pistes prioritaires, détaillées au chapitre Perspectives : modèle de dégradation exponentiel ou à processus de Wiener, intervalles recalibrés, Weibull 3P avec censure et intervalles de confiance des durées B10 et B50, extension à FD002 et FD004, explicabilité.

## Version 3 — « Consolider et industrialiser » (prévue)

Optimisation de la planification, étude économique, données industrielles réelles, déploiement.
