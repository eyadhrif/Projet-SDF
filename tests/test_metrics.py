"""RUL-03 — Tests des métriques de RUL : score NASA (run_all.nasa_score), RMSE, MAE, biais.

Erreur d = RUL prédit − RUL réel (d > 0 : prédiction tardive, donc dangereuse).
Score NASA (Saxena et al., 2008) : exp(−d/13) − 1 si d < 0, exp(d/10) − 1 sinon.
"""
import numpy as np
import pytest

from run_all import nasa_score


def rmse(p, t):
    return float(np.sqrt(np.mean((np.asarray(p) - np.asarray(t)) ** 2)))


def test_score_nul_si_prediction_parfaite():
    assert nasa_score([10, 50, 100], [10, 50, 100]) == 0


def test_score_cas_calcules_a_la_main():
    e = np.e - 1                                        # exp(1) − 1 = 1,71828…
    assert nasa_score([37], [50]) == pytest.approx(e)   # en avance de 13 : exp(13/13) − 1
    assert nasa_score([60], [50]) == pytest.approx(e)   # en retard de 10 : exp(10/10) − 1
    assert nasa_score([37, 60], [50, 50]) == pytest.approx(2 * e)


@pytest.mark.parametrize("d", [1, 5, 10, 30])
def test_score_asymetrique_retard_plus_couteux(d):
    assert nasa_score([100 + d], [100]) > nasa_score([100 - d], [100]) > 0


def test_rmse_mae_biais_a_la_main():
    pred, true = np.array([37, 60]), np.array([50, 50])     # erreurs −13 et +10
    assert rmse(pred, true) == pytest.approx(np.sqrt((169 + 100) / 2))
    assert np.mean(np.abs(pred - true)) == 11.5
    assert np.mean(pred - true) == -1.5


@pytest.mark.parametrize("model", ["deg", "lstm", "ensemble"])
def test_metriques_du_json_recalculees(results, model):
    t = results["rul"]["table"]
    true = np.array([r["true"] for r in t], float)
    if model == "ensemble":
        pred = np.array([(r["deg"] + r["lstm"]) / 2 for r in t])
    else:
        pred = np.array([r[model] for r in t], float)
    e = pred - true
    m = results["rul"]["metrics"][model]
    assert round(rmse(pred, true), 2) == m["rmse"]
    assert round(float(np.mean(np.abs(e))), 2) == m["mae"]
    assert round(float(np.mean(e)), 2) == m["bias"]
    assert round(nasa_score(pred, true), 1) == m["score"]
    assert round(100 * float(np.mean(np.abs(e) <= 15)), 1) == m["within15"]
    assert round(100 * float(np.mean(e > 0)), 1) == m["late_pct"]


def test_non_regression_rul(results):
    m = results["rul"]["metrics"]
    assert (m["deg"]["rmse"], m["deg"]["mae"]) == (24.47, 18.98)
    assert m["deg"]["score"] == pytest.approx(3743, abs=0.5)
    assert m["lstm"]["rmse"] == pytest.approx(15.35, abs=0.5)        # LSTM : dépend du matériel (§0.3)


def test_histogramme_des_erreurs(results):
    h = results["rul"]["error_hist"]
    assert [b["bin"] for b in h] == [str(x) for x in range(-80, 80, 10)]
    t = results["rul"]["table"]
    for k in ("deg", "lstm"):
        e = np.array([r[k] - r["true"] for r in t])
        assert sum(b[k] for b in h) == int(np.sum((e >= -80) & (e < 80)))
