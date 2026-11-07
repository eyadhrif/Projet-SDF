"""Cohérence de la documentation : chaque chiffre de résultat du README est confronté au JSON.

Les chaînes attendues sont construites à partir de backend/results/*.json, avec l'arrondi
« demi vers le haut » et la virgule décimale, comme sur le dashboard (fmt de ui.jsx).
"""
from decimal import Decimal, ROUND_HALF_UP

import pytest

from conftest import ROOT, load_json

README = (ROOT / "README.md").read_text(encoding="utf-8")


def fr(x, d=2, signe=False):
    """Nombre au format français, arrondi demi vers le haut (0,6205 -> 0,621)."""
    q = Decimal(str(x)).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    s = f"{q:f}".replace(".", ",")
    return ("+" + s) if signe and q > 0 else s


def _attendus():
    f, h, r = load_json("fmds"), load_json("health"), load_json("rul")
    fi, ma, di, pr = f["fiabilite"], f["maintenabilite"], f["disponibilite"], f["preventif"]
    gb, sv = h["classifiers"]["Gradient Boosting"], h["classifiers"]["SVM (RBF)"]
    m = r["metrics"]

    def ligne_rul(nom, k, gras=False):
        b = "**" if gras else ""
        return (f"| {b}{nom}{b} | {b}{fr(m[k]['rmse'])}{b} | {b}{fr(m[k]['mae'])}{b} | "
                f"{fr(m[k]['bias'], 1, True)} | {b}{fr(m[k]['score'], 0)}{b} |")

    return {
        "unités de fiabilité": f"**Données de durée de vie :** {fi['n_units']} moteurs",
        "KM médiane et MTTF": f"Médiane = {fr(fi['median_km'], 0)} cycles, MTTF (aire sous KM) = {fr(fi['mttf_km'], 0)} cycles",
        "W2P MCO": f"β = {fr(fi['mco']['beta'])}, η = {fr(fi['mco']['eta'], 1)}, R² = {fr(fi['mco']['r2'], 3)}",
        "W2P MV": f"β = {fr(fi['mv']['beta'])}, η = {fr(fi['mv']['eta'], 1)}, **test KS p = {fr(fi['mv']['ks_p'], 3)}, rejeté**",
        "W2P MV censuré": (f"β = {fr(fi['mv_cens']['beta'])} [{fr(fi['mv_cens']['beta_ci'][0])} ; "
                           f"{fr(fi['mv_cens']['beta_ci'][1])}], η = {fr(fi['mv_cens']['eta'], 1)}"),
        "W3P": (f"β = {fr(fi['w3']['beta'])}, η = {fr(fi['w3']['eta'], 1)}, γ = {fr(fi['w3']['gamma'], 1)} cycles**, "
                f"KS p = {fr(fi['w3']['ks_p'])}, accepté"),
        "R² arrondi": f"(R² = {fr(fi['mco']['r2'])})",
        "première défaillance": f"aucune défaillance ne survient avant {fr(fi['t_min_obs'], 0)} cycles",
        "MTTF": f"= **{fr(fi['mttf'], 1)} cycles**",
        "B10": f"B10 = {fr(fi['b10'], 0)} cycles",
        "B1": f"B1 = {fr(fi['b1'], 0)} cycles",
        "B50": f"B50 = {fr(fi['b50'], 1)} cycles",
        "loi de maintenabilité": f"μ = {fr(ma['mu'], 3)}, σ = {fr(ma['sigma'], 3)}, KS p = {fr(ma['ks']['p'])}",
        "MTTR": f"**MTTR = {fr(ma['mttr_h'], 1)} h** ({fr(ma['mttr_cycles'], 1)} cycles)",
        "t90": f"t90 = {fr(ma['t90_h'], 1)} h",
        "disponibilité": f"= **{fr(100 * di['A'], 2)} %**",
        "T*": f"**T\\* ≈ {fr(pr['T_opt'], 0)} cycles**, avec R(T\\*) = {fr(pr['R_at_T'], 3)}",
        "gain préventif": f"réduit de **{fr(pr['saving_pct'], 0)} %**",
        "capteurs écartés": f"{len(h['dropped'])} capteurs constants sont écartés : {', '.join(h['dropped'])}",
        "capteurs retenus": (f"**{len(h['selected'])} capteurs pronostiques**"),
        "classif. GB": (f"| **Gradient Boosting** | {fr(gb['cv']['auc'], 3)} | **{fr(gb['test']['auc'], 3)}** | "
                        f"{fr(gb['test']['recall'], 3)} |"),
        "classif. SVM": (f"| SVM (RBF) | {fr(sv['cv']['auc'], 3)} | {fr(sv['test']['auc'], 3)} | "
                         f"{fr(sv['test']['recall'], 3)} |"),
        "RUL dégradation": ligne_rul("Dégradation bayésienne", "deg"),
        "RUL LSTM": ligne_rul("LSTM", "lstm", gras=True),
        "RUL moyenne": ligne_rul("Moyenne des deux", "ensemble"),
        "biais dégradation": f"prédictions tardives ({fr(m['deg']['bias'], 1, True)} cycles)",
        "couverture": f"dans {fr(r['deg_info']['coverage_10_90'], 0)} % des cas",
    }


@pytest.mark.parametrize("nom, attendu", list(_attendus().items()))
def test_chiffre_readme_conforme_au_json(nom, attendu):
    assert attendu in README, f"README : « {attendu} » introuvable ({nom})"


def test_capteurs_retenus_listes_dans_le_readme():
    h = load_json("health")
    assert ", ".join(sorted(h["selected"], key=lambda s: int(s[1:]))) in README


def test_format_fr():
    assert fr(0.6205, 3) == "0,621"
    assert fr(13.52, 1, True) == "+13,5"
    assert fr(3742.7, 0) == "3743"
    assert fr(-2.25, 1, True) == "-2,3"
