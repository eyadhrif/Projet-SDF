# Annexes {-}

## Annexe A — Hypothèses et paramètres {-}

!tableau[hypotheses_parametres]

## Annexe B — Structure du dépôt {-}

```
data/raw/                      jeu C-MAPSS FD001 (train, test, RUL)
backend/
  pipeline/data.py             SET-02   chargement, RUL, table de durées de vie, description
  pipeline/fmds.py             FMDS-01  fiabilité ; FMDS-02 maintenabilité, disponibilité, préventif
  pipeline/features.py         PDM-01   capteurs, features, indicateur de santé
  pipeline/health.py           PDM-02   classification normal / critique
  pipeline/rul_degradation.py  RUL-01   modèle de dégradation bayésien
  pipeline/rul_lstm.py         RUL-02   LSTM
  run_all.py                   RUL-03   orchestration et export des résultats
  report_figures.py            figures du rapport
  report_tables.py             tableaux et valeurs du rapport
  api/main.py                  WEB-01   API FastAPI
  models/  results/            modèles sauvegardés et résultats JSON
frontend/                      WEB-02   tableau de bord React (src/, dist/)
dashboard_autonome.html        tableau de bord autonome (un seul fichier)
report/                        rapport : source/, figures/, tables/, build.mjs
tests/                         suite de tests pytest ; frontend/tests : Playwright
```

## Annexe C — Guide de lancement {-}

```bash
# tableau de bord (résultats déjà calculés)
cd backend
pip install -r requirements.txt
python -m uvicorn api.main:app --port 8000        # http://localhost:8000

# recalcul complet, figures, tableaux
python run_all.py
python report_figures.py
python report_tables.py

# rapport (Node.js)
cd ../report
npm install
node build.mjs                                     # -> Rapport_V1_FMDS_Eya_Salma.pdf

# tests
cd ..
run_tests.bat --slow
```

La version autonome `dashboard_autonome.html` s'ouvre directement dans un navigateur, sans installation.

## Annexe D — Répartition du travail {#sec:annexe-repartition}

| Ticket | Contenu | Responsable |
|---|---|---|
| SET-02 | Chargement des données, RUL, table de durées de vie, description du jeu | Salma |
| FMDS-01 | Fiabilité : Kaplan-Meier, Nelson-Aalen, Weibull, adéquation, indicateurs | Eya |
| FMDS-02 | Maintenabilité, disponibilité, remplacement préventif | Salma |
| PDM-01 | Sélection des capteurs, features, indicateur de santé | Salma |
| PDM-02 | Classification normal / critique | Eya |
| RUL-01 | Modèle de dégradation bayésien | Eya |
| RUL-02 | Réseau LSTM | Salma |
| RUL-03 | Orchestration, comparaison, export | Eya et Salma |
| WEB-01 | API FastAPI | Eya |
| WEB-02 | Tableau de bord React | Salma |
| Rapport | Figures, tableaux, rédaction | Eya et Salma |
