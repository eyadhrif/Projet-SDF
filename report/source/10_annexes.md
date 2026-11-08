# Annexes {-}

## Annexe A — Hypothèses et paramètres {-}

!tableau[hypotheses_parametres]

## Annexe B — Structure du dépôt {-}

```
data/raw/                      jeu C-MAPSS FD001 (train, test, RUL)
backend/
  pipeline/data.py             chargement, RUL, table de durées de vie
  pipeline/fmds.py             fiabilité, maintenabilité, disponibilité, préventif
  pipeline/features.py         capteurs, variables fenêtrées, indicateur de santé
  pipeline/health.py           classification normal / critique
  pipeline/rul_degradation.py  modèle de dégradation bayésien
  pipeline/rul_lstm.py         réseau LSTM
  run_all.py                   orchestration et export des résultats
  report_figures.py            figures du rapport
  report_tables.py             tableaux et valeurs du rapport
  api/main.py                  API FastAPI
  models/  results/            modèles sauvegardés et résultats JSON
frontend/                      tableau de bord React (src/, dist/)
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
node build.mjs --latex                             # -> latex/ (sources LaTeX)
cd latex && latexmk -xelatex main.tex               # -> main.pdf

# tests
cd ..
run_tests.bat --slow
```

La version autonome `dashboard_autonome.html` s'ouvre directement dans un navigateur, sans installation.
