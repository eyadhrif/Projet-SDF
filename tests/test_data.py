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
