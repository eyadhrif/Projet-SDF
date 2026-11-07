"""FMDS-01 (Eya) et FMDS-02 (Salma) — Tests de backend/pipeline/fmds.py.

1. Validation sur des cas connus (données simulées dont on connaît la vraie loi, exemple à la main)
2. Propriétés mathématiques des fonctions de fiabilité, de disponibilité et de coût
3. Non-régression : chiffres de la section 1 du prompt maître, avec tolérances explicites
"""
import numpy as np
import pandas as pd
import pytest
from scipy import integrate, stats
from scipy.special import gamma as G

from pipeline import fmds
from pipeline.data import lifetime_table
from pipeline.fmds import (Weibull3, kaplan_meier, nelson_aalen, weibull_mco, weibull_mv,
                           model_comparison, maintenabilite, disponibilite, remplacement_preventif,
                           compute_fmds)


def life_df(times, status=None):
    times = np.asarray(times, float)
    status = np.ones(len(times), int) if status is None else np.asarray(status, int)
    return pd.DataFrame({"time": times, "status": status})


@pytest.fixture(scope="module")
def life(fd001):
    return lifetime_table(fd001[0], fd001[1])


@pytest.fixture(scope="module")
def out(life):
    """Sortie complète de compute_fmds sur FD001 (calculée une fois)."""
    return compute_fmds(life)


@pytest.fixture(scope="module")
def W(out):
    w3 = out["fiabilite"]["w3"]
    return Weibull3(w3["beta"], w3["gamma"], w3["eta"])


@pytest.fixture(scope="module")
def weib_sim():
    return stats.weibull_min.rvs(2.0, scale=100, size=5000, random_state=np.random.default_rng(1))


# =============================================================== 1. cas connus
def test_mco_retrouve_weibull_simulee(weib_sim):
    p, plot = weibull_mco(weib_sim)
    assert p["beta"] == pytest.approx(2.0, rel=0.05)
    assert p["eta"] == pytest.approx(100, rel=0.05)
    assert p["r2"] > 0.99
    assert len(plot) == 5000


def test_mv_retrouve_weibull_simulee(weib_sim):
    _, p = weibull_mv(life_df(weib_sim))
    assert p["beta"] == pytest.approx(2.0, rel=0.05)
    assert p["eta"] == pytest.approx(100, rel=0.05)
    assert p["beta_ci"][0] < p["beta"] < p["beta_ci"][1]


def test_mv_avec_censure_retrouve_weibull_simulee():
    """Censure à droite aléatoire : la MV censurée reste sans biais notable."""
    rng = np.random.default_rng(2)
    t = stats.weibull_min.rvs(2.0, scale=100, size=5000, random_state=rng)
    c = rng.uniform(0, 250, 5000)
    _, p = weibull_mv(life_df(np.minimum(t, c), (t <= c).astype(int)))
    assert p["beta"] == pytest.approx(2.0, rel=0.05)
    assert p["eta"] == pytest.approx(100, rel=0.05)


def test_weibull_3p_retrouve_gamma():
    x = stats.weibull_min.rvs(1.8, loc=125, scale=90, size=5000, random_state=np.random.default_rng(3))
    comp, params = model_comparison(x)
    b, g, e = params["Weibull 3P"]
    assert g == pytest.approx(125, abs=3)
    assert b == pytest.approx(1.8, rel=0.08)
    assert e == pytest.approx(90, rel=0.05)
    w3 = next(c for c in comp if c["model"] == "Weibull 3P")
    assert w3["accept"]


def test_km_sans_censure_egal_fonction_de_repartition_empirique(weib_sim):
    x = np.round(weib_sim[:300], 1)
    _, pts, cens = kaplan_meier(life_df(x))
    assert cens == []
    for p in pts:
        assert p["R"] == pytest.approx(np.mean(x > p["t"]), abs=1e-4)


