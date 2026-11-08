# Handoff — Projet SdF : Estimation des indices FMDS & Maintenance prédictive

Context file for Claude Code. Read this first before touching the project.

## 1. Context

- **Students:** Eya DHRIF and Salma MOUEDDEB (binôme), GMAM 3 at ENSIT
- **Supervisor:** Prof. Fayçal Ben Hmida, module "SdF et maintenance"
- **Deadline:** 1 November 2026, 23:59
- **Scope:** this is ONLY the binôme practical project. The second project, a group-of-6 "portfolio numérique SdF" due 6 Dec 2026, has NOT been started and is not in this repo
- **Spec:** the professor's zip `Docs_étudiants_Projets SdF` has no formal project statement. It contains the course slides (`Estimation indices FMDS_vf.pdf`), dataset notes and example MATLAB/Python scripts. The students' own sprint plan (`Plan_Sprints_Salma_Eya.pdf`) is the spec:
  - React + FastAPI dashboard
  - FMDS indices
  - Health-state detection
  - RUL estimation with one model per student
  - Dataset: NASA C-MAPSS FD001
- **Language:** all UI, comments and README are in French

## 2. Status: complete and verified

- Pipeline, API and dashboard all run end to end
- Tested from a clean unzip: API returns 200, Swagger works, the standalone HTML opens offline with no console errors
- Work follows `PROMPT_MAITRE_RAPPORT.md` (Phase 0 tests → Phase A code consolidation → Phase B report). Commit messages in French, one commit per step
- **All three phases of `PROMPT_MAITRE_RAPPORT.md` are done** (merged into `main`, tag `v1.0-rapport`):
  - Phase 0: full test suite (pytest + Playwright), `tests/RAPPORT_TESTS.md`; coverage ≈ 100 % on `backend/pipeline` and `backend/api`
  - Defects fixed: D1/D2 API path traversal and unknown `/api/…` routes (now 404); D3 wrong SVM recall in README (0.621); D4 LSTM not reproducible across machines (committed `models/lstm_rul.pt` is the reference); D5 minimum versions + `backend/requirements-lock.txt`; D6 Back button (`hashchange` listener in `App.jsx`); D7 horizontal overflow at 390 px (`minmax(0, 1fr)`)
  - Phase A: A1 B50 (199.9) exported and shown; A2 `results/dataset.json` + `.csv`; A3 `backend/report_figures.py` → `report/figures` (21 figures); A4 `backend/report_tables.py` → `report/tables` (11 tables, md + tex) and `report/generated/valeurs.json`; A5 `run_all.py` reloads the reference LSTM by default (`--reentrainer-lstm` to retrain), seeds documented, `results/run_info.json`; A6 degradation calibration (coverage 35/54/59 % at nominal 50/80/90 %, bias by RUL range) in `rul.json` and on the RUL page
  - Phase B: `report/Rapport_V1_FMDS_Eya_Salma.pdf` (51 pages), built from `report/source/*.md` by `report/build.mjs` (marked + KaTeX → HTML → PDF with Chromium). No LaTeX distribution on the PC; downloading Tectonic was blocked. Report numbers are never typed by hand: the text cites `{{key}}` from `valeurs.json`, enforced by `tests/test_report.py`
  - Limit found while writing: the retained Weibull 3P is fitted on the 100 failures only (no censoring); discussed in the report, chapter 8
