# Architecture et workflow du système {#sec:architecture}

## Pipeline de calcul {#sec:pipeline}

Le code Python est organisé en modules, un par ticket du plan de sprints (répartition en annexe, [@sec:annexe-repartition]). Le script `run_all.py` enchaîne toutes les étapes et exporte les résultats dans des fichiers JSON, qui sont l'unique source de vérité du tableau de bord, des figures, des tableaux et des chiffres de ce rapport :

```
data/raw/*.txt
   │  data.py           chargement, RUL, table de durées de vie, description du jeu
   ▼
fmds.py                 fiabilité, maintenabilité, disponibilité, préventif
features.py             capteurs, features fenêtrées, indicateur de santé
health.py               classification normal / critique
rul_degradation.py      modèle de dégradation bayésien
rul_lstm.py             réseau LSTM
   ▼
results/  fmds.json  health.json  rul.json  engines.json  dataset.json  run_info.json
   ├──► api/main.py (FastAPI)  ──►  tableau de bord React
   ├──► report_figures.py      ──►  report/figures   (PNG et PDF)
   └──► report_tables.py       ──►  report/tables, report/generated/valeurs.json
```

Les modèles entraînés sont sauvegardés dans `backend/models/`. Sur la machine de développement, la chaîne complète s'exécute en un peu moins d'une minute lorsque le LSTM de référence est rechargé.

## API et endpoints {#sec:api}

L'API est développée avec FastAPI (ticket WEB-01, Eya). Elle lit les fichiers JSON, les garde en mémoire et expose cinq routes en lecture :

- `/api/fmds` : indices de fiabilité, de maintenabilité et de disponibilité, et politique préventive ;
- `/api/health` : sélection des capteurs, indicateur de santé et performances des classifieurs ;
- `/api/rul` : métriques, calibration et prédictions des deux modèles de RUL ;
- `/api/fleet` : état actuel des moteurs de test (tableau de flotte) ;
- `/api/engines/{id}` : historique complet d'un moteur de test (indicateur de santé, probabilité d'état critique, RUL prédit à chaque cycle).

Un identifiant de moteur hors de la plage connue renvoie une erreur `404`, un identifiant non numérique une erreur `422`, et l'absence des résultats une erreur `503` avec un message explicite. La documentation interactive (Swagger) est générée automatiquement. La même application sert le tableau de bord compilé ; elle refuse toute requête qui tenterait de sortir du dossier du tableau de bord.

## Tableau de bord {#sec:dashboard}

Le tableau de bord (ticket WEB-02, Salma) est une application React avec des graphiques Recharts. Il comporte quatre pages : la vue d'ensemble ([@fig:dashboard_overview]), la fiabilité et les indices FMDS ([@fig:dashboard_fiab]), le suivi de l'état de santé ([@fig:dashboard_mon]) et la durée de vie résiduelle ([@fig:dashboard_rul]). Une version **autonome** en un seul fichier HTML, avec les résultats intégrés, s'ouvre sans serveur ni installation, ce qui facilite la démonstration et la diffusion.

!figure[dashboard_overview](Page « Vue d'ensemble » : indicateurs clés, distribution des durées de vie, état de la flotte en service et priorités d'intervention.)

!figure[dashboard_fiab](Page « Fiabilité & FMDS » : fonction de fiabilité, paramètres estimés, adéquation des lois, maintenabilité, disponibilité et politique préventive.)

!figure[dashboard_mon](Page « Monitoring santé » : sélection des capteurs, indicateur de santé, performances de la classification et suivi d'un moteur.)

!figure[dashboard_rul](Page « Durée de vie résiduelle » : métriques des deux modèles, prédictions pour la flotte, calibration et analyse moteur par moteur.)

## Reproductibilité et qualité {#sec:reproductibilite}

Plusieurs dispositifs garantissent que chaque chiffre est reproductible et traçable :

- **graines fixées** pour toutes les étapes aléatoires (temps de réparation simulés, classifieurs, tirages du modèle de dégradation, LSTM) ;
- **modèle LSTM de référence** : un réentraînement sur une autre machine a donné un RMSE légèrement différent, dans la tolérance fixée de plus ou moins un demi-cycle. Les résultats publiés correspondent donc au modèle sauvegardé, que `run_all.py` recharge par défaut ; toutes les autres étapes sont déterministes, et deux exécutions produisent des fichiers JSON identiques. Une installation propre sous Linux redonne les mêmes résultats ; seule une prédiction intermédiaire du LSTM y diffère d'une unité d'arrondi, sans effet sur aucune métrique ;
- **traçabilité** : chaque exécution écrit la date, la durée, les versions des bibliothèques et les graines dans `run_info.json`. Les résultats de ce rapport ont été produits avec Python {{python}}, NumPy {{v_numpy}}, pandas {{v_pandas}}, scikit-learn {{v_sklearn}}, lifelines {{v_lifelines}} et PyTorch {{v_torch}} ;
- **suite de tests automatiques** (pytest pour le calcul et l'API, Playwright pour le tableau de bord). Elle vérifie les méthodes sur des cas dont la réponse est connue, la non-régression de chaque chiffre, l'absence de fuite entre moteurs, la cohérence entre l'API, les fichiers et le tableau de bord, et la concordance de chaque nombre de ce rapport avec sa source.
