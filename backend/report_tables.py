"""A4 — Tableaux et valeurs chiffrées du rapport, générés à partir de results/*.json (Eya + Salma).

    python report_tables.py
      -> report/tables/<nom>.md et <nom>.tex   (Markdown pour le rapport, LaTeX booktabs pour Overleaf)
      -> report/generated/valeurs.json         (toutes les valeurs citées dans le texte, déjà formatées)

Le texte du rapport ne contient aucun chiffre de résultat tapé à la main : il cite {{cle}}, remplacé
par valeurs.json à la construction (report/build.mjs). tests/test_report.py le vérifie.
"""
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from pipeline import fmds as fmds_mod
from pipeline.features import WINDOW, TREND_THRESHOLD
from pipeline.health import CRITICAL_RUL, PROB_WATCH
from pipeline.rul_degradation import N_SAMPLES, HORIZON, DEG
from pipeline.rul_lstm import SEQ, RUL_CAP

ROOT = Path(__file__).resolve().parent
RES = ROOT / "results"
REPORT = ROOT.parent / "report"


def fr(x, d=1, signe=False):
    """Nombre au format français, arrondi demi vers le haut (comme le dashboard), espace fine des milliers."""
    if x is None:
        return "—"
    q = Decimal(str(x)).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    ent, _, dec = f"{abs(q):f}".partition(".")
    ent = f"{int(ent):,}".replace(",", " ")
    s = ("−" if q < 0 else ("+" if signe and q > 0 else "")) + ent + ("," + dec if dec else "")
    return s


def charger(nom):
    return json.loads((RES / f"{nom}.json").read_text(encoding="utf-8"))


# ================================================================= tableaux
class Tableau:
    def __init__(self, nom, titre, entetes, lignes, alignement=None, note=None):
        self.nom, self.titre, self.entetes, self.lignes, self.note = nom, titre, entetes, lignes, note
        self.alignement = alignement or ["l"] + ["r"] * (len(entetes) - 1)

    def markdown(self):
        sep = ["---:" if a == "r" else ":---:" if a == "c" else "---" for a in self.alignement]
        out = [f"| {' | '.join(self.entetes)} |", f"|{'|'.join(sep)}|"]
        cell = lambda c: str(c).replace("|", r"\|")            # une barre dans une cellule casserait le tableau
        out[0] = f"| {' | '.join(cell(e) for e in self.entetes)} |"
        out += [f"| {' | '.join(cell(c) for c in l)} |" for l in self.lignes]
        return "\n".join(out) + "\n"

    def latex(self):
        esc = lambda s: (str(s).replace("\\", r"\textbackslash{}").replace("%", r"\%").replace("&", r"\&")
                         .replace("_", r"\_").replace("#", r"\#").replace("**", ""))
        out = [r"\begin{table}[htbp]", r"\centering", rf"\caption{{{esc(self.titre)}}}", rf"\label{{tab:{self.nom}}}",
               rf"\begin{{tabular}}{{{''.join(self.alignement)}}}", r"\toprule",
               " & ".join(esc(e) for e in self.entetes) + r" \\", r"\midrule"]
        out += [" & ".join(esc(c) for c in l) + r" \\" for l in self.lignes]
        out += [r"\bottomrule", r"\end{tabular}"]
        if self.note:
            out.append(rf"\par\smallskip\footnotesize {esc(self.note)}")
        out.append(r"\end{table}")
        return "\n".join(out) + "\n"


