# Rapport de tests

- **Date :** 2026-11-07 23:43
- **Commit :** `f1ac56d`
- **Mode :** complet (tests lents inclus : réentraînements, run_all.py complet)
- **Généré par :** `tests/generer_rapport.py` (ne pas modifier à la main)

## Synthèse

| Suite | Tests | Réussis | Échecs | Erreurs | Échecs attendus | Ignorés | Durée |
|---|---|---|---|---|---|---|---|
| pytest (backend) | 191 | 188 | 0 | 0 | 1 | 2 | 511 s |
| Playwright (dashboard) | 68 | 56 | 0 | 0 | 12 | 0 | 90 s |
| **Total** | **259** | **244** | **0** | **0** | **13** | **2** | **602 s** |

✅ **Tout est vert**

« Échec attendu » : test d'un défaut connu, qui échoue comme prévu tant que le défaut n'est pas corrigé (xfail strict pour pytest, `test.fail()` pour Playwright). Si le défaut est corrigé sans retirer le marqueur, le test devient rouge.

## Détail par fichier

| Fichier | Tests | Réussis | Échecs | Échecs attendus | Ignorés | Durée |
|---|---|---|---|---|---|---|
| `dashboard.spec.js` | 68 | 56 | 0 | 12 | 0 | 90.1 s |
| `test_api.py` | 25 | 25 | 0 | 0 | 0 | 6.5 s |
| `test_build.py` | 2 | 2 | 0 | 0 | 0 | 23.7 s |
| `test_data.py` | 15 | 15 | 0 | 0 | 0 | 0.9 s |
| `test_documentation.py` | 28 | 28 | 0 | 0 | 0 | 0.1 s |
| `test_environnement.py` | 12 | 12 | 0 | 0 | 0 | 0.1 s |
| `test_features.py` | 16 | 16 | 0 | 0 | 0 | 18.5 s |
| `test_fmds.py` | 32 | 31 | 0 | 1 | 0 | 3.2 s |
| `test_health.py` | 13 | 13 | 0 | 0 | 0 | 48.2 s |
| `test_metrics.py` | 12 | 12 | 0 | 0 | 0 | 0.0 s |
| `test_report.py` | 1 | 0 | 0 | 0 | 1 | 0.0 s |
| `test_results.py` | 14 | 13 | 0 | 0 | 1 | 215.9 s |
| `test_rul_degradation.py` | 12 | 12 | 0 | 0 | 0 | 6.7 s |
| `test_rul_lstm.py` | 9 | 9 | 0 | 0 | 0 | 187.7 s |

## Couverture du code Python

Objectif : **≥ 90 %** sur `backend/pipeline/` et `backend/api/`.

| Fichier | Instructions | Non couvertes | Couverture |
|---|---|---|---|
| `backend/api/main.py` | 48 | 0 | 100 % |
| `backend/pipeline/__init__.py` | 0 | 0 | 100 % |
| `backend/pipeline/data.py` | 32 | 0 | 100 % |
| `backend/pipeline/features.py` | 63 | 0 | 100 % |
| `backend/pipeline/fmds.py` | 124 | 0 | 100 % |
| `backend/pipeline/health.py` | 36 | 0 | 100 % |
| `backend/pipeline/rul_degradation.py` | 46 | 0 | 100 % |
| `backend/pipeline/rul_lstm.py` | 85 | 1 | 99 % |
| **Total** | **434** | **1** | **99.8 %** |

Objectif atteint ✅.

## Échecs et erreurs

Aucun.

## Échecs attendus (défauts connus)

- `test_fmds.py` — test_b50_exporte : B50 pas encore exporté par fmds.py (ticket A1 de la phase A)
- `dashboard.spec.js` — plusieurs tests (×4) : D6 : bouton « Précédent » et changement d'adresse
- `dashboard.spec.js` — plusieurs tests (×8) : D7 : débordement horizontal en largeur mobile

## Tests ignorés

- `test_report.py` — test_dossier_du_rapport : rapport pas encore rédigé (phase B)
- `test_results.py` — test_figures_et_tableaux_du_rapport : report/figures et report/tables seront générés en phase A (tickets A3, A4)

## Environnement

| Élément | Version |
|---|---|
| Python | 3.12.10 |
| Système | Windows 11 |
| numpy | 2.5.4 |
| pandas | 2.3.3 |
| scikit-learn | 1.9.1 |
| lifelines | 0.30.3 |
| torch | 2.15.0 |
| fastapi | 0.162.2 |
| pytest | 9.2.0 |
| Playwright | 1.65.0 |

## Relancer

```bash
run_tests.bat            # Windows (tests rapides + dashboard)
run_tests.bat --slow     # suite complète (~10 min)
./run_tests.sh [--slow]  # Linux / macOS / Git Bash
```
