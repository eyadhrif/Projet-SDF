"""Tests des résultats exportés (backend/results/*.json) et de la reproductibilité de run_all.py (§0.7, §0.10)."""
import copy
import json
import math
import os
import shutil
import subprocess
import sys

import pytest

from conftest import ROOT, BACKEND, RESULTS, MODELS

NAMES = ("fmds", "health", "rul", "engines")
# dataset.json (A2) est déterministe ; run_info.json change à chaque exécution (date, durée)


def _strict_load(path):
    """json.loads qui refuse NaN, Infinity et -Infinity (non conformes au standard JSON)."""
    def refuse(c):
        raise ValueError(f"constante non standard {c} dans {path.name}")
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=refuse)


def _nombres(o):
    if isinstance(o, dict):
        for v in o.values():
            yield from _nombres(v)
    elif isinstance(o, list):
        for v in o:
            yield from _nombres(v)
    elif isinstance(o, float):
        yield o


# ------------------------------------------------------------- validité
@pytest.mark.parametrize("name", NAMES + ("dataset", "run_info"))
def test_json_valide_sans_nan_ni_infini(name):
    d = _strict_load(RESULTS / f"{name}.json")
    assert d
    assert all(math.isfinite(x) for x in _nombres(d))


@pytest.mark.parametrize("name", ["health_clf.joblib", "health_indicator.joblib",
                                  "degradation_model.joblib", "lstm_rul.pt"])
def test_modeles_presents(name):
    assert (MODELS / name).stat().st_size > 0


# ------------------------------------------------------------- cohérence croisée
def test_moteurs_engines_egaux_table_rul(results):
    eng, table = results["engines"], results["rul"]["table"]
    assert sorted(map(int, eng)) == sorted(r["unit"] for r in table) == list(range(1, 101))
    for r in table:
        e = eng[str(r["unit"])]
        assert e["unit"] == r["unit"]
        assert e["last_cycle"] == r["cycles"]
        assert e["true_end"] == r["true"]
        assert e["series"][-1]["c"] == r["cycles"] and e["series"][-1]["true"] == r["true"]
        assert e["series"][-1]["lstm"] == r["lstm"]
        assert e["series"][-1]["deg"] == r["deg"]
        assert e["deg_ci"] == [r["deg_p10"], r["deg_p90"]]


def test_series_completes(results):
    for e in results["engines"].values():
        c = [s["c"] for s in e["series"]]
        assert c == list(range(1, e["last_cycle"] + 1))
        t = [s["true"] for s in e["series"]]
        assert all(a - b == 1 for a, b in zip(t, t[1:]))


def test_dataset_fmds_coherent_avec_les_donnees(results, fd001):
    ds = results["fmds"]["dataset"]
    assert (ds["train_rows"], ds["test_rows"], ds["train_units"], ds["test_units"]) == (20631, 13096, 100, 100)
    assert (ds["life_min"], ds["life_max"]) == (128, 362)
    assert len(ds["lifetimes"]) == 200


def test_etats_de_la_flotte_coherents(results):
    from collections import Counter
    assert Counter(r["state"] for r in results["rul"]["table"]) == results["health"]["fleet_states"]


# ------------------------------------------------------------- phase A (figures et tableaux)
def test_figures_et_tableaux_du_rapport():
    figs, tabs = ROOT / "report" / "figures", ROOT / "report" / "tables"
    if not figs.exists() and not tabs.exists():
        pytest.skip("report/figures et report/tables seront générés en phase A (tickets A3, A4)")
    fichiers = [p for d in (figs, tabs) if d.exists() for p in d.iterdir() if p.is_file()]
    assert fichiers
    assert all(p.stat().st_size > 0 for p in fichiers)


# ------------------------------------------------------------- reproductibilité complète
def _sans_lstm(name, d):
    """Retire tout ce qui dépend de l'entraînement du LSTM (non reproductible d'une machine à l'autre)."""
    d = copy.deepcopy(d)
    if name == "rul":
        for k in ("lstm", "ensemble"):
            d["metrics"].pop(k)
        d.pop("lstm_info")
        for r in d["table"]:
            r.pop("lstm")
        for b in d["error_hist"]:
            b.pop("lstm")
    if name == "engines":
        for e in d.values():
            for s in e["series"]:
                s.pop("lstm")
    return d


def _copie_et_lance(tmp_path, *args, garder_lstm):
    """Copie backend/ et data/ dans tmp_path (fichiers commités intacts) et lance run_all.py."""
    shutil.copytree(BACKEND, tmp_path / "backend",
                    ignore=shutil.ignore_patterns("results", "models", "__pycache__"))
    shutil.copytree(ROOT / "data", tmp_path / "data")
    if garder_lstm:
        (tmp_path / "backend" / "models").mkdir()
        shutil.copy(MODELS / "lstm_rul.pt", tmp_path / "backend" / "models" / "lstm_rul.pt")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    p = subprocess.run([sys.executable, "run_all.py", *args], cwd=tmp_path / "backend", env=env,
                       capture_output=True, text=True, encoding="utf-8", timeout=1200)
    assert p.returncode == 0, p.stderr[-2000:]
    res = tmp_path / "backend" / "results"
    return {n: _strict_load(res / f"{n}.json") for n in NAMES + ("run_info", "dataset")}


@pytest.mark.slow
def test_run_all_reproduit_exactement_les_resultats(tmp_path, results):
    """Mode par défaut (LSTM de référence rechargé) : les 4 JSON sont identiques aux fichiers commités."""
    new = _copie_et_lance(tmp_path, garder_lstm=True)
    for n in NAMES:
        assert new[n] == results[n], f"{n}.json diffère"
    assert new["dataset"] == _strict_load(RESULTS / "dataset.json")
    assert new["run_info"]["lstm"].startswith("rechargé")


@pytest.mark.slow
def test_run_all_avec_reentrainement_du_lstm(tmp_path, results):
    """--reentrainer-lstm : identique hors LSTM ; le LSTM reste dans la tolérance (§0.3)."""
    new = _copie_et_lance(tmp_path, "--reentrainer-lstm", garder_lstm=False)
    for n in NAMES:
        assert _sans_lstm(n, new[n]) == _sans_lstm(n, results[n]), f"{n}.json diffère hors LSTM"
    m, ref = new["rul"]["metrics"]["lstm"], results["rul"]["metrics"]["lstm"]
    assert m["rmse"] == pytest.approx(ref["rmse"], abs=0.5)
    assert 13 <= m["rmse"] <= 18
    assert new["run_info"]["lstm"].startswith("réentraîné")


# ------------------------------------------------------------- traçabilité (A5)
def test_run_info():
    info = _strict_load(RESULTS / "run_info.json")
    assert set(info) >= {"date", "duree_s", "python", "systeme", "bibliotheques", "graines", "lstm"}
    assert info["duree_s"] > 0
    assert all(info["bibliotheques"][p] for p in ("numpy", "pandas", "scikit-learn", "lifelines", "torch"))
    assert len(info["graines"]) == 4 and 42 in info["graines"].values()
    assert info["lstm"].startswith("rechargé")         # résultats publiés = modèle de référence


def test_graines_documentees_coherentes_avec_le_code():
    from pipeline import fmds
    import run_all
    assert fmds.SEED in run_all.GRAINES.values()
    src = (BACKEND / "pipeline" / "rul_lstm.py").read_text(encoding="utf-8")
    assert "torch.manual_seed(0)" in src and "np.random.seed(0)" in src and "default_rng(0)" in src
