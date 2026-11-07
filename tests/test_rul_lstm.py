"""RUL-02 — Tests du modèle LSTM (backend/pipeline/rul_lstm.py).

Référence (D4) : le réentraînement du LSTM n'est pas reproductible d'une machine à l'autre
(calcul flottant de torch sur CPU). La référence est donc le modèle commité models/lstm_rul.pt,
qui doit redonner exactement les prédictions de results/rul.json. Le réentraînement complet
n'est vérifié qu'avec une tolérance (test lent).
"""
import numpy as np
import pandas as pd
import pytest
import torch

from conftest import MODELS
from pipeline.rul_lstm import LSTMRUL, LSTMRegressor, SEQ, RUL_CAP


def charger_lstm(path=MODELS / "lstm_rul.pt"):
    ck = torch.load(path, weights_only=False)
    m = LSTMRUL(ck["sensors"])
    m.lo, m.hi = pd.Series(ck["lo"]), pd.Series(ck["hi"])
    m.model = LSTMRegressor(len(ck["sensors"]))
    m.model.load_state_dict(ck["state"])
    return m


@pytest.fixture(scope="module")
def lstm():
    return charger_lstm()


def rmse(p, t):
    return float(np.sqrt(np.mean((np.asarray(p) - np.asarray(t)) ** 2)))


# ------------------------------------------------------------- formes et entrées
def test_formes_des_fenetres(lstm, fd001):
    train, _, _ = fd001
    g = train[train.unit == 1]
    X, y = lstm._windows(lstm._norm(g), np.minimum(g.RUL.values, RUL_CAP))
    assert X.shape == (len(g) - SEQ + 1, SEQ, 12)
    assert y.shape == (len(g) - SEQ + 1,)
    assert y.max() <= RUL_CAP


def test_serie_courte_remplie_par_la_premiere_ligne(lstm):
    X = np.arange(12 * 5, dtype=np.float32).reshape(5, 12)       # 5 cycles < 30
    W, _ = lstm._windows(X)
    assert W.shape == (1, SEQ, 12)
    np.testing.assert_array_equal(W[0, :SEQ - 5], np.repeat(X[:1], SEQ - 5, 0))
    np.testing.assert_array_equal(W[0, SEQ - 5:], X)


def test_sortie_positive(lstm, fd001):
    _, test, _ = fd001
    for _, g in list(test.groupby("unit"))[:10]:
        _, p = lstm.predict_unit(g)
        assert (p >= 0).all()


# ------------------------------------------------------------- référence commitée (D4)
def test_modele_sauvegarde_redonne_les_predictions_du_json(lstm, fd001, results):
    _, test, _ = fd001
    ref = {row["unit"]: row["lstm"] for row in results["rul"]["table"]}
    for u, g in test.groupby("unit"):
        _, p = lstm.predict_unit(g)
        assert round(float(p[-1]), 1) == pytest.approx(ref[int(u)], abs=0.05), f"moteur {u}"


def test_metriques_lstm_de_reference(results):
    t = results["rul"]["table"]
    pred, true = [r["lstm"] for r in t], [r["true"] for r in t]
    m = results["rul"]["metrics"]["lstm"]
    assert rmse(pred, true) == pytest.approx(m["rmse"], abs=0.005)
    assert m["rmse"] == pytest.approx(15.35, abs=0.005)
    assert m["mae"] == pytest.approx(11.22, abs=0.005)
    assert m["bias"] == pytest.approx(2.19, abs=0.005)
    assert m["score"] == pytest.approx(484.7, abs=0.05)


def test_sauvegarde_puis_rechargement_identique(lstm, fd001, tmp_path):
    _, test, _ = fd001
    lstm.save(tmp_path / "m.pt")
    m2 = charger_lstm(tmp_path / "m.pt")
    g = test[test.unit == 7]
    np.testing.assert_array_equal(lstm.predict_unit(g)[1], m2.predict_unit(g)[1])


# ------------------------------------------------------------- apprentissage
def test_mini_entrainement(fd001):
    """Entraînement court (rapide) : historique rempli, état restauré, prédictions finies."""
    train, _, _ = fd001
    sub = train[train.unit <= 20]
    m = LSTMRUL(["s2", "s3", "s4", "s7", "s8", "s11", "s12", "s13", "s15", "s17", "s20", "s21"])
    m.fit(sub, epochs=2, patience=1, log=lambda *a: None)
    assert 1 <= len(m.history) <= 2
    assert np.isfinite(m.best_val_rmse)
    _, p = m.predict_unit(sub[sub.unit == 1])
    assert np.isfinite(p).all()


def test_arret_precoce(fd001):
    train, _, _ = fd001
    sub = train[train.unit <= 20]
    m = LSTMRUL(["s2", "s3", "s4", "s7", "s8", "s11", "s12", "s13", "s15", "s17", "s20", "s21"])
    m.fit(sub, epochs=50, patience=1, lr=0.0, log=lambda *a: None)   # lr nul : aucune amélioration
    assert len(m.history) == 2


@pytest.mark.slow
def test_reentrainement_complet_dans_la_tolerance(fd001, results):
    """Réentraînement complet : RMSE de test dans [13 ; 18] (§0.5) et à ±0,5 de la référence (§0.3)."""
    train, test, _ = fd001
    sel = results["health"]["selected"]
    m = LSTMRUL(sel).fit(train.copy(), log=lambda *a: None)
    pred = [m.predict_unit(g)[1][-1] for _, g in test.groupby("unit")]
    true = test.groupby("unit").RUL.last().values
    e = rmse(pred, true)
    assert 13 <= e <= 18
    assert e == pytest.approx(results["rul"]["metrics"]["lstm"]["rmse"], abs=0.5)