def test_km_exemple_calcule_a_la_main():
    """Durées 3, 5, 5+, 8, 10+, 12 (+ = censure). Calcul à la main :
    R(3) = 5/6 ; R(5) = 5/6·4/5 = 2/3 ; R(8) = 2/3·2/3 = 4/9 ; R(10) = 4/9 ; R(12) = 0.
    Remarque : l'exemple chiffré du cours (PDF hors dépôt) reste à ajouter.
    """
    _, pts, cens = kaplan_meier(life_df([3, 5, 5, 8, 10, 12], [1, 1, 0, 1, 0, 1]))
    R = {p["t"]: p["R"] for p in pts}
    assert R[0] == 1
    assert R[3] == pytest.approx(5 / 6, abs=1e-4)
    assert R[5] == pytest.approx(2 / 3, abs=1e-4)
    assert R[8] == pytest.approx(4 / 9, abs=1e-4)
    assert R[10] == pytest.approx(4 / 9, abs=1e-4)
    assert R[12] == pytest.approx(0, abs=1e-4)
    assert [c["t"] for c in cens] == [5.0, 10.0]


def test_km_intervalle_de_confiance_encadre(life):
    _, pts, _ = kaplan_meier(life)
    for p in pts[1:]:
        if p["R"] > 0:
            assert p["lo"] <= p["R"] <= p["hi"]


def test_nelson_aalen_proche_de_km(life):
    _, km, _ = kaplan_meier(life)
    na, hz = nelson_aalen(life)
    Rkm = {p["t"]: p["R"] for p in km}
    for p in na:
        if Rkm[p["t"]] > 0.1:
            assert p["Rfh"] == pytest.approx(Rkm[p["t"]], abs=0.03)
        assert p["Rfh"] == pytest.approx(np.exp(-p["H"]), abs=1e-4)
    assert all(h["h"] >= 0 for h in hz)


def test_lognormale_simulee_retrouvee(monkeypatch):
    """Grand échantillon : μ = ln(16), σ = 0,6 retrouvés ; MTTR = exp(μ + σ²/2)."""
    m, mttr_c = maintenabilite(20000)
    assert m["mu"] == pytest.approx(np.log(fmds.TTR_MEDIAN_H), abs=0.02)
    assert m["sigma"] == pytest.approx(fmds.TTR_SIGMA, abs=0.02)
    assert m["mttr_h"] == pytest.approx(np.exp(m["mu"] + m["sigma"] ** 2 / 2), abs=0.02)
    assert mttr_c == pytest.approx(m["mttr_h"] / fmds.HOURS_PER_CYCLE, abs=0.01)
    assert m["t90_h"] == pytest.approx(np.exp(m["mu"] + 1.2816 * m["sigma"]), rel=1e-3)
    assert m["ks"]["accept"]


def test_maintenabilite_fonction_de_repartition(out):
    m = out["maintenabilite"]
    M = [p["M"] for p in m["M"]]
    assert all(0 <= v <= 1 for v in M) and np.all(np.diff(M) >= 0)
    assert sum(h["n"] for h in m["hist"]) == len(m["samples"]) == 100


# =============================================================== 2. propriétés
T = np.linspace(0, 600, 3001)


def test_R_decroissante_entre_0_et_1(W):
    R = W.R(T)
    assert R[0] == 1
    assert ((R >= 0) & (R <= 1)).all()
    assert (np.diff(R) <= 0).all()


def test_R_vaut_1_et_lambda_nul_avant_gamma(W):
    t = np.linspace(0, W.g, 50)
    np.testing.assert_array_equal(W.R(t), 1.0)
    np.testing.assert_array_equal(W.lam(t), 0.0)
    assert (W.lam(np.linspace(W.g + 1, 400, 50)) > 0).all()


def test_lambda_croissant_car_beta_superieur_a_1(W):
    assert W.b > 1
    assert (np.diff(W.lam(np.linspace(W.g + 1, 400, 100))) > 0).all()


def test_F_plus_R_egal_1(out):
    for c in out["fiabilite"]["curves"]:
        assert c["F"] + c["R_w3"] == pytest.approx(1, abs=2e-4)


