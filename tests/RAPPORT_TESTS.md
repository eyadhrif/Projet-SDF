# Rapport de tests

- **Date :** 2026-11-08 22:58
- **Commit :** `d660d7c + modifications non commitées`
- **Mode :** rapide (tests lents exclus ; lancer `run_tests --slow` pour la suite complète)
- **Généré par :** `tests/generer_rapport.py` (ne pas modifier à la main)

## Synthèse

| Suite | Tests | Réussis | Échecs | Erreurs | Échecs attendus | Ignorés | Durée |
|---|---|---|---|---|---|---|---|
| pytest (backend) | 281 | 281 | 0 | 0 | 0 | 0 | 132 s |
| Playwright (dashboard) | 68 | 68 | 0 | 0 | 0 | 0 | 105 s |
| **Total** | **349** | **349** | **0** | **0** | **0** | **0** | **236 s** |

✅ **Tout est vert**

« Échec attendu » : test d'un défaut connu, qui échoue comme prévu tant que le défaut n'est pas corrigé (xfail strict pour pytest, `test.fail()` pour Playwright). Si le défaut est corrigé sans retirer le marqueur, le test devient rouge.

## Détail par fichier

| Fichier | Tests | Réussis | Échecs | Échecs attendus | Ignorés | Durée |
|---|---|---|---|---|---|---|
| `dashboard.spec.js` | 68 | 68 | 0 | 0 | 0 | 105.0 s |
| `test_api.py` | 25 | 25 | 0 | 0 | 0 | 10.5 s |
| `test_build.py` | 2 | 2 | 0 | 0 | 0 | 23.9 s |
| `test_data.py` | 19 | 19 | 0 | 0 | 0 | 1.1 s |
| `test_documentation.py` | 33 | 33 | 0 | 0 | 0 | 0.1 s |
| `test_environnement.py` | 12 | 12 | 0 | 0 | 0 | 0.1 s |
| `test_features.py` | 16 | 16 | 0 | 0 | 0 | 18.7 s |
| `test_fmds.py` | 32 | 32 | 0 | 0 | 0 | 3.5 s |
| `test_health.py` | 12 | 12 | 0 | 0 | 0 | 15.8 s |
| `test_metrics.py` | 12 | 12 | 0 | 0 | 0 | 0.0 s |
| `test_report.py` | 12 | 12 | 0 | 0 | 0 | 0.8 s |
| `test_report_figures.py` | 25 | 25 | 0 | 0 | 0 | 31.0 s |
| `test_report_latex.py` | 10 | 10 | 0 | 0 | 0 | 5.2 s |
| `test_report_tables.py` | 27 | 27 | 0 | 0 | 0 | 0.3 s |
| `test_results.py` | 17 | 17 | 0 | 0 | 0 | 0.5 s |
| `test_rul_degradation.py` | 17 | 17 | 0 | 0 | 0 | 10.1 s |
| `test_rul_lstm.py` | 10 | 10 | 0 | 0 | 0 | 9.9 s |

## Couverture du code Python

Objectif : **≥ 90 %** sur `backend/pipeline/` et `backend/api/`.

| Fichier | Instructions | Non couvertes | Couverture |
|---|---|---|---|
| `backend/api/main.py` | 48 | 0 | 100 % |
| `backend/pipeline/__init__.py` | 0 | 0 | 100 % |
| `backend/pipeline/data.py` | 50 | 0 | 100 % |
| `backend/pipeline/features.py` | 63 | 0 | 100 % |
| `backend/pipeline/fmds.py` | 124 | 0 | 100 % |
| `backend/pipeline/health.py` | 36 | 0 | 100 % |
| `backend/pipeline/rul_degradation.py` | 47 | 0 | 100 % |
| `backend/pipeline/rul_lstm.py` | 97 | 1 | 99 % |
| **Total** | **465** | **1** | **99.8 %** |

Objectif atteint ✅.

## Échecs et erreurs

Aucun.

## Échecs attendus (défauts connus)

Aucun.

## Tests ignorés

Aucun.

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
