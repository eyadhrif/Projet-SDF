"""A3 — Figures du rapport, générées à partir de results/*.json (Eya + Salma).

    python report_figures.py        # -> report/figures/*.png (300 dpi) et *.pdf

Aucune donnée n'est recalculée ici : chaque figure ne fait que tracer les résultats exportés par
run_all.py, ce qui garantit que le rapport montre exactement les chiffres du dashboard.
Style sobre pour l'impression : libellés en français, virgule décimale, un seul axe vertical par
graphique (deux grandeurs d'échelles différentes -> deux panneaux), palette validée pour les
daltoniens (3 couleurs) ; le modèle de dégradation est toujours en bleu, le LSTM en orange.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                     # noqa: E402
import numpy as np                                  # noqa: E402
from matplotlib.ticker import FuncFormatter         # noqa: E402

ROOT = Path(__file__).resolve().parent
RES = ROOT / "results"
OUT = ROOT.parent / "report" / "figures"

# palette (validée : 3 couleurs distinguables, y compris en vision des couleurs altérée)
BLEU, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
ENCRE, ENCRE2, GRIS, GRILLE = "#0b0b0b", "#52514e", "#9a9893", "#e6e5e0"
DEG, LSTM = BLEU, ORANGE
L_PLEINE, L_DEMI = 6.3, 3.1                        # largeurs en pouces (16 cm et 8 cm)

plt.rcParams.update({
    "font.size": 8.5, "axes.titlesize": 9, "axes.labelsize": 8.5, "legend.fontsize": 7.5,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "axes.edgecolor": GRIS, "axes.labelcolor": ENCRE,
    "xtick.color": ENCRE2, "ytick.color": ENCRE2, "text.color": ENCRE, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": GRILLE, "grid.linewidth": 0.5,
    "axes.axisbelow": True, "lines.linewidth": 1.5, "legend.frameon": False, "figure.dpi": 100,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.03, "pdf.fonttype": 42,
})

_virgule = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",").replace("-", "−"))


def charger(nom):
    return json.loads((RES / f"{nom}.json").read_text(encoding="utf-8"))


def finir(fig, nom, axes=None):
    """Virgule décimale sur tous les axes numériques, puis export PNG 300 dpi + PDF."""
    for ax in (axes if axes is not None else fig.axes):
        if ax.get_xscale() == "linear" and ax.xaxis.get_major_formatter().__class__.__name__ == "ScalarFormatter":
            ax.xaxis.set_major_formatter(_virgule)
        if ax.get_yscale() == "linear" and ax.yaxis.get_major_formatter().__class__.__name__ == "ScalarFormatter":
            ax.yaxis.set_major_formatter(_virgule)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{nom}.png", dpi=300)
    fig.savefig(OUT / f"{nom}.pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)
    return nom


def fr(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


# ================================================================= données
def fig_durees_de_vie(F, D):
    life = [l["time"] for l in F["dataset"]["lifetimes"] if l["status"] == 1]
    cens = [l["time"] for l in F["dataset"]["lifetimes"] if l["status"] == 0]
    fig, axs = plt.subplots(1, 2, figsize=(L_PLEINE, 2.3), sharey=False)
    axs[0].hist(life, bins=np.arange(120, 381, 20), color=BLEU, edgecolor="white", linewidth=1)
    axs[0].axvline(min(life), color=ENCRE2, ls="--", lw=1)
    axs[0].text(min(life) + 4, axs[0].get_ylim()[1] * 0.92, f"min. {min(life)}", fontsize=7, color=ENCRE2)
    axs[0].set(xlabel="durée de vie (cycles)", ylabel="moteurs", title="Entraînement : 100 défaillances observées")
    axs[1].hist(cens, bins=np.arange(0, 321, 20), color=GRIS, edgecolor="white", linewidth=1)
    axs[1].set(xlabel="dernier cycle observé", ylabel="moteurs", title="Test : 100 moteurs censurés à droite")
    return finir(fig, "donnees_durees_de_vie")


def fig_signaux(H):
    keys = ["s2", "s4", "s7", "s11", "s12", "s15"]
    pts = H["raw_sensors"]
    c = np.array([p["c"] for p in pts])
    fig, axs = plt.subplots(2, 3, figsize=(L_PLEINE, 3.2), sharex=True)
    for ax, k in zip(axs.flat, keys):
        v = np.array([p[k] for p in pts])
        ax.plot(c, v, color=GRIS, lw=0.8)
        lisse = np.convolve(v, np.ones(10) / 10, mode="valid")
        ax.plot(c[9:], lisse, color=BLEU, lw=1.5)
        ax.set_title(f"{k} — {H['sensor_info'][k].split(' — ')[0]}", fontsize=8)
    for ax in axs[1]:
        ax.set_xlabel("cycle")
    fig.suptitle("Moteur d'entraînement n° 1 : signaux bruts (gris) et moyenne glissante sur 10 cycles (bleu)",
                 fontsize=8.5, y=1.0)
    fig.tight_layout()
    return finir(fig, "donnees_signaux_moteur1")


# ================================================================= fiabilité (FMDS-01)
def fig_fiabilite(F):
    fi = F["fiabilite"]
    km = fi["km"]
    t = [p["t"] for p in km]
    fig, ax = plt.subplots(figsize=(L_PLEINE, 2.9))
    ax.fill_between(t, [p["lo"] for p in km], [p["hi"] for p in km], step="post", color=BLEU, alpha=0.15,
                    lw=0, label="IC 95 % (Greenwood, log-log)")
    ax.step(t, [p["R"] for p in km], where="post", color=BLEU, lw=1.5, label="Kaplan-Meier")
    cv = [c for c in fi["curves"] if c["t"] <= 380]
    tc = [c["t"] for c in cv]
    ax.plot(tc, [c["R_w3"] for c in cv], color=ORANGE, lw=1.8, label="Weibull 3P (retenue)")
    ax.plot(tc, [c["R_w2"] for c in cv], color=AQUA, lw=1.3, ls="--", label="Weibull 2P (MV, rejetée)")
    ce = fi["censored"]
    ax.plot([c["t"] for c in ce], [c["R"] for c in ce], "|", color=ENCRE2, ms=5, mew=0.8, label="censures")
    ax.axvline(fi["w3"]["gamma"], color=ENCRE2, ls=":", lw=1)
    ax.text(fi["w3"]["gamma"] + 3, 0.08, f"γ = {fr(fi['w3']['gamma'])}", fontsize=7, color=ENCRE2)
    ax.set(xlabel="t (cycles)", ylabel="R(t)", xlim=(0, 380), ylim=(0, 1.03))
    ax.legend(loc="lower left")
    return finir(fig, "fiabilite_kaplan_meier")


def fig_weibull_mco(F):
    fi = F["fiabilite"]
    p = fi["weibull_plot"]
    fig, ax = plt.subplots(figsize=(L_DEMI, 2.6))
    ax.plot([q["x"] for q in p], [q["y"] for q in p], "o", color=BLEU, ms=3, mew=0, alpha=0.8, label="durées observées")
    ax.plot([q["x"] for q in p], [q["fit"] for q in p], color=ORANGE, lw=1.5, label="droite MCO")
    ax.set(xlabel="ln t", ylabel="ln(−ln(1 − F))")
    ax.text(0.03, 0.97, f"β = {fr(fi['mco']['beta'], 2)} ; η = {fr(fi['mco']['eta'])}\nR² = {fr(fi['mco']['r2'], 3)}",
            transform=ax.transAxes, va="top", fontsize=7)
    ax.legend(loc="lower right")
    return finir(fig, "fiabilite_diagramme_weibull")


def fig_taux(F):
    fi = F["fiabilite"]
    hz = [h for h in fi["hazard"] if h["t"] <= 360]
    cv = [c for c in fi["curves"] if c["t"] <= 360]
    fig, ax = plt.subplots(figsize=(L_DEMI, 2.6))
    ax.plot([h["t"] for h in hz], [h["h"] for h in hz], color=BLEU, label="Nelson-Aalen lissé")
    ax.plot([c["t"] for c in cv], [c["lam"] for c in cv], color=ORANGE, ls="--", label="Weibull 3P")
    ax.set(xlabel="t (cycles)", ylabel="λ(t) (par cycle)")
    ax.legend(loc="upper left")
    return finir(fig, "fiabilite_taux_defaillance")


def fig_densite(F):
    cv = [c for c in F["fiabilite"]["curves"] if c["t"] <= 380]
    t = [c["t"] for c in cv]
    fig, axs = plt.subplots(1, 2, figsize=(L_PLEINE, 2.2))
    axs[0].fill_between(t, [c["f"] for c in cv], color=ORANGE, alpha=0.15, lw=0)
    axs[0].plot(t, [c["f"] for c in cv], color=ORANGE)
    axs[0].set(xlabel="t (cycles)", ylabel="f(t)", title="Densité de défaillance")
    axs[1].plot(t, [c["F"] for c in cv], color=ORANGE)
    axs[1].set(xlabel="t (cycles)", ylabel="F(t)", title="Fonction de répartition F = 1 − R", ylim=(0, 1.02))
    for q, lab in ((F["fiabilite"]["b10"], "B10"), (F["fiabilite"]["b50"], "B50")):
        axs[1].axvline(q, color=ENCRE2, ls=":", lw=1)
        axs[1].text(q + 3, 0.05 if lab == "B10" else 0.15, f"{lab} = {fr(q)}", fontsize=7, color=ENCRE2)
    fig.tight_layout()
    return finir(fig, "fiabilite_densite_repartition")


def fig_conditionnelle(F):
    c = F["fiabilite"]["conditional"]
    fig, ax = plt.subplots(figsize=(L_DEMI, 2.4))
    ax.plot([p["t"] for p in c], [p["Rc"] for p in c], "o-", color=BLEU, ms=3)
    ax.axhline(0.9, color=ENCRE2, ls=":", lw=1)
    ax.set(xlabel="âge atteint t (cycles)", ylabel="R(t + 25 | t)", ylim=(0, 1.03))
    return finir(fig, "fiabilite_conditionnelle")


# ================================================================= FMDS-02
def fig_maintenabilite(F):
    m = F["maintenabilite"]
    fig, axs = plt.subplots(1, 2, figsize=(L_PLEINE, 2.3))
    axs[0].hist(m["samples"], bins=14, color=ORANGE, edgecolor="white", linewidth=1)
    axs[0].set(xlabel="temps de réparation simulé (h)", ylabel="réparations", title="Échantillon simulé (n = 100)")
    axs[1].plot([p["t"] for p in m["M"]], [p["M"] for p in m["M"]], color=ORANGE)
    for x, lab in ((m["mttr_h"], "MTTR"), (m["t90_h"], "t90")):
        axs[1].axvline(x, color=ENCRE2, ls=":", lw=1)
        axs[1].text(x + 0.8, 0.1 if lab == "MTTR" else 0.25, f"{lab} = {fr(x)} h", fontsize=7, color=ENCRE2)
    axs[1].set(xlabel="t (h)", ylabel="M(t)", title="Maintenabilité (log-normale, MV)", xlim=(0, 60), ylim=(0, 1.02))
    fig.tight_layout()
    return finir(fig, "fmds_maintenabilite")


def fig_disponibilite(F):
    d = F["disponibilite"]
    fig, ax = plt.subplots(figsize=(L_DEMI, 2.4))
    ax.plot([p["t"] for p in d["A_t"]], [p["A"] for p in d["A_t"]], color=BLEU)
    ax.axhline(d["A"], color=ENCRE2, ls=":", lw=1)
    ax.text(30, d["A"] + 0.002, f"A∞ = {fr(100 * d['A'], 2)} %", fontsize=7, color=ENCRE2)
    ax.set(xlabel="t (cycles)", ylabel="A(t)", ylim=(0.95, 1.002))
    return finir(fig, "fmds_disponibilite")


def fig_preventif(F):
    p = F["preventif"]
    fig, ax = plt.subplots(figsize=(L_PLEINE, 2.4))
    ax.plot([c["T"] for c in p["curve"]], [c["cost"] for c in p["curve"]], color=BLEU, label="politique d'âge T")
    ax.axhline(p["cost_rtf"], color=ENCRE2, ls="--", lw=1, label="maintenance corrective seule")
    ax.axvline(p["T_opt"], color=ORANGE, ls=":", lw=1.2)
    ax.plot([p["T_opt"]], [p["cost_opt"]], "o", color=ORANGE, ms=5)
    ax.annotate(f"T* = {fr(p['T_opt'])} cycles\ncoût −{fr(p['saving_pct'], 0)} %", xy=(p["T_opt"], p["cost_opt"]),
                xytext=(p["T_opt"] + 70, p["cost_opt"]), va="center", fontsize=7, color=ENCRE,
                arrowprops=dict(arrowstyle="-", color=ENCRE2, lw=0.6))
    ax.set(xlabel="âge de remplacement préventif T (cycles)", ylabel="coût moyen par cycle (unités de Cp)")
    ax.legend(loc="lower right")
    return finir(fig, "fmds_remplacement_preventif")


# ================================================================= santé (PDM-01, PDM-02)
def fig_capteurs(H):
    rk = sorted(H["sensor_ranking"], key=lambda d: d["trend"])
    fig, ax = plt.subplots(figsize=(L_DEMI, 2.9))
    cols = [BLEU if d["selected"] else GRILLE for d in rk]
    ax.barh([d["sensor"] for d in rk], [d["trend"] for d in rk], color=cols, height=0.7)
    for x in (-0.5, 0.5):
        ax.axvline(x, color=ENCRE2, ls=":", lw=1)
    ax.set(xlabel="tendance (corrélation moyenne avec le cycle)", xlim=(-1, 1))
    ax.set_title(f"Retenus : |tendance| ≥ 0,5 (bleu)\nconstants écartés : {', '.join(H['dropped'])}", fontsize=7.5)
    ax.grid(axis="y", visible=False)
    return finir(fig, "sante_selection_capteurs")


def fig_hi(H):
    fig, ax = plt.subplots(figsize=(L_PLEINE, 2.5))
    for u in H["hi_train"]:
        ax.plot([p["c"] for p in u["pts"]], [p["hi"] for p in u["pts"]], color=GRIS, lw=0.9)
    ax.axhline(H["hi_threshold"], color=ORANGE, ls="--", lw=1.2, label=f"seuil de défaillance = {fr(H['hi_threshold'], 3)}")
    ax.plot([], [], color=GRIS, label="10 moteurs d'entraînement")
    ax.set(xlabel="cycle", ylabel="indicateur de santé (HI)", ylim=(-0.6, 1.3))
    ax.legend(loc="lower left", ncol=2)
    return finir(fig, "sante_indicateur")


def fig_poids(H):
    w = sorted(H["hi_weights"], key=lambda d: d["w"])
    fig, ax = plt.subplots(figsize=(L_DEMI, 2.6))
    ax.barh([d["sensor"] for d in w], [d["w"] for d in w], color=[BLEU if d["w"] > 0 else ORANGE for d in w], height=0.7)
    ax.axvline(0, color=ENCRE2, lw=0.8)
    ax.set(xlabel="poids dans le HI (capteur standardisé)")
    ax.grid(axis="y", visible=False)
    return finir(fig, "sante_poids_hi")


def fig_roc(H):
    fig, ax = plt.subplots(figsize=(L_DEMI, 2.7))
    for (nom, m), col, ls in zip(H["classifiers"].items(), (BLEU, ORANGE), ("-", "--")):
        roc = m["test"]["roc"]
        ax.plot([p["fpr"] for p in roc], [p["tpr"] for p in roc], color=col, ls=ls,
                label=f"{nom} (AUC {fr(m['test']['auc'], 3)})")
    ax.plot([0, 1], [0, 1], color=GRIS, ls=":", lw=1)
    ax.set(xlabel="taux de faux positifs", ylabel="taux de vrais positifs", xlim=(0, 1), ylim=(0, 1.01))
    ax.legend(loc="lower right")
    return finir(fig, "sante_roc")


def fig_confusion(H):
    cm = H["classifiers"][H["best"]]["test"]["cm"]
    M = np.array([[cm["tn"], cm["fp"]], [cm["fn"], cm["tp"]]])
    fig, ax = plt.subplots(figsize=(L_DEMI, 2.3))
    ax.imshow(M / M.sum(axis=1, keepdims=True), cmap="Blues", vmin=0, vmax=1.4)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{M[i, j]:,}".replace(",", " ") + f"\n({fr(100 * M[i, j] / M[i].sum())} %)",
                    ha="center", va="center", fontsize=8)
    ax.set_xticks([0, 1], ["prédit normal", "prédit critique"])
    ax.set_yticks([0, 1], ["réel normal", "réel critique"])
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    return finir(fig, "sante_matrice_confusion", axes=[])


# ================================================================= RUL
def fig_rul_pred_reel(R):
    t = R["table"]
    fig, axs = plt.subplots(1, 2, figsize=(L_PLEINE, 2.9), sharex=True, sharey=True)
    for ax, k, col, nom in ((axs[0], "deg", DEG, "Dégradation bayésienne"), (axs[1], "lstm", LSTM, "LSTM")):
        ax.plot([0, 220], [0, 220], color=GRIS, ls=":", lw=1)
        ax.plot([r["true"] for r in t], [r[k] for r in t], "o", color=col, ms=3.5, mew=0, alpha=0.8)
        m = R["metrics"][k]
        ax.set(title=f"{nom} — RMSE {fr(m['rmse'], 2)}", xlabel="RUL réel (cycles)", xlim=(0, 220), ylim=(0, 220))
    axs[0].set_ylabel("RUL prédit (cycles)")
    fig.tight_layout()
    return finir(fig, "rul_predit_vs_reel")


def fig_rul_erreurs(R):
    t = R["table"]
    bins = np.arange(-80, 81, 10)
    fig, axs = plt.subplots(1, 2, figsize=(L_PLEINE, 2.2), sharey=True)
    for ax, k, col, nom in ((axs[0], "deg", DEG, "Dégradation bayésienne"), (axs[1], "lstm", LSTM, "LSTM")):
        e = [r[k] - r["true"] for r in t]
        ax.hist(np.clip(e, -80, 79.9), bins=bins, color=col, edgecolor="white", linewidth=1)
        ax.axvline(0, color=ENCRE, lw=0.8)
        ax.set(title=f"{nom} — biais {fr(R['metrics'][k]['bias'], 1)}", xlabel="erreur = prédit − réel (cycles)")
    axs[0].set_ylabel("moteurs")
    fig.tight_layout()
    return finir(fig, "rul_erreurs")


def fig_rul_flotte(R):
    t = sorted(R["table"], key=lambda r: r["true"])
    i = np.arange(1, len(t) + 1)
    fig, ax = plt.subplots(figsize=(L_PLEINE, 2.7))
    ax.vlines(i, [r["deg_p10"] for r in t], [r["deg_p90"] for r in t], color=DEG, alpha=0.3, lw=2.2,
              label="intervalle 10–90 % (dégradation)")
    ax.plot(i, [r["true"] for r in t], color=ENCRE, lw=1.5, label="RUL réel")
    ax.plot(i, [r["deg"] for r in t], "o", color=DEG, ms=2.8, mew=0, label="dégradation (médiane)")
    ax.plot(i, [r["lstm"] for r in t], "s", color=LSTM, ms=2.6, mew=0, label="LSTM")
    ax.set(xlabel="moteurs de test triés par RUL réel croissant", ylabel="RUL (cycles)", ylim=(0, 250), xlim=(0, 101))
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=4)
    return finir(fig, "rul_flotte")


def fig_calibration(R):
    c = R["deg_info"]["calibration"]
    fig, ax = plt.subplots(figsize=(L_DEMI, 2.5))
    ax.plot([0, 100], [0, 100], color=GRIS, ls=":", lw=1, label="calibration parfaite")
    ax.plot([x["nominal"] for x in c], [x["couverture"] for x in c], "o-", color=DEG, ms=4, label="modèle de dégradation")
    for x in c:
        ax.text(x["nominal"] + 2, x["couverture"] - 6, f"{fr(x['couverture'], 0)} %", fontsize=7, color=ENCRE2)
    ax.set(xlabel="niveau nominal de l'intervalle (%)", ylabel="couverture observée (%)", xlim=(0, 100), ylim=(0, 100))
    ax.legend(loc="upper left")
    return finir(fig, "rul_calibration")


def fig_lstm(R):
    h = R["lstm_info"]["history"]
    fig, ax = plt.subplots(figsize=(L_DEMI, 2.4))
    ax.plot([p["epoch"] for p in h], [p["train_rmse"] for p in h], color=LSTM, label="entraînement")
    ax.plot([p["epoch"] for p in h], [p["val_rmse"] for p in h], color=ENCRE2, ls="--", label="validation (15 moteurs)")
    ax.set(xlabel="époque", ylabel="RMSE (cycles, cible plafonnée)", ylim=(0, None))
    ax.legend(loc="upper right")
    return finir(fig, "rul_apprentissage_lstm")


def fig_moteur(R, E, unit=31):
    e, row = E[str(unit)], next(r for r in R["table"] if r["unit"] == unit)
    s = e["series"]
    fig, axs = plt.subplots(1, 2, figsize=(L_PLEINE, 2.6))
    c = [p["c"] for p in s]
    axs[0].plot(c, [p["true"] for p in s], color=ENCRE, label="RUL réel")
    axs[0].plot([p["c"] for p in s if p["lstm"] is not None], [p["lstm"] for p in s if p["lstm"] is not None],
                color=LSTM, label="LSTM")
    axs[0].plot([p["c"] for p in s if p["deg"] is not None], [p["deg"] for p in s if p["deg"] is not None], "o-",
                color=DEG, ms=2.5, lw=1, label="dégradation")
    axs[0].set(xlabel="cycle", ylabel="RUL (cycles)", title=f"Moteur de test n° {unit} : RUL prédit au fil des cycles",
               ylim=(0, None))
    axs[0].legend(loc="upper right")
    last = e["last_cycle"]
    axs[1].axvspan(last + row["deg_p10"], last + row["deg_p90"], color=DEG, alpha=0.12, lw=0, label="intervalle 10–90 %")
    axs[1].plot(c, [p["hr"] for p in s], color=GRIS, lw=0.8, label="HI mesuré")
    axs[1].plot([p["c"] for p in e["projection"]], [p["proj"] for p in e["projection"]], color=DEG, label="projection")
    axs[1].axhline(R["deg_info"]["threshold"], color=ORANGE, ls="--", lw=1, label="seuil")
    axs[1].axvline(last + e["true_end"], color=ENCRE, ls=":", lw=1, label="défaillance réelle")
    axs[1].set(xlabel="cycle", ylabel="HI", ylim=(-1.15, 1.3), title="Projection du HI jusqu'au seuil")
    axs[1].legend(loc="lower left", fontsize=6.5, ncol=2)
    fig.tight_layout()
    return finir(fig, "rul_exemple_moteur")


FIGURES = [
    ("donnees_durees_de_vie", lambda d: fig_durees_de_vie(d["fmds"], d["dataset"])),
    ("donnees_signaux_moteur1", lambda d: fig_signaux(d["health"])),
    ("fiabilite_kaplan_meier", lambda d: fig_fiabilite(d["fmds"])),
    ("fiabilite_diagramme_weibull", lambda d: fig_weibull_mco(d["fmds"])),
    ("fiabilite_taux_defaillance", lambda d: fig_taux(d["fmds"])),
    ("fiabilite_densite_repartition", lambda d: fig_densite(d["fmds"])),
    ("fiabilite_conditionnelle", lambda d: fig_conditionnelle(d["fmds"])),
    ("fmds_maintenabilite", lambda d: fig_maintenabilite(d["fmds"])),
    ("fmds_disponibilite", lambda d: fig_disponibilite(d["fmds"])),
    ("fmds_remplacement_preventif", lambda d: fig_preventif(d["fmds"])),
    ("sante_selection_capteurs", lambda d: fig_capteurs(d["health"])),
    ("sante_indicateur", lambda d: fig_hi(d["health"])),
    ("sante_poids_hi", lambda d: fig_poids(d["health"])),
    ("sante_roc", lambda d: fig_roc(d["health"])),
    ("sante_matrice_confusion", lambda d: fig_confusion(d["health"])),
    ("rul_predit_vs_reel", lambda d: fig_rul_pred_reel(d["rul"])),
    ("rul_erreurs", lambda d: fig_rul_erreurs(d["rul"])),
    ("rul_flotte", lambda d: fig_rul_flotte(d["rul"])),
    ("rul_calibration", lambda d: fig_calibration(d["rul"])),
    ("rul_apprentissage_lstm", lambda d: fig_lstm(d["rul"])),
    ("rul_exemple_moteur", lambda d: fig_moteur(d["rul"], d["engines"])),
]


def main():
    data = {n: charger(n) for n in ("fmds", "health", "rul", "engines", "dataset")}
    for nom, f in FIGURES:
        assert f(data) == nom
        print(f"  -> report/figures/{nom}.png / .pdf")
    print(f"{len(FIGURES)} figures")


if __name__ == "__main__":
    main()