def test_integrale_de_f_vaut_1(W):
    val, _ = integrate.quad(lambda t: W.lam(t) * W.R(t), W.g, np.inf)
    assert val == pytest.approx(1, abs=1e-3)


def test_quantiles_ordonnes_et_coherents(W):
    b1, b10, b50 = W.quantile(0.01), W.quantile(0.10), W.quantile(0.50)
    assert W.g < b1 < b10 < b50
    for p, q in ((0.01, b1), (0.10, b10), (0.50, b50)):
        assert 1 - W.R(q) == pytest.approx(p, abs=1e-9)


def test_mttf_analytique_egal_integrale_de_R(W):
    assert W.mttf() == pytest.approx(W.g + W.e * G(1 + 1 / W.b))
    num, _ = integrate.quad(W.R, 0, np.inf, limit=200)
    assert W.mttf() == pytest.approx(num, rel=1e-6)


def test_fiabilite_conditionnelle(out, W):
    for c in out["fiabilite"]["conditional"]:
        assert 0 <= c["Rc"] <= 1
        if c["t"] + 25 <= W.g:
            assert c["Rc"] == 1


def test_disponibilite_markovienne():
    d = disponibilite(200.0, 10.0)
    assert d["A_t"][0]["A"] == 1
    assert d["A"] == pytest.approx(200 / 210, abs=1e-5)
    assert d["A_t"][-1]["A"] == pytest.approx(d["A"], abs=1e-3)
    A = [p["A"] for p in d["A_t"]]
    assert (np.diff(A) <= 0).all()
    assert d["mtbf"] == 210 and d["unavail_h_per_1000h"] == pytest.approx((1 - 200 / 210) * 1000, abs=0.01)


def test_disponibilite_fd001_converge(out):
    d = out["disponibilite"]
    assert d["A_t"][0]["A"] == 1
    # mut et mdt sont arrondis à 0,01 dans le JSON (A est calculé avec les valeurs exactes) :
    # l'erreur d'arrondi sur A vaut au plus 0,005 / (mut + mdt) ≈ 2,3e-5, d'où la tolérance 5e-5
    assert d["A"] == pytest.approx(d["mut"] / (d["mut"] + d["mdt"]), abs=5e-5)
    assert d["A_t"][-1]["A"] == pytest.approx(d["A"], abs=1e-4)


def _cout(W, T):
    up = integrate.quad(lambda t: float(W.R(t)), 0, T)[0]
    return (fmds.COST_PREVENTIVE * float(W.R(T)) + fmds.COST_CORRECTIVE * (1 - float(W.R(T)))) / up


def test_T_optimal_est_un_minimum(out, W):
    pr = out["preventif"]
    T = pr["T_opt"]
    c = _cout(W, T)
    assert c == pytest.approx(pr["cost_opt"], abs=1e-5)
    assert _cout(W, T - 5) > c and _cout(W, T + 5) > c
    assert c < pr["cost_rtf"]
    assert pr["cost_rtf"] == pytest.approx(fmds.COST_CORRECTIVE / W.mttf(), rel=1e-4)
    assert pr["R_at_T"] == pytest.approx(float(W.R(T)), abs=1e-3)


def test_preventif_courbe(out):
    pr = out["preventif"]
    assert all(0 < p["A"] <= 1 and 0 <= p["R"] <= 1 for p in pr["curve"])
    assert min(p["cost"] for p in pr["curve"]) >= pr["cost_opt"] - 1e-6


def test_remplacement_preventif_cas_simple():
    """Loi exponentielle (taux constant) : le préventif ne sert à rien, T* part vers la borne haute."""
    W = Weibull3(1.0, 0.0, 100.0)
    pr = remplacement_preventif(W, 5.0)
    assert pr["T_opt"] > 350
    assert pr["saving_pct"] == pytest.approx(0, abs=1.5)


# =============================================================== 3. non-régression
TOL = {"beta": 0.01, "eta": 0.1, "p": 0.001}


def test_non_regression_effectifs(out):
    fi = out["fiabilite"]
    assert (fi["n_units"], fi["n_failures"], fi["n_censored"]) == (200, 100, 100)
    assert fi["t_min_obs"] == 128


