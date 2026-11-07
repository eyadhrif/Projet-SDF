"""SET-02 — Tests du chargement C-MAPSS FD001 (backend/pipeline/data.py)."""
import numpy as np
import pandas as pd
import pytest

from pipeline.data import DATA_DIR, COLS, SENSORS, SENSOR_INFO, load_fd001, lifetime_table


# ------------------------------------------------------------- fichiers bruts
@pytest.mark.parametrize("name, rows, cols", [
    ("train_FD001.txt", 20631, 26), ("test_FD001.txt", 13096, 26), ("RUL_FD001.txt", 100, 1),
])
def test_fichier_brut_dimensions(name, rows, cols):
    path = DATA_DIR / name
    assert path.exists()
    df = pd.read_csv(path, sep=r"\s+", header=None)
    assert df.shape == (rows, cols)


def test_colonnes():
    assert len(COLS) == 26 and COLS[:5] == ["unit", "cycle", "set1", "set2", "set3"]
    assert SENSORS == [f"s{i}" for i in range(1, 22)]
    assert set(SENSOR_INFO) == set(SENSORS)


# ------------------------------------------------------------- jeux chargés
def test_tailles(fd001):
    train, test, rul = fd001
    assert len(train) == 20631 and len(test) == 13096 and len(rul) == 100
    assert list(train.columns) == COLS + ["RUL"]


@pytest.mark.parametrize("idx", [0, 1], ids=["train", "test"])
def test_100_moteurs_sans_trou(fd001, idx):
    df = fd001[idx]
    assert sorted(df.unit.unique()) == list(range(1, 101))


@pytest.mark.parametrize("idx", [0, 1], ids=["train", "test"])
def test_cycles_consecutifs_depuis_1(fd001, idx):
    for u, g in fd001[idx].groupby("unit"):
        c = g.cycle.values
        assert c[0] == 1, f"moteur {u}"
        assert (np.diff(c) == 1).all(), f"moteur {u} : trou ou doublon"


@pytest.mark.parametrize("idx", [0, 1], ids=["train", "test"])
def test_aucune_valeur_manquante_ou_infinie(fd001, idx):
    num = fd001[idx].select_dtypes("number")
    assert not num.isna().any().any()
    assert np.isfinite(num.values).all()


def test_rul_train_nul_au_dernier_cycle_et_decroissant(fd001):
    train = fd001[0]
    for u, g in train.groupby("unit"):
        assert g.RUL.values[-1] == 0, f"moteur {u}"
        assert (np.diff(g.RUL.values) == -1).all(), f"moteur {u}"
        assert g.RUL.values[0] == len(g) - 1


def test_rul_test_au_dernier_cycle_egal_au_fichier(fd001):
    _, test, rul = fd001
    ref = pd.read_csv(DATA_DIR / "RUL_FD001.txt", header=None)[0].values
    last = test.groupby("unit").RUL.last().values
    np.testing.assert_array_equal(last, ref)
    np.testing.assert_array_equal(rul.RUL.values, ref)
    for u, g in test.groupby("unit"):
        assert (np.diff(g.RUL.values) == -1).all(), f"moteur {u}"


def test_statistiques_du_jeu_de_test(fd001):
    _, test, rul = fd001
    ln = test.groupby("unit").cycle.max()
    assert (ln.min(), ln.max()) == (31, 303)
    assert ln.mean() == pytest.approx(131, abs=0.05)
    assert (rul.RUL.min(), rul.RUL.max()) == (7, 145)
    assert rul.RUL.mean() == pytest.approx(75.5, abs=0.05)


# ------------------------------------------------------------- table de durées de vie
def test_table_de_durees_de_vie(fd001):
    train, test, _ = fd001
    life = lifetime_table(train, test)
    assert len(life) == 200
    assert (life.status == 1).sum() == 100 and (life.status == 0).sum() == 100
    assert set(life[life.status == 1].source) == {"train"}
    assert set(life[life.status == 0].source) == {"test"}
    assert life[life.status == 1].time.min() == 128
    # durée = dernier cycle observé
    np.testing.assert_array_equal(life[life.source == "test"].time.values,
                                  test.groupby("unit").cycle.max().values)


# ------------------------------------------------------------- description du jeu de données (A2)
from pipeline.data import describe_dataset  # noqa: E402
from conftest import RESULTS  # noqa: E402

SELECTED = ["s2", "s3", "s4", "s7", "s8", "s11", "s12", "s13", "s15", "s17", "s20", "s21"]


@pytest.fixture(scope="module")
def description(fd001):
    train, test, rul = fd001
    return describe_dataset(train, test, rul, SELECTED)


def test_description_tailles_et_series(description):
    d, _ = description
    assert d["tailles"] == {"lignes_entrainement": 20631, "lignes_test": 13096, "moteurs_entrainement": 100,
                            "moteurs_test": 100, "colonnes_fichier": 26, "capteurs": 21, "reglages": 3}
    assert (d["duree_de_vie_entrainement"]["min"], d["duree_de_vie_entrainement"]["max"]) == (128, 362)
    assert d["longueur_series_test"]["min"] == 31 and d["longueur_series_test"]["max"] == 303
    assert d["longueur_series_test"]["moyenne"] == pytest.approx(131, abs=0.05)
    assert (d["rul_reel_test"]["min"], d["rul_reel_test"]["max"]) == (7, 145)
    assert d["rul_reel_test"]["moyenne"] == pytest.approx(75.5, abs=0.05)
    assert d["fiabilite"] == {"unites": 200, "defaillances": 100, "censures_a_droite": 100}


def test_description_statistiques_recalculees(fd001, description):
    train = fd001[0]
    _, table = description
    for _, r in table.iterrows():
        s = train[r.variable]
        assert r["min"] == round(s.min(), 4) and r["max"] == round(s.max(), 4)
        assert r.moyenne == pytest.approx(s.mean(), abs=1e-4)
        assert r.ecart_type == pytest.approx(s.std(), abs=1e-4)
        assert r.valeurs_distinctes == s.nunique()
    num = table[["min", "max", "moyenne", "mediane", "ecart_type"]].to_numpy(float)
    assert not np.any((num == 0) & np.signbit(num)), "zéro négatif (-0.0) après arrondi"


def test_description_capteurs_constants_et_retenus(description):
    d, table = description
    assert d["capteurs_constants"] == ["s1", "s5", "s6", "s10", "s16", "s18", "s19"]
    assert d["capteurs_retenus"] == SELECTED
    assert len(table) == 24 and (table.type == "réglage").sum() == 3
    assert not table[table.type == "réglage"].constant.any()          # set3 est fixe mais n'est pas un capteur
    assert not (table.constant & table.retenu).any()
    assert table[table.retenu].variable.tolist() == SELECTED


def test_fichiers_dataset_exportes(description):
    import json
    import pandas as pd
    d, table = description
    assert json.loads((RESULTS / "dataset.json").read_text(encoding="utf-8")) == json.loads(json.dumps(d))
    csv = pd.read_csv(RESULTS / "dataset.csv")
    assert list(csv.columns) == list(table.columns) and len(csv) == 24
    pd.testing.assert_frame_equal(csv, table.reset_index(drop=True), check_dtype=False)
