"""RUL-01 (Eya) — Tests du modèle de dégradation bayésien (backend/pipeline/rul_degradation.py)."""
import joblib
import numpy as np
import pytest

from conftest import MODELS
from pipeline.rul_degradation import DegradationRUL, HORIZON, N_SAMPLES, DEG, _phi


@pytest.fixture(scope="module")
def deg():
    return joblib.load(MODELS / "degradation_model.joblib")


def modele_synthetique(w_true, sigma2=1e-8, prior_var=10.0):
    """Modèle construit à la main : a priori large centré sur 0, bruit quasi nul, seuil fixe à 0."""
    m = DegradationRUL()
    m.m0 = np.zeros(DEG + 1)
    m.S0 = prior_var * np.eye(DEG + 1)
    m.S0inv = np.linalg.inv(m.S0)
    m.sigma2, m.threshold, m.threshold_std = sigma2, 0.0, 0.0
    return m


# ------------------------------------------------------------- cas synthétiques
def test_base_polynomiale():
    P = _phi([0, 100, 200])
    np.testing.assert_allclose(P, [[1, 0, 0], [1, 1, 1], [1, 2, 4]])


def test_trajectoire_sans_bruit_rul_exact():
    """HI(t) = 1 − 0,2τ − 0,3τ², τ = t/100 : passage sous 0 en t* = 152,26 (racine positive).
    Observé jusqu'au cycle 100 : RUL vrai = 52,26 ; le modèle doit le retrouver à ±2 cycles."""
    w = np.array([1.0, -0.2, -0.3])
    t = np.arange(1, 101)
    h = _phi(t) @ w
    t_star = 100 * (-0.2 + np.sqrt(0.04 + 4 * 0.3)) / (2 * 0.3)
    p = modele_synthetique(w).predict(t, h, np.random.default_rng(0))
    assert p["rul"] == pytest.approx(t_star - 100, abs=2)
    np.testing.assert_allclose(p["m"], w, atol=1e-3)
    assert p["p90"] - p["p10"] <= 2


def test_horizon_si_le_seuil_n_est_jamais_atteint():
    t = np.arange(1, 51)
    p = modele_synthetique(None).predict(t, np.ones(50), np.random.default_rng(0))   # HI constant = 1
    assert p["rul"] == HORIZON


def test_a_posteriori_se_resserre(deg, sprint2):
    g = sprint2["test"][sprint2["test"].unit == 49]
    t, h = g.cycle.values, g.HI_raw.values
    traces = [np.trace(deg.posterior(t[:k], h[:k])[1]) for k in (5, 20, 60, len(t))]
    assert all(a > b for a, b in zip(traces, traces[1:]))
    assert traces[0] < np.trace(deg.S0)


def test_a_posteriori_sans_observation_egal_a_priori(deg):
    m, S = deg.posterior(np.array([]), np.array([]))
    np.testing.assert_allclose(m, deg.m0)
    np.testing.assert_allclose(S, deg.S0, rtol=1e-9)


# ------------------------------------------------------------- propriétés des prédictions
def test_quantiles_ordonnes_rul_positif(deg, sprint2):
    for u, g in list(sprint2["test"].groupby("unit"))[::10]:
        p = deg.predict(g.cycle.values, g.HI_raw.values, np.random.default_rng(1))
        assert 0 <= p["p10"] <= p["rul"] <= p["p90"] <= HORIZON, f"moteur {u}"


def test_meme_graine_memes_resultats(deg, sprint2):
    g = sprint2["test"][sprint2["test"].unit == 7]
    a = deg.predict(g.cycle.values, g.HI_raw.values, np.random.default_rng(5))
    b = deg.predict(g.cycle.values, g.HI_raw.values, np.random.default_rng(5))
    assert {k: a[k] for k in ("rul", "p10", "p90")} == {k: b[k] for k in ("rul", "p10", "p90")}


def test_courbe_moyenne(deg):
    g, v = deg.mean_curve(deg.m0, 1, 201)
    assert g[0] == 1 and g[-1] == 201 and len(g) == len(v) == 101
    np.testing.assert_allclose(v, _phi(g) @ deg.m0)


# ------------------------------------------------------------- apprentissage et référence
def test_apprentissage_flotte_identique_au_modele_sauvegarde(deg, sprint2, results):
    fit = DegradationRUL().fit([(g.cycle.values, g.HI_raw.values) for _, g in sprint2["train"].groupby("unit")])
    np.testing.assert_allclose(fit.m0, deg.m0)
    np.testing.assert_allclose(fit.S0, deg.S0)
    assert (fit.threshold, fit.threshold_std, fit.sigma2) == pytest.approx(
        (deg.threshold, deg.threshold_std, deg.sigma2))
    info = results["rul"]["deg_info"]
    assert round(fit.threshold, 4) == info["threshold"]
    assert round(fit.threshold_std, 4) == info["threshold_std"]
    assert round(fit.sigma2 ** .5, 4) == info["sigma"]
    assert [round(x, 4) for x in fit.m0] == info["prior_mean"]
    assert fit.W_train.shape == (100, DEG + 1)
    assert np.all(np.linalg.eigvalsh(fit.S0) > 0)


def test_predictions_reproduites_exactement(deg, sprint2, results):
    """Rejoue la boucle de run_all.py (même générateur partagé, mêmes appels) : colonnes deg de rul.json."""
    rng = np.random.default_rng(0)
    ref = {r["unit"]: r for r in results["rul"]["table"]}
    for u, g in sprint2["test"].groupby("unit"):
        t, h = g.cycle.values, g.HI_raw.values
        d = deg.predict(t, h, rng)
        r = ref[int(u)]
        assert (round(d["rul"], 1), round(d["p10"], 1), round(d["p90"], 1)) == (r["deg"], r["deg_p10"], r["deg_p90"])
        for k in range(max(10, len(t) % 5), len(t) + 1, 5):          # trajectoire (consomme le générateur)
            deg.predict(t[:k], h[:k], rng)


# ------------------------------------------------------------- métriques et limites connues
def test_couverture_et_biais_recalcules(results):
    t = results["rul"]["table"]
    true = np.array([r["true"] for r in t])
    lo, hi, pred = (np.array([r[k] for r in t]) for k in ("deg_p10", "deg_p90", "deg"))
    cover = 100 * np.mean((true >= lo) & (true <= hi))
    assert round(cover, 1) == results["rul"]["deg_info"]["coverage_10_90"] == 54.0
    assert round(np.mean(pred - true), 2) == results["rul"]["metrics"]["deg"]["bias"]
    assert results["rul"]["metrics"]["deg"]["bias"] == pytest.approx(13.5, abs=0.05)


def test_constantes():
    assert (HORIZON, N_SAMPLES, DEG) == (400, 1000, 2)
