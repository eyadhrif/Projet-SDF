# Projet pratique — Estimation des indices FMDS & Maintenance prédictive

**Binôme :** Eya DHRIF & Salma MOUEDDEB · **Encadrant :** M. Fayçal Ben Hmida · GMAM 3, ENSIT
**Données :** NASA C-MAPSS, sous-ensemble FD001 (turboréacteurs, une condition opératoire, un mode de défaillance — dégradation du compresseur HPC)
**Livrable :** dashboard web interactif (FastAPI + React) et son code source

---

## 1. Lancer le dashboard (2 minutes)

Les résultats sont **déjà calculés** (`backend/results/`) et le front est **déjà compilé** (`frontend/dist/`). Il suffit de Python.

```bash
cd backend
pip install fastapi uvicorn
python -m uvicorn api.main:app --port 8000
```

Ouvrir **http://localhost:8000**. La documentation de l'API (Swagger) est sur **http://localhost:8000/docs**.

**Sans aucune installation :** ouvrir `dashboard_autonome.html` dans un navigateur. C'est le même dashboard, en un seul fichier, avec les résultats intégrés (pratique pour la démo ou l'envoi par mail).

### Recalculer tous les résultats (optionnel, ~1 min sur CPU)

```bash
cd backend
pip install -r requirements.txt      # numpy>=2, pandas>=2.2, scikit-learn, lifelines, torch…
python run_all.py                    # recharge le LSTM de référence : résultats identiques
python run_all.py --reentrainer-lstm # réentraîne aussi le LSTM (~+2 min, résultats dépendants de la machine)
```

Chaque exécution écrit `results/run_info.json` : date, durée, versions des bibliothèques, graines aléatoires et mode du LSTM.

Pour retrouver exactement l'environnement testé (Windows 11, Python 3.12, CPU) : `pip install -r requirements-lock.txt`.

> **Windows : chemins trop longs.** torch installe des fichiers à des chemins très profonds. Si le projet est placé dans un dossier lui-même profond, l'installation échoue (`OSError: [Errno 2] No such file or directory … LICENSE…`) à cause de la limite de 260 caractères. Solutions : placer le projet (ou l'environnement virtuel) dans un dossier court, par exemple `C:\SdF\`, ou activer les chemins longs de Windows (`LongPathsEnabled`).

> **Reproductibilité du LSTM.** Tous les résultats sont déterministes (graines fixées), sauf l'entraînement du LSTM, qui dépend de la machine et du contexte d'exécution (calcul flottant de PyTorch sur CPU). Sur une autre machine (Windows 11, Python 3.12, torch 2.15), `run_all.py` a donné RMSE 15,64, MAE 11,89 et score NASA 477, contre 15,35, 11,22 et 485 publiés. Deux entraînements successifs dans les mêmes conditions donnent en revanche des résultats identiques. **Les résultats publiés correspondent au modèle sauvegardé `models/lstm_rul.pt`**, qui redonne exactement les prédictions de `results/rul.json` (vérifié par `tests/test_rul_lstm.py`). C'est pourquoi `run_all.py` recharge ce modèle par défaut ; l'option `--reentrainer-lstm` le réentraîne et l'écrase.

### Modifier le front (optionnel, Node 18+)

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173 (proxy vers l'API sur le port 8000)
npm run build          # -> frontend/dist, servi par FastAPI
npm run build:static   # -> frontend/dist-static/index.html (version autonome)
```

### Rapport scientifique (Version 1)

Le rapport est dans [`report/Rapport_V1_FMDS_Eya_Salma.pdf`](report/Rapport_V1_FMDS_Eya_Salma.pdf) (51 pages). Ses sources sont en Markdown avec formules LaTeX (`report/source/`), et **aucun chiffre n'y est tapé à la main** : le texte cite des valeurs générées depuis `backend/results/`.

```bash
cd backend
python report_figures.py   # -> report/figures (21 figures, PNG 300 dpi + PDF)
python report_tables.py    # -> report/tables (Markdown + LaTeX) et report/generated/valeurs.json
cd ../report
npm install
node build.mjs             # -> Rapport_V1_FMDS_Eya_Salma.pdf (vérifications comprises)
```

### Lancer les tests

```bash
pip install -r backend/requirements-dev.txt
cd frontend && npm install && npx playwright install chromium && cd ..
cd report && npm install && cd ..
run_tests.bat              # Windows : tests rapides + dashboard (Playwright)
run_tests.bat --slow       # suite complète, y compris réentraînements (~10 min)
./run_tests.sh [--slow]    # Linux / macOS / Git Bash
```

Le résultat est écrit dans [`tests/RAPPORT_TESTS.md`](tests/RAPPORT_TESTS.md) : nombre de tests, réussites, échecs, durée, couverture du code et défauts connus.

