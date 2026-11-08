"""A4 — Tableaux et valeurs du rapport (backend/report_tables.py) : complets, bien formés, à jour, exacts."""
import json
import re

import pytest

import report_tables as rt
from conftest import ROOT, load_json

TABLES = ROOT / "report" / "tables"
VALEURS = ROOT / "report" / "generated" / "valeurs.json"
NOMS = ["donnees_tailles", "donnees_capteurs", "fiabilite_modeles", "fiabilite_adequation", "fiabilite_indicateurs",
        "fmds_maintenabilite_disponibilite", "sante_classifieurs", "rul_metriques", "rul_calibration",
        "rul_biais_tranches", "hypotheses_parametres"]


def _cellules(ligne):
    return re.split(r"(?<!\\)\|", ligne.strip()[1:-1])      # barres échappées (\|) ignorées


@pytest.mark.parametrize("nom", NOMS)
def test_tableau_markdown_bien_forme(nom):
    lignes = (TABLES / f"{nom}.md").read_text(encoding="utf-8").strip().splitlines()
    n = len(_cellules(lignes[0]))
    assert len(lignes) >= 3
    for l in lignes:
        assert len(_cellules(l)) == n, f"{nom} : ligne mal formée « {l} »"


@pytest.mark.parametrize("nom", NOMS)
def test_tableau_latex(nom):
    tex = (TABLES / f"{nom}.tex").read_text(encoding="utf-8")
    assert tex.count(r"\begin{table}") == 1 and rf"\label{{tab:{nom}}}" in tex and r"\bottomrule" in tex
    assert "**" not in tex


def test_aucun_tableau_orphelin():
    assert {p.stem for p in TABLES.glob("*.md")} == {p.stem for p in TABLES.glob("*.tex")} == set(NOMS)


def test_tableaux_et_valeurs_a_jour(tmp_path, monkeypatch):
    monkeypatch.setattr(rt, "REPORT", tmp_path)
    rt.main()
    for nom in NOMS:
        for ext in ("md", "tex"):
            assert (tmp_path / "tables" / f"{nom}.{ext}").read_text(encoding="utf-8") == \
                   (TABLES / f"{nom}.{ext}").read_text(encoding="utf-8"), f"{nom}.{ext} pas à jour : python report_tables.py"
    assert (tmp_path / "generated" / "valeurs.json").read_text(encoding="utf-8") == VALEURS.read_text(encoding="utf-8")


def test_format_francais():
    assert rt.fr(0.6205, 3) == "0,621" and rt.fr(3742.7, 0) == "3 743"
    assert rt.fr(13.52, 1, True) == "+13,5" and rt.fr(-2.25, 1) == "−2,3" and rt.fr(None) == "—"


def test_valeurs_conformes_aux_json():
    """Échantillon de valeurs recalculées indépendamment depuis les JSON (et la section 1 du prompt maître)."""
    v = json.loads(VALEURS.read_text(encoding="utf-8"))
    f, h, r = load_json("fmds"), load_json("health"), load_json("rul")
    attendu = {
        "mttf": "206,3", "b1": "132,6", "b10": "151,9", "b50": "199,9", "mediane_km": "202",
        "w3_beta": "1,83", "w3_eta": "91,3", "w3_gamma": "125,2", "mco_beta": "5,52", "mco_r2": "0,894",
        "mv_ks_p": "0,013", "mttr_h": "17,3", "dispo": "95,98", "gain_preventif": "68",
        "gb_auc": "0,991", "gb_rappel": "0,657", "svm_auc": "0,974", "svm_rappel": "0,621",
        "deg_rmse": "24,47", "deg_mae": "18,98", "deg_biais": "+13,5", "deg_score": "3 743",
        "lstm_rmse": "15,35", "lstm_mae": "11,22", "lstm_biais": "+2,2", "lstm_score": "485",
        "couverture_80": "54", "n_lignes_train": "20 631", "n_lignes_test": "13 096",
        "test_len_moy": "131,0", "rul_test_moy": "75,5", "t_min_obs": "128",
    }
    for k, a in attendu.items():
        assert v[k] == a, k
    assert v["mttf"] == rt.fr(f["fiabilite"]["mttf"]) and v["gb_auc"] == rt.fr(h["classifiers"]["Gradient Boosting"]["test"]["auc"], 3)
    assert v["lstm_rmse"] == rt.fr(r["metrics"]["lstm"]["rmse"], 2)
    assert "duree_run_all" not in v                       # change à chaque exécution : jamais cité


def test_valeurs_non_vides():
    v = json.loads(VALEURS.read_text(encoding="utf-8"))
    assert len(v) > 100 and all(isinstance(x, str) and x and x != "—" for x in v.values())