def test_non_regression_weibull(out):
    fi = out["fiabilite"]
    assert fi["mco"]["beta"] == pytest.approx(5.52, abs=TOL["beta"])
    assert fi["mco"]["eta"] == pytest.approx(223.4, abs=TOL["eta"])
    assert fi["mco"]["r2"] == pytest.approx(0.894, abs=0.001)
    assert fi["mv"]["beta"] == pytest.approx(4.41, abs=TOL["beta"])
    assert fi["mv"]["eta"] == pytest.approx(225.0, abs=TOL["eta"])
    assert fi["mv"]["ks_p"] == pytest.approx(0.013, abs=TOL["p"])
    assert fi["mv_cens"]["beta"] == pytest.approx(4.82, abs=TOL["beta"])
    assert fi["mv_cens"]["beta_ci"] == pytest.approx([4.22, 5.42], abs=TOL["beta"])
    assert fi["mv_cens"]["eta"] == pytest.approx(236.6, abs=TOL["eta"])
    assert fi["w3"]["beta"] == pytest.approx(1.83, abs=TOL["beta"])
    assert fi["w3"]["eta"] == pytest.approx(91.3, abs=TOL["eta"])
    assert fi["w3"]["gamma"] == pytest.approx(125.2, abs=TOL["eta"])
    assert fi["w3"]["ks_p"] == pytest.approx(0.32, abs=0.005)
    assert fi["retained"] == "Weibull 3P"


def test_non_regression_adequation(out):
    comp = {c["model"]: c for c in out["fiabilite"]["comparison"]}
    assert set(comp) == {"Exponentielle", "Weibull 2P", "Log-normale", "Weibull 3P"}
    assert not comp["Weibull 2P"]["accept"] and comp["Weibull 3P"]["accept"]
    assert abs(comp["Weibull 3P"]["aic"] - comp["Log-normale"]["aic"]) < 1
    assert comp["Weibull 3P"]["aic"] < comp["Weibull 2P"]["aic"]


def test_non_regression_indicateurs(out):
    fi = out["fiabilite"]
    assert fi["mttf"] == pytest.approx(206.3, abs=0.05)
    assert fi["b1"] == pytest.approx(132.6, abs=0.05)
    assert fi["b10"] == pytest.approx(151.9, abs=0.05)
    assert fi["median_km"] == 202
    assert fi["mttf_km"] == pytest.approx(214.28, abs=0.01)


@pytest.mark.xfail(strict=True, reason="B50 pas encore exporté par fmds.py (ticket A1 de la phase A)")
def test_b50_exporte(out):
    assert out["fiabilite"]["b50"] == pytest.approx(199.9, abs=0.05)


def test_b50_calcule_depuis_le_modele(W):
    assert W.quantile(0.5) == pytest.approx(199.9, abs=0.05)


def test_non_regression_maintenabilite_disponibilite_preventif(out):
    m, d, p = out["maintenabilite"], out["disponibilite"], out["preventif"]
    assert m["mttr_h"] == pytest.approx(17.3, abs=0.05)
    assert (m["mu"], m["sigma"]) == pytest.approx((2.742, 0.464), abs=0.001)
    assert 100 * d["A"] == pytest.approx(95.98, abs=0.005)
    assert p["T_opt"] == pytest.approx(131, abs=0.5)
    assert p["saving_pct"] == pytest.approx(68, abs=0.5)
    assert (p["Cp"], p["Cc"]) == (1.0, 5.0)


def test_hypotheses_exportees(out):
    a = out["assumptions"]
    assert (a["hours_per_cycle"], a["ttr_median_h"], a["ttr_sigma"]) == (2.0, 16.0, 0.6)
    assert "censur" in a["censoring"]


def test_sortie_identique_au_json(out, results):
    """compute_fmds est déterministe : sa sortie = fmds.json commité (hors bloc dataset, ajouté par run_all)."""
    ref = {k: v for k, v in results["fmds"].items() if k != "dataset"}
    assert out == ref