---

## 2. Structure du projet et répartition (plan de sprints)

```
data/raw/                      C-MAPSS FD001 : train, test, RUL
backend/
  pipeline/data.py             SET-02  Chargement, calcul du RUL, table de durées de vie       Salma
  pipeline/fmds.py             FMDS-01 Fiabilité : KM, Nelson-Aalen, Weibull MCO / MV, KS     Eya
                               FMDS-02 Maintenabilité, MTBF/MTTR, disponibilité, préventif     Salma
  pipeline/features.py         PDM-01  Sélection des capteurs, features, indicateur de santé  Salma
  pipeline/health.py           PDM-02  Classification normal / critique                       Eya
  pipeline/rul_degradation.py  RUL-01  Modèle de dégradation bayésien                         Eya
  pipeline/rul_lstm.py         RUL-02  Modèle LSTM (PyTorch)                                  Salma
  run_all.py                   RUL-03  Orchestration, comparaison, export JSON                 Eya + Salma
  report_figures.py                    Figures du rapport (depuis les JSON)                    Eya + Salma
  report_tables.py                     Tableaux et valeurs du rapport (depuis les JSON)        Eya + Salma
  api/main.py                  WEB-01  API FastAPI : /api/fmds, /api/health, /api/rul, /api/engines/{id}   Eya
  models/                      Modèles sérialisés (joblib, .pt)
  results/                     Résultats JSON consommés par le dashboard
frontend/src/                  WEB-02  React + Recharts : 4 pages                             Salma
report/                        Rapport V1 : source/, figures/, tables/, build.mjs, PDF        Eya + Salma
tests/                         Suite de tests pytest (+ frontend/tests : Playwright)
```

---

## 3. Méthodologie et résultats

### 3.1 Fiabilité (FMDS-01)

**Données de durée de vie :** 200 moteurs.
- Les 100 moteurs d'entraînement ont une défaillance observée (statut = 1)
- Les 100 moteurs de test sont encore en service au dernier cycle. Ils sont traités comme des **données censurées à droite** (statut = 0)

| Méthode | Résultat |
|---|---|
| Kaplan-Meier (IC 95 % log-log) | Médiane = 202 cycles, MTTF (aire sous KM) = 214 cycles |
| Nelson-Aalen + lissage par noyau | λ(t) nul avant ~125 cycles puis croissant |
| Weibull 2P par **MCO** (rangs de Bernard) | β = 5,52, η = 223,4, R² = 0,894 |
| Weibull 2P par **MV** | β = 4,41, η = 225,0, **test KS p = 0,013, rejeté** |
| Weibull 2P par MV avec censure | β = 4,82 [4,22 ; 5,42], η = 236,6 |
| **Weibull 3P par MV (retenue)** | **β = 1,83, η = 91,3, γ = 125,2 cycles**, KS p = 0,32, accepté |

**Choix du modèle.** Le diagramme de Weibull est **courbé** (R² = 0,89), et aucune défaillance ne survient avant 128 cycles. Ces deux signes indiquent un **paramètre de position γ > 0**.

La Weibull 3P et la log-normale sont équivalentes (ΔAIC < 1). On retient la Weibull 3P pour deux raisons :
- γ a une interprétation physique : c'est la durée sans défaillance garantie
- β = 1,83 > 1 indique un **taux de défaillance croissant**, donc une usure

**Indicateurs :**
- MTTF = γ + η·Γ(1 + 1/β) = **206,3 cycles**
- B1 = 133 cycles
- B10 = 152 cycles
- B50 = 199,9 cycles (durée médiane : la moitié des moteurs a défailli)

### 3.2 Maintenabilité, disponibilité, stratégie (FMDS-02)

