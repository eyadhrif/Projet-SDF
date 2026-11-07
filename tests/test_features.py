"""PDM-01 (Salma) — Tests de la sélection des capteurs, des features et du HI (backend/pipeline/features.py)."""
import joblib
import numpy as np
import pandas as pd
import pytest

from conftest import MODELS
from pipeline.features import (WINDOW, TREND_THRESHOLD, drop_constant, monotonicity, trendability,
                               window_features, HealthIndicator)

DROPPED = ["s1", "s5", "s6", "s10", "s16", "s18", "s19"]
SELECTED = ["s2", "s3", "s4", "s7", "s8", "s11", "s12", "s13", "s15", "s17", "s20", "s21"]


# ------------------------------------------------------------- sélection des capteurs
def test_capteurs_constants_ecartes(fd001):
    kept = drop_constant(fd001[0])
    assert sorted(set(f"s{i}" for i in range(1, 22)) - set(kept), key=lambda s: int(s[1:])) == DROPPED


def test_capteurs_retenus(sprint2):
    assert sprint2["dropped"] == DROPPED
    assert sorted(sprint2["selected"], key=lambda s: int(s[1:])) == SELECTED


def test_classement_coherent(sprint2, results):
    rank = sprint2["rank"]
    assert len(rank) == 14                                     # 21 - 7 constants
    assert all(abs(d["trend"]) >= TREND_THRESHOLD for d in rank if d["selected"])
    assert all(abs(d["trend"]) < TREND_THRESHOLD for d in rank if not d["selected"])
    assert [abs(d["trend"]) for d in rank] == sorted((abs(d["trend"]) for d in rank), reverse=True)
    assert all(0 <= d["mono"] <= 1 and -1 <= d["trend"] <= 1 for d in rank)
    assert rank == results["health"]["sensor_ranking"]


def test_monotonie_et_tendance_sur_un_cas_simple():
    df = pd.DataFrame({"unit": [1] * 20 + [2] * 20, "cycle": list(range(1, 21)) * 2,
                       "up": list(range(20)) * 2, "down": list(range(20, 0, -1)) * 2})
    assert monotonicity(df, ["up", "down"]) == {"up": 1.0, "down": 1.0}
    t = trendability(df, ["up", "down"])
    assert t["up"] == pytest.approx(1) and t["down"] == pytest.approx(-1)


# ------------------------------------------------------------- features fenêtrées
def test_features_nombre_et_noms(sprint2, results):
    F = sprint2["Ftr"]
    assert F.shape == (20631, 12 * 3 + 2)
    assert F.shape[1] == results["health"]["n_features"]
    assert {f"s2_{k}" for k in ("mean", "std", "slope")} <= set(F.columns)


@pytest.mark.parametrize("key", ["Ftr", "Fte"])
def test_features_sans_valeur_manquante(sprint2, key):
    F = sprint2[key]
    assert not F.isna().any().any()
    assert np.isfinite(F.values).all()


def test_features_premier_cycle_sans_fuite(sprint2):
    """Au 1er cycle de chaque moteur : moyenne = valeur brute, écart-type et pente nuls."""
    train, F = sprint2["train"], sprint2["Ftr"]
    first = train.groupby("unit").head(1).index
    for s in SELECTED:
        np.testing.assert_allclose(F.loc[first, f"{s}_mean"], train.loc[first, s])
        assert (F.loc[first, f"{s}_std"] == 0).all()
        assert (F.loc[first, f"{s}_slope"] == 0).all()


def test_features_aucune_fuite_entre_moteurs(fd001, sprint2):
    """Les features d'un moteur calculées seul sont identiques à celles du calcul sur tout le jeu."""
    train = fd001[0]
    for u in (2, 50, 100):
        g = train[train.unit == u]
        alone = window_features(g, SELECTED)
        pd.testing.assert_frame_equal(alone, sprint2["Ftr"].loc[g.index, alone.columns])


def test_pente_locale_exacte():
    df = pd.DataFrame({"unit": [1] * 15, "cycle": range(1, 16), "x": 3.0 * np.arange(15) + 7})
    F = window_features(df, ["x"])
    assert (F["x_slope"].iloc[:WINDOW - 1] == 0).all()
    np.testing.assert_allclose(F["x_slope"].iloc[WINDOW - 1:], 3.0)


# ------------------------------------------------------------- indicateur de santé
@pytest.fixture(scope="module")
def hi_train(sprint2):
    train = sprint2["train"]
    frac = train.cycle / train.groupby("unit").cycle.transform("max")
    return train, frac


def test_hi_debut_de_vie(hi_train):
    train, frac = hi_train
    assert train.HI[frac <= 0.1].mean() == pytest.approx(0.94, abs=0.03)


def test_hi_fin_de_vie(hi_train):
    train, _ = hi_train
    assert train.groupby("unit").HI.last().mean() == pytest.approx(0, abs=0.1)


def test_hi_decroit_pour_chaque_moteur(hi_train):
    train, _ = hi_train
    corr = train.groupby("unit").apply(lambda g: np.corrcoef(g.cycle, g.HI)[0, 1], include_groups=False)
    assert (corr < 0).all(), corr[corr >= 0]


def test_hi_lissage_par_moteur(sprint2):
    """Le lissage glissant ne mélange pas deux moteurs : au 1er cycle, HI lissé = HI brut."""
    train = sprint2["train"]
    first = train.groupby("unit").head(1)
    np.testing.assert_allclose(first.HI, first.HI_raw)


def test_hi_identique_au_modele_sauvegarde(sprint2, results):
    saved = joblib.load(MODELS / "health_indicator.joblib")
    test = sprint2["test"]
    np.testing.assert_allclose(saved.raw(test), test.HI_raw, atol=1e-12)
    w = sprint2["hi"].weights()
    assert len(w) == 12 and w == saved.weights() == results["health"]["hi_weights"]


def test_hi_cas_simple():
    """Un seul capteur qui décroît linéairement : le HI vaut 1 au début et 0 à la fin."""
    n = 100
    df = pd.DataFrame({"unit": [1] * n, "cycle": range(1, n + 1), "x": np.linspace(10, 0, n)})
    hi = HealthIndicator(["x"]).fit(df)
    raw = hi.raw(df)
    assert raw[0] == pytest.approx(1.05, abs=0.1) and raw[-1] == pytest.approx(-0.05, abs=0.1)
    assert (np.diff(raw) < 0).all()