- **Report change workflow:** edit code → `python run_all.py` → `python report_figures.py` → `python report_tables.py` → rebuild `frontend` (`npm run build` and `build:static`, copy to `dashboard_autonome.html`) → `node report/build.mjs` → `run_tests.bat --slow`. Tests fail if any generated file is stale
- **Machine note:** Avast and 360 antivirus run on Eya's PC; on 8 Nov 2026 the fast test suite took 55 min instead of ~75 s for one run (probably file scanning)
- **Linux install verified** (8 Nov 2026) in WSL Ubuntu, Python 3.12: clean clone + `pip install -r backend/requirements-lock.txt --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple`; fast suite 267 passed (3 skipped: no Node in WSL); `run_all.py` identical to Windows except one per-cycle LSTM value in `engines.json` (39.0 vs 38.9, float rounding). `python3.12-venv` was installed in WSL as root for this
- **Pushed to GitHub** `origin` = https://github.com/eyadhrif/Projet-SDF (main, corrections-defauts, tag v1.0-rapport). Salma still has to be invited (needs her GitHub username)
- **Deliverables folder updated** (`Docs_étudiants_Projets SdF`): new zip (`git archive` of v1.0-rapport), dashboard_autonome.html, Rapport_V1 PDF, CLAUDE.md; old files kept as `*_ancien_2026-11-01`
- **Windows long paths:** torch 2.15 fails to install in a deep folder (260-char limit, `LongPathsEnabled = 0` on Eya's PC). Keep the venv in a short path
- **Not yet on GitHub.** The plan is a private repo `eyadhrif/SdF-FMDS-Maintenance-Predictive`, then invite Salma as a collaborator with Write access. Creating the repo from the cloud session was blocked, so Eya creates it empty on github.com, then push:
  ```bash
  git remote add origin https://github.com/eyadhrif/SdF-FMDS-Maintenance-Predictive.git
  git push -u origin main
  ```
- **Deliverables on Eya's PC**, in `C:\Users\ASUS\Documents\3_éme_GMAM\Fm\SDF\Docs_étudiants_Projets SdF\`:
  - `Projet_FMDS_Eya_Salma.zip` — full project
  - `dashboard_autonome.html` — single-file dashboard with the data built in
- **Email issue:** Gmail blocks zips that contain `.js` files. Send the zip as a Google Drive link or a GitHub link, and attach `dashboard_autonome.html` directly

## 3. Structure (ownership follows the sprint plan)

```
data/raw/                     train_FD001.txt, test_FD001.txt, RUL_FD001.txt (from a GitHub mirror)
backend/
  pipeline/data.py            SET-02  loader, RUL labels, lifetime table              Salma
  pipeline/fmds.py            FMDS-01 KM, Nelson-Aalen, Weibull MCO/MV, KS, AIC      Eya
                              FMDS-02 maintainability, MTBF/MTTR, availability,
                                      age-replacement policy                         Salma
  pipeline/features.py        PDM-01  sensor selection, window features, HI          Salma
  pipeline/health.py          PDM-02  normal/critical classifier                      Eya
  pipeline/rul_degradation.py RUL-01  Bayesian degradation model                     Eya
  pipeline/rul_lstm.py        RUL-02  LSTM (PyTorch)                                 Salma
  run_all.py                  RUL-03  runs everything, writes results/*.json (~2 min CPU)
  api/main.py                 WEB-01  FastAPI: /api/fmds /api/health /api/rul /api/engines/{id} /api/fleet
                                      also serves frontend/dist at /
  models/                     health_clf.joblib, health_indicator.joblib, degradation_model.joblib, lstm_rul.pt
  results/                    fmds.json, health.json, rul.json, engines.json
frontend/                     WEB-02  Vite + React 18 + Recharts 2
  src/api.js                  fetches /api/*; in "static" mode it bundles results/*.json instead
  src/pages/                  Overview, Fiabilite, Monitoring, Rul
  dist/                       built app served by FastAPI
  tests/dashboard.spec.js     Playwright: 4 pages × (server, standalone file://) × (1440 px, 390 px)
dashboard_autonome.html       = frontend/dist-static/index.html (vite-plugin-singlefile)
README.md                     French: run steps, method, results tables, limits, references
tests/                        pytest suite, one file per module (+ test_api, test_results, test_build,
                              test_documentation, test_environnement, test_metrics, test_report)
  conftest.py                 shared fixtures (fd001, results, sprint2, client)
  generer_rapport.py          writes tests/RAPPORT_TESTS.md from JUnit XML + coverage JSON
  RAPPORT_TESTS.md            latest test report (regenerate and commit with every ticket)
run_tests.bat / run_tests.sh  run everything (add --slow for retraining + full run_all.py)
pytest.ini                    marker `slow`, pythonpath = backend
report/                       Phase B report: source/*.md, figures/ (A3), tables/ (A4), generated/valeurs.json,
                              captures/ (dashboard screenshots), bibliographie.json, build.mjs, CHANGELOG.md,
                              Rapport_V1_FMDS_Eya_Salma.pdf
```

### Run

```bash
cd backend
pip install fastapi uvicorn
python -m uvicorn api.main:app --port 8000      # http://localhost:8000
python run_all.py                               # recompute (needs requirements.txt); --reentrainer-lstm to retrain the LSTM

cd frontend
npm install
npm run dev                                     # or: npm run build / npm run build:static
```

After rebuilding the static version, copy `frontend/dist-static/index.html` to `dashboard_autonome.html`.

`run_all.py` (A5) reloads the reference LSTM `models/lstm_rul.pt` by default, so all 4 JSON files come out byte-identical (~1 min); `--reentrainer-lstm` retrains and overwrites it (machine-dependent numbers). Every run writes `results/run_info.json` (date, duration, library versions, seeds, LSTM mode). Slow tests in `tests/test_results.py` check both modes in a temp copy.

### Tests

```bash
# environment: Python 3.12 venv at the repo root (.venv/, git-ignored)
pip install -r backend/requirements-dev.txt     # or backend/requirements-lock.txt for exact versions
cd frontend && npm install && npx playwright install chromium && cd ..
run_tests.bat            # fast pytest + Playwright, then tests/RAPPORT_TESTS.md
run_tests.bat --slow     # full suite (~10 min)
```

Rules: never change a test to make it pass without a written reason; known defects use strict xfail (pytest) or `test.fail()` (Playwright), so fixing the defect turns the marker red and forces its removal. `tests/test_build.py` fails if `frontend/dist` or `dashboard_autonome.html` is not rebuilt after a front change.

## 4. Key decisions (keep consistent if editing)

- **Censoring:** the 100 train engines are failures (status 1). The 100 test engines are right-censored at their last observed cycle (status 0), giving 200 units for Kaplan-Meier
- **Reliability model:**
  - Weibull 2P fitted by MCO (Bernard median ranks) gives β 5.52, η 223.4, R² 0.894
  - Weibull 2P fitted by MV gives β 4.41, η 225.0, and is REJECTED by KS (p = 0.013)
  - **Weibull 3P is retained:** β 1.83, η 91.3, γ 125.2, KS p = 0.32
  - Log-normal is equivalent (ΔAIC < 1). Weibull 3P is chosen because γ means a guaranteed failure-free period: no engine fails before 128 cycles
  - Results: MTTF 206.3 cycles, B10 152, B1 133 (B50 = 199.9 is computed but not yet exported: ticket A1)
- **Repair times are SIMULATED** because C-MAPSS has none: log-normal with median 16 h, σ 0.6, seed 42, and 1 cycle ≈ 2 h
  - Gives MTTR 17.3 h, availability A = 95.98 %
  - Age-replacement policy with Cc = 5·Cp gives T* ≈ 131 cycles and a 68 % cost saving
  - These assumptions are clearly stated in the README and on the dashboard
- **Sensors:**
  - 7 constant sensors dropped: s1, s5, s6, s10, s16, s18, s19
  - 12 kept (|trend| ≥ 0.5): s2, s3, s4, s7, s8, s11, s12, s13, s15, s17, s20, s21
- **Health indicator:** linear regression with target 1 for the first 10 % of life and 0 for the last 10 %, then a rolling mean over 10 cycles
- **Classifier:**
  - "Critical" means RUL ≤ 30 cycles
  - Validated with GroupKFold by engine
  - HistGradientBoosting: test AUC 0.991, recall 0.657
  - SVM (RBF, calibrated): test AUC 0.974
- **RUL:**

  | Model | RMSE | MAE | NASA score |
  |---|---|---|---|
  | Degradation (Eya): quadratic HI, fleet Gaussian prior, conjugate update, 1000 draws, random threshold | 24.47 | 18.98 | 3743 |
  | LSTM (Salma): 2×64, window 30, cap 125, early stopping | **15.35** | 11.22 | 485 |

- **Known limits (documented honestly in the README):**
  - The degradation model predicts too late, with a bias of +13.5 cycles
  - Its 10–90 % interval covers the true RUL only 54 % of the time
  - Suggested fix: an exponential degradation model

## 5. Possible next steps

1. Invite Salma on GitHub (repository already pushed)
2. Send the report PDF, the standalone dashboard and the repository link to the professor
3. Version 2 of the report (see `report/CHANGELOG.md` and the report's Perspectives chapter): exponential / Wiener degradation model, calibrated intervals, Weibull 3P fitted with censoring, FD002/FD004
4. Later and separate: the group portfolio (due 6 Dec), using `Feuille de route pour portfolio numérique_2025.pdf`

## 6. Notes

- **Environment:** Python ≥ 3.10 with numpy ≥ 2 (uses `np.trapezoid`) and pandas ≥ 2.2. Developed on Python 3.13, sklearn 1.9, lifelines 0.30, torch 2.15
- **Ownership:** Eya and Salma each need to understand and present their own tickets at the demo. Keep the per-file ownership labels