**Hypothèse (C-MAPSS n'a pas de temps de réparation) :**
- Les temps de réparation sont simulés selon une loi log-normale (médiane 16 h, σ = 0,6, graine fixe)
- La conversion utilisée est 1 cycle ≈ 1 vol ≈ 2 h

**Maintenabilité :** loi ré-estimée par MV, μ = 2,742, σ = 0,464, KS p = 0,61.
- **MTTR = 17,3 h** (8,6 cycles)
- t90 = 28,1 h

**Disponibilité intrinsèque :** A = MUT / (MUT + MDT) = **95,98 %**. A(t) est calculée avec le modèle markovien à 2 états.

**Remplacement préventif à âge fixe :**
- Politique de Barlow-Proschan, avec Cc = 5·Cp
- Âge optimal **T\* ≈ 131 cycles**, avec R(T\*) = 0,994
- Coût par cycle réduit de **68 %** par rapport à la maintenance corrective seule

### 3.3 Indicateur de santé et détection (PDM-01, PDM-02)

**Sélection des capteurs :**
- 7 capteurs constants sont écartés : s1, s5, s6, s10, s16, s18, s19
- **12 capteurs pronostiques** sont retenus, avec |corrélation avec le temps| ≥ 0,5 : s2, s3, s4, s7, s8, s11, s12, s13, s15, s17, s20, s21

**Features :** moyenne, écart-type et pente sur une fenêtre glissante de 10 cycles.

**Indicateur de santé (HI) :**
- Fusion linéaire des capteurs, avec une cible 1 en début de vie (10 %) et 0 en fin de vie (10 %)
- Lissage glissant
- Le HI passe d'environ 0,94 à environ 0 à la défaillance

**Classification « critique » (RUL ≤ 30 cycles) :**
- Validation croisée **par groupes de moteurs** (GroupKFold), pour éviter toute fuite d'information

| Modèle | AUC (CV) | AUC (test) | Rappel (test) |
|---|---|---|---|
| **Gradient Boosting** | 0,990 | **0,991** | 0,657 |
| SVM (RBF) | 0,983 | 0,974 | 0,621 |

### 3.4 Durée de vie résiduelle (RUL-01, RUL-02, RUL-03)

**Modèle de dégradation (Eya)**, bayésien et interprétable :
1. HI(t) est modélisé par un polynôme de degré 2
2. La loi a priori des coefficients est apprise sur la flotte des 100 moteurs d'entraînement
3. Pour chaque moteur, une mise à jour bayésienne conjuguée intègre ses propres mesures
4. 1000 trajectoires sont simulées, avec un seuil de défaillance incertain
5. Le premier passage sous le seuil donne la **distribution du RUL** (médiane et intervalle 10–90 %)

**LSTM (Salma) :**
- 12 capteurs normalisés, fenêtres de 30 cycles
- Cible plafonnée à 125 cycles
- 2 couches LSTM de 64 unités, Adam, arrêt précoce sur 15 moteurs de validation

| Modèle (100 moteurs de test) | RMSE | MAE | Biais | Score NASA |
|---|---|---|---|---|
| Dégradation bayésienne | 24,47 | 18,98 | +13,5 | 3743 |
| **LSTM** | **15,35** | **11,22** | +2,2 | **485** |
| Moyenne des deux | 16,91 | 13,49 | +7,9 | 600 |

**Lecture.**
- Le LSTM est le plus précis. Son RMSE ≈ 15 est dans l'ordre de grandeur de la littérature sur FD001
- Le modèle de dégradation est moins précis mais **explicable**, et donne un **intervalle de confiance**

**Limites.**
- Le modèle de dégradation est biaisé vers des prédictions tardives (+13,5 cycles)
- Son intervalle 10–90 % ne couvre le RUL réel que dans 54 % des cas, ce qui veut dire que l'incertitude est sous-estimée
- Calibration (A6, sans changer le modèle) : couverture de 35 % pour l'intervalle 25–75 % et de 59 % pour 5–95 % ; biais le plus fort (+21,4 cycles) pour un RUL réel entre 50 et 100 cycles
- La Weibull 3P retenue est ajustée sur les seules défaillances, sans les moteurs censurés (voir le rapport, chapitre 8)
- **Piste d'amélioration :** remplacer le polynôme par un modèle exponentiel, comme `exponentialDegradationModel` de la PdM Toolbox

---

## 4. Pages du dashboard

1. **Vue d'ensemble :** KPI, distribution des durées de vie, état de la flotte, priorités d'intervention
2. **Fiabilité & FMDS :**
   - KM avec IC, censures et modèles paramétriques
   - Diagramme de Weibull (MCO), λ(t), adéquation des lois
   - Fiabilité conditionnelle, M(t), A(t)
   - Remplacement préventif optimal
3. **Monitoring santé :**
   - Sélection des capteurs, signaux bruts, HI de la flotte
   - Performances, ROC, matrice de confusion
   - Suivi d'un moteur au choix
4. **Durée de vie résiduelle :**
   - Métriques, prédit vs réel, erreurs
   - Prédictions pour les 100 moteurs
   - Trajectoire du RUL et projection du HI pour un moteur, apprentissage du LSTM, tableau de flotte

## Références

- A. Saxena, K. Goebel, *Turbofan Engine Degradation Simulation Data Set*, NASA Ames Prognostics Data Repository, 2008
- A. Saxena et al., *Damage propagation modeling for aircraft engine run-to-failure simulation*, PHM 2008
- F. Ben Hmida, *Estimation des indices FMDS*, support de cours ENSIT, 2025
- J. Coble, J. W. Hines, *Identifying optimal prognostic parameters from data*, PHM 2009
- R. E. Barlow, F. Proschan, *Mathematical Theory of Reliability*, 1965