def tableaux(F, H, R, D):
    fi, ma, di, pr = F["fiabilite"], F["maintenabilite"], F["disponibilite"], F["preventif"]
    comp = {c["model"]: c for c in fi["comparison"]}
    T = []

    t = D["tailles"]
    s = lambda k: D[k]
    T.append(Tableau("donnees_tailles", "Tailles exactes et statistiques du jeu C-MAPSS FD001",
        ["Élément", "Valeur"],
        [["Lignes d'entraînement / de test", f"{fr(t['lignes_entrainement'], 0)} / {fr(t['lignes_test'], 0)}"],
         ["Moteurs d'entraînement / de test", f"{t['moteurs_entrainement']} / {t['moteurs_test']}"],
         ["Variables", f"{t['capteurs']} capteurs + {t['reglages']} réglages opérationnels"],
         ["Durée de vie (entraînement) : min. – max., moyenne",
          f"{fr(s('duree_de_vie_entrainement')['min'], 0)} – {fr(s('duree_de_vie_entrainement')['max'], 0)} cycles, "
          f"{fr(s('duree_de_vie_entrainement')['moyenne'])}"],
         ["Longueur des séries de test : min. – max., moyenne",
          f"{fr(s('longueur_series_test')['min'], 0)} – {fr(s('longueur_series_test')['max'], 0)} cycles, "
          f"{fr(s('longueur_series_test')['moyenne'])}"],
         ["RUL réel de test : min. – max., moyenne",
          f"{fr(s('rul_reel_test')['min'], 0)} – {fr(s('rul_reel_test')['max'], 0)} cycles, {fr(s('rul_reel_test')['moyenne'])}"],
         ["Unités pour la fiabilité", f"{D['fiabilite']['unites']} ({D['fiabilite']['defaillances']} défaillances, "
                                      f"{D['fiabilite']['censures_a_droite']} censures à droite)"]],
        ["l", "l"]))

    T.append(Tableau("donnees_capteurs", "Variables de FD001 (statistiques sur le jeu d'entraînement)",
        ["Variable", "Description", "Moyenne", "Écart-type", "Valeurs distinctes", "Statut"],
        [[v["variable"], v["description"], fr(v["moyenne"], 3), fr(v["ecart_type"], 3), fr(v["valeurs_distinctes"], 0),
          "retenu" if v["retenu"] else ("constant, écarté" if v["constant"] else
                                        ("réglage" if v["type"] == "réglage" else "non retenu"))]
         for v in D["variables"]],
        ["l", "l", "r", "r", "r", "l"]))

    T.append(Tableau("fiabilite_modeles", "Modèles de fiabilité estimés sur les 100 durées de défaillance",
        ["Méthode", "β", "η (cycles)", "γ (cycles)", "Adéquation", "Décision"],
        [["Weibull 2P, MCO (rangs de Bernard)", fr(fi["mco"]["beta"], 2), fr(fi["mco"]["eta"]), "0",
          f"R² = {fr(fi['mco']['r2'], 3)}", "diagramme courbé"],
         ["Weibull 2P, MV", fr(fi["mv"]["beta"], 2), fr(fi["mv"]["eta"]), "0", f"KS p = {fr(fi['mv']['ks_p'], 3)}", "rejetée"],
         ["Weibull 2P, MV avec censure (200 unités)",
          f"{fr(fi['mv_cens']['beta'], 2)} [{fr(fi['mv_cens']['beta_ci'][0], 2)} ; {fr(fi['mv_cens']['beta_ci'][1], 2)}]",
          fr(fi["mv_cens"]["eta"]), "0", "—", "comparaison"],
         ["**Weibull 3P, MV**", f"**{fr(fi['w3']['beta'], 2)}**", f"**{fr(fi['w3']['eta'])}**",
          f"**{fr(fi['w3']['gamma'])}**", f"KS p = {fr(fi['w3']['ks_p'], 2)}", "**retenue**"]],
        ["l", "r", "r", "r", "l", "l"]))

    T.append(Tableau("fiabilite_adequation", "Adéquation des lois candidates (MV sur les durées complètes)",
        ["Loi", "Paramètres", "Log-vraisemblance", "AIC", "KS D", "KS p", "Décision (α = 5 %)"],
        [[c["model"], str(c["k"]), fr(c["loglik"], 2), fr(c["aic"], 2), fr(c["ks_D"], 3), fr(c["ks_p"], 3),
          "acceptée" if c["accept"] else "rejetée"] for c in fi["comparison"]],
        ["l", "r", "r", "r", "r", "r", "l"]))

    T.append(Tableau("fiabilite_indicateurs", "Indicateurs de fiabilité",
        ["Indicateur", "Valeur", "Source"],
        [["MTTF = γ + η·Γ(1 + 1/β)", f"{fr(fi['mttf'])} cycles", "Weibull 3P"],
         ["B1 (1 % de défaillances)", f"{fr(fi['b1'])} cycles", "Weibull 3P"],
         ["B10 (10 %)", f"{fr(fi['b10'])} cycles", "Weibull 3P"],
         ["B50 (médiane)", f"{fr(fi['b50'])} cycles", "Weibull 3P"],
         ["Médiane de survie", f"{fr(fi['median_km'], 0)} cycles", "Kaplan-Meier"],
         ["Aire sous la courbe de survie", f"{fr(fi['mttf_km'])} cycles", "Kaplan-Meier"],
         ["Première défaillance observée", f"{fr(fi['t_min_obs'], 0)} cycles", "données"]],
        ["l", "r", "l"]))

    T.append(Tableau("fmds_maintenabilite_disponibilite",
        "Maintenabilité, disponibilité et remplacement préventif (temps de réparation simulés)",
        ["Grandeur", "Valeur"],
        [["Loi des temps de réparation (MV)", f"log-normale, μ = {fr(ma['mu'], 3)}, σ = {fr(ma['sigma'], 3)} (KS p = {fr(ma['ks']['p'], 2)})"],
         ["MTTR", f"{fr(ma['mttr_h'])} h = {fr(ma['mttr_cycles'])} cycles"],
         ["t90 (90 % des réparations terminées)", f"{fr(ma['t90_h'])} h"],
         ["MUT / MDT / MTBF", f"{fr(di['mut'])} / {fr(di['mdt'], 2)} / {fr(di['mtbf'])} cycles"],
         ["Disponibilité intrinsèque A = MUT / (MUT + MDT)", f"{fr(100 * di['A'], 2)} %"],
         ["Âge optimal de remplacement T*", f"{fr(pr['T_opt'])} cycles, R(T*) = {fr(pr['R_at_T'], 3)}"],
         ["Coût par cycle : à T* / corrective seule", f"{fr(pr['cost_opt'], 4)} / {fr(pr['cost_rtf'], 4)} (unités de Cp)"],
         ["Gain du préventif", f"{fr(pr['saving_pct'])} %"]],
        ["l", "l"]))

    cl = H["classifiers"]
    T.append(Tableau("sante_classifieurs", "Classification normal / critique (RUL ≤ 30 cycles)",
        ["Modèle", "Évaluation", "AUC", "Exactitude", "Précision", "Rappel", "F1"],
        [[n if k == "cv" else "", "validation croisée (GroupKFold 5)" if k == "cv" else "test NASA",
          fr(m[k]["auc"], 3), fr(m[k]["accuracy"], 3), fr(m[k]["precision"], 3), fr(m[k]["recall"], 3), fr(m[k]["f1"], 3)]
         for n, m in cl.items() for k in ("cv", "test")],
        ["l", "l", "r", "r", "r", "r", "r"]))

    M = R["metrics"]
    noms = {"deg": "Dégradation bayésienne (Eya)", "lstm": "LSTM (Salma)", "ensemble": "Moyenne des deux"}
    T.append(Tableau("rul_metriques", "Performances des modèles de RUL sur les 100 moteurs de test",
        ["Modèle", "RMSE", "MAE", "Biais", "Score NASA", "|e| ≤ 15", "Tardives"],
        [[noms[k], fr(M[k]["rmse"], 2), fr(M[k]["mae"], 2), fr(M[k]["bias"], 1, True), fr(M[k]["score"], 0),
          f"{fr(M[k]['within15'], 0)} %", f"{fr(M[k]['late_pct'], 0)} %"] for k in ("deg", "lstm", "ensemble")],
        ["l", "r", "r", "r", "r", "r", "r"], "Erreur e = RUL prédit − RUL réel, en cycles ; e > 0 : prédiction tardive."))

    di_ = R["deg_info"]
    T.append(Tableau("rul_calibration", "Calibration des intervalles du modèle de dégradation",
        ["Intervalle", "Niveau nominal", "Couverture observée", "Largeur moyenne"],
        [[f"{c['bornes'][0]} – {c['bornes'][1]}", f"{c['nominal']} %", f"{fr(c['couverture'], 0)} %",
          f"{fr(c['largeur_moyenne'])} cycles"] for c in di_["calibration"]],
        ["l", "r", "r", "r"]))
    T.append(Tableau("rul_biais_tranches", "Biais du modèle de dégradation selon le RUL réel",
        ["RUL réel", "Moteurs", "Biais moyen", "MAE", "Couverture 10–90 %"],
        [[(f"{t['rul_min']} – {t['rul_max']}" if t["rul_max"] else f"> {t['rul_min']}") + " cycles", str(t["n"]),
          fr(t["biais"], 1, True), fr(t["mae"]), f"{fr(t['couverture_80'], 0)} %"] for t in di_["biais"]["par_tranche"]],
        ["l", "r", "r", "r", "r"]))

    T.append(Tableau("hypotheses_parametres", "Hypothèses et paramètres des méthodes",
        ["Paramètre", "Valeur", "Module"],
        [["Conversion temps", f"1 cycle ≈ {fr(fmds_mod.HOURS_PER_CYCLE, 0)} h (1 vol)", "fmds.py"],
         ["Temps de réparation simulés", f"log-normale, médiane {fr(fmds_mod.TTR_MEDIAN_H, 0)} h, σ = {fr(fmds_mod.TTR_SIGMA)}, graine {fmds_mod.SEED}", "fmds.py"],
         ["Coûts relatifs", f"Cp = {fr(fmds_mod.COST_PREVENTIVE, 0)}, Cc = {fr(fmds_mod.COST_CORRECTIVE, 0)}", "fmds.py"],
         ["Capteur constant", "moins de 10 valeurs distinctes", "features.py"],
         ["Sélection des capteurs", f"|tendance| ≥ {fr(TREND_THRESHOLD)}", "features.py"],
         ["Fenêtre glissante (features, lissage du HI)", f"{WINDOW} cycles", "features.py"],
         ["Cible du HI", "1 sur les 10 % premiers cycles, 0 sur les 10 % derniers", "features.py"],
         ["Classe « critique »", f"RUL ≤ {CRITICAL_RUL} cycles ; « surveillance » si P ≥ {fr(PROB_WATCH)}", "health.py"],
         ["Modèle de dégradation", f"polynôme de degré {DEG}, {N_SAMPLES} tirages, horizon {HORIZON} cycles", "rul_degradation.py"],
         ["LSTM", f"fenêtres de {SEQ} cycles, cible plafonnée à {RUL_CAP}, 2 couches de 64", "rul_lstm.py"]],
        ["l", "l", "l"]))
    return T


# ================================================================= valeurs citées dans le texte
def valeurs(F, H, R, D, I):
    fi, ma, di, pr = F["fiabilite"], F["maintenabilite"], F["disponibilite"], F["preventif"]
    comp = {c["model"]: c for c in fi["comparison"]}
    cl, best = H["classifiers"], H["classifiers"][H["best"]]
    M, DI = R["metrics"], R["deg_info"]
    t = D["tailles"]
    v = {
        # données
        "n_lignes_train": fr(t["lignes_entrainement"], 0), "n_lignes_test": fr(t["lignes_test"], 0),
        "n_moteurs_train": str(t["moteurs_entrainement"]), "n_moteurs_test": str(t["moteurs_test"]),
        "n_capteurs": str(t["capteurs"]), "n_reglages": str(t["reglages"]),
        "vie_min": fr(D["duree_de_vie_entrainement"]["min"], 0), "vie_max": fr(D["duree_de_vie_entrainement"]["max"], 0),
        "vie_moy": fr(D["duree_de_vie_entrainement"]["moyenne"]),
        "test_len_min": fr(D["longueur_series_test"]["min"], 0), "test_len_max": fr(D["longueur_series_test"]["max"], 0),
        "test_len_moy": fr(D["longueur_series_test"]["moyenne"]),
        "rul_test_min": fr(D["rul_reel_test"]["min"], 0), "rul_test_max": fr(D["rul_reel_test"]["max"], 0),
        "rul_test_moy": fr(D["rul_reel_test"]["moyenne"]),
        "n_unites": str(D["fiabilite"]["unites"]), "n_defaillances": str(D["fiabilite"]["defaillances"]),
        "n_censures": str(D["fiabilite"]["censures_a_droite"]),
        "capteurs_constants": ", ".join(D["capteurs_constants"]), "n_constants": str(len(D["capteurs_constants"])),
        "capteurs_retenus": ", ".join(D["capteurs_retenus"]), "n_retenus": str(len(D["capteurs_retenus"])),
        "n_features": str(H["n_features"]),
        # fiabilité
        "mco_beta": fr(fi["mco"]["beta"], 2), "mco_eta": fr(fi["mco"]["eta"]), "mco_r2": fr(fi["mco"]["r2"], 3),
        "mv_beta": fr(fi["mv"]["beta"], 2), "mv_eta": fr(fi["mv"]["eta"]), "mv_ks_p": fr(fi["mv"]["ks_p"], 3),
        "mvc_beta": fr(fi["mv_cens"]["beta"], 2), "mvc_beta_lo": fr(fi["mv_cens"]["beta_ci"][0], 2),
        "mvc_beta_hi": fr(fi["mv_cens"]["beta_ci"][1], 2), "mvc_eta": fr(fi["mv_cens"]["eta"]),
        "w3_beta": fr(fi["w3"]["beta"], 2), "w3_eta": fr(fi["w3"]["eta"]), "w3_gamma": fr(fi["w3"]["gamma"]),
        "w3_ks_p": fr(fi["w3"]["ks_p"], 2),
        "aic_w3": fr(comp["Weibull 3P"]["aic"], 2), "aic_ln": fr(comp["Log-normale"]["aic"], 2),
        "aic_w2": fr(comp["Weibull 2P"]["aic"], 2), "aic_exp": fr(comp["Exponentielle"]["aic"], 2),
        "delta_aic": fr(abs(comp["Weibull 3P"]["aic"] - comp["Log-normale"]["aic"]), 2),
        "ln_ks_p": fr(comp["Log-normale"]["ks_p"], 2), "exp_ks_p": fr(comp["Exponentielle"]["ks_p"], 3),
        "mttf": fr(fi["mttf"]), "b1": fr(fi["b1"]), "b10": fr(fi["b10"]), "b50": fr(fi["b50"]),
        "mediane_km": fr(fi["median_km"], 0), "mttf_km": fr(fi["mttf_km"]), "t_min_obs": fr(fi["t_min_obs"], 0),
        # FMDS-02
        "h_par_cycle": fr(fmds_mod.HOURS_PER_CYCLE, 0), "ttr_mediane": fr(fmds_mod.TTR_MEDIAN_H, 0),
        "ttr_sigma_sim": fr(fmds_mod.TTR_SIGMA), "graine_ttr": str(fmds_mod.SEED),
        "ttr_mu": fr(ma["mu"], 3), "ttr_sigma": fr(ma["sigma"], 3), "ttr_ks_p": fr(ma["ks"]["p"], 2),
        "mttr_h": fr(ma["mttr_h"]), "mttr_cycles": fr(ma["mttr_cycles"]), "t90_h": fr(ma["t90_h"]),
        "mut": fr(di["mut"]), "mdt": fr(di["mdt"], 2), "mtbf": fr(di["mtbf"]), "dispo": fr(100 * di["A"], 2),
        "indispo_h": fr(di["unavail_h_per_1000h"]),
        "cp": fr(pr["Cp"], 0), "cc": fr(pr["Cc"], 0), "t_opt": fr(pr["T_opt"]), "t_opt_arrondi": fr(pr["T_opt"], 0),
        "r_t_opt": fr(pr["R_at_T"], 3), "cout_opt": fr(pr["cost_opt"], 4), "cout_rtf": fr(pr["cost_rtf"], 4),
        "gain_preventif": fr(pr["saving_pct"], 0),
        # santé
        "rul_critique": str(H["critical_rul"]), "prob_surveillance": fr(PROB_WATCH),
        "seuil_tendance": fr(TREND_THRESHOLD), "fenetre": str(WINDOW),
        "gb_auc_cv": fr(cl["Gradient Boosting"]["cv"]["auc"], 3), "gb_auc": fr(cl["Gradient Boosting"]["test"]["auc"], 3),
        "gb_rappel": fr(cl["Gradient Boosting"]["test"]["recall"], 3),
        "gb_precision": fr(cl["Gradient Boosting"]["test"]["precision"], 3),
        "gb_f1": fr(cl["Gradient Boosting"]["test"]["f1"], 3), "gb_exactitude": fr(cl["Gradient Boosting"]["test"]["accuracy"], 3),
        "gb_rappel_cv": fr(cl["Gradient Boosting"]["cv"]["recall"], 3),
        "svm_auc_cv": fr(cl["SVM (RBF)"]["cv"]["auc"], 3), "svm_auc": fr(cl["SVM (RBF)"]["test"]["auc"], 3),
        "svm_rappel": fr(cl["SVM (RBF)"]["test"]["recall"], 3), "svm_precision": fr(cl["SVM (RBF)"]["test"]["precision"], 3),
        "cm_tn": fr(best["test"]["cm"]["tn"], 0), "cm_fp": fr(best["test"]["cm"]["fp"], 0),
        "cm_fn": fr(best["test"]["cm"]["fn"], 0), "cm_tp": fr(best["test"]["cm"]["tp"], 0),
        "n_critiques_test": fr(best["test"]["cm"]["tp"] + best["test"]["cm"]["fn"], 0),
        "etat_normal": str(H["fleet_states"].get("Normal", 0)), "etat_surveillance": str(H["fleet_states"].get("Surveillance", 0)),
        "etat_critique": str(H["fleet_states"].get("Critique", 0)), "seuil_hi": fr(H["hi_threshold"], 3),
        # RUL
        "deg_rmse": fr(M["deg"]["rmse"], 2), "deg_mae": fr(M["deg"]["mae"], 2), "deg_biais": fr(M["deg"]["bias"], 1, True),
        "deg_score": fr(M["deg"]["score"], 0), "deg_within15": fr(M["deg"]["within15"], 0), "deg_tardif": fr(M["deg"]["late_pct"], 0),
        "lstm_rmse": fr(M["lstm"]["rmse"], 2), "lstm_mae": fr(M["lstm"]["mae"], 2), "lstm_biais": fr(M["lstm"]["bias"], 1, True),
        "lstm_score": fr(M["lstm"]["score"], 0), "lstm_within15": fr(M["lstm"]["within15"], 0),
        "lstm_tardif": fr(M["lstm"]["late_pct"], 0),
        "ens_rmse": fr(M["ensemble"]["rmse"], 2), "ens_score": fr(M["ensemble"]["score"], 0),
        "couverture_80": fr(DI["coverage_10_90"], 0),
        "couverture_50": fr(DI["calibration"][0]["couverture"], 0), "couverture_90": fr(DI["calibration"][2]["couverture"], 0),
        "largeur_80": fr(DI["calibration"][1]["largeur_moyenne"]),
        "biais_median": fr(DI["biais"]["median"], 1, True), "rmse_hors_biais": fr(DI["biais"]["rmse_hors_biais"], 1),
        "biais_t1": fr(DI["biais"]["par_tranche"][0]["biais"], 1, True),
        "biais_t2": fr(DI["biais"]["par_tranche"][1]["biais"], 1, True),
        "biais_t3": fr(DI["biais"]["par_tranche"][2]["biais"], 1, True),
        "couv_t3": fr(DI["biais"]["par_tranche"][2]["couverture_80"], 0),
        "seuil_deg": fr(DI["threshold"], 3), "seuil_deg_std": fr(DI["threshold_std"], 3), "sigma_deg": fr(DI["sigma"], 3),
        "n_tirages": fr(N_SAMPLES, 0), "horizon": str(HORIZON), "seq": str(SEQ), "rul_cap": str(RUL_CAP),
        "lstm_epoques": str(len(R["lstm_info"]["history"])), "lstm_val_rmse": fr(R["lstm_info"]["best_val_rmse"], 2),
        # exécution
        "python": I["python"],
        "v_numpy": I["bibliotheques"]["numpy"], "v_pandas": I["bibliotheques"]["pandas"],
        "v_sklearn": I["bibliotheques"]["scikit-learn"], "v_lifelines": I["bibliotheques"]["lifelines"],
        "v_torch": I["bibliotheques"]["torch"], "v_fastapi": I["bibliotheques"]["fastapi"],
    }
    return dict(sorted(v.items()))


def main():
    F, H, R, D, I = (charger(n) for n in ("fmds", "health", "rul", "dataset", "run_info"))
    (REPORT / "tables").mkdir(parents=True, exist_ok=True)
    (REPORT / "generated").mkdir(parents=True, exist_ok=True)
    T = tableaux(F, H, R, D)
    for t in T:
        (REPORT / "tables" / f"{t.nom}.md").write_text(t.markdown(), encoding="utf-8")
        (REPORT / "tables" / f"{t.nom}.tex").write_text(t.latex(), encoding="utf-8")
        print(f"  -> report/tables/{t.nom}.md / .tex")
    titres = {t.nom: t.titre for t in T}
    v = valeurs(F, H, R, D, I)
    (REPORT / "generated" / "valeurs.json").write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
    (REPORT / "generated" / "tableaux.json").write_text(json.dumps(titres, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  -> report/generated/valeurs.json ({len(v)} valeurs), {len(T)} tableaux")


if __name__ == "__main__":
    main()
