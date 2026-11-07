"""Sprint 1 — Estimation des indices FMDS.

FMDS-01 (Eya)   : Fiabilité — Kaplan-Meier + IC, Nelson-Aalen, Weibull (MCO et MV), adéquation
FMDS-02 (Salma) : Maintenabilité (log-normale), MTBF / MTTR, disponibilité, politique de
                  remplacement préventif
Méthodes alignées sur le cours « Estimation des indices FMDS » (F. Ben Hmida).
"""
import numpy as np
import pandas as pd
from scipy import stats, integrate, optimize
from scipy.special import gamma as G
from lifelines import (KaplanMeierFitter, NelsonAalenFitter, WeibullFitter,
                       ExponentialFitter, LogNormalFitter)

# ---------------------------------------------------------------- hypothèses
HOURS_PER_CYCLE = 2.0          # 1 cycle = 1 vol ≈ 2 h d'exploitation (hypothèse)
TTR_MEDIAN_H = 16.0            # médiane du temps de réparation simulé (h)
TTR_SIGMA = 0.6                # écart-type du log du temps de réparation
COST_PREVENTIVE = 1.0          # coût relatif d'un remplacement préventif
COST_CORRECTIVE = 5.0          # coût relatif d'une défaillance en service
SEED = 42


def _r(x, n=4):
    return None if x is None or not np.isfinite(x) else round(float(x), n)


# ======================================================== FMDS-01 Fiabilité
def kaplan_meier(life: pd.DataFrame):
    km = KaplanMeierFitter(alpha=0.05).fit(life["time"], life["status"], label="KM")
    sf = km.survival_function_["KM"]
    ci = km.confidence_interval_  # IC 95 % log(-log) (Greenwood exponentiel)
    pts = [{"t": float(t), "R": _r(sf.loc[t]), "lo": _r(ci.iloc[i, 0]), "hi": _r(ci.iloc[i, 1])}
           for i, t in enumerate(sf.index)]
    cens = life[life.status == 0]["time"].values
    cens_pts = [{"t": float(t), "R": _r(float(km.predict(t)))} for t in np.sort(cens)]
    return km, pts, cens_pts


def nelson_aalen(life: pd.DataFrame, bandwidth=15.0):
    na = NelsonAalenFitter(alpha=0.05).fit(life["time"], life["status"])
    H = na.cumulative_hazard_.iloc[:, 0]
    sm = na.smoothed_hazard_(bandwidth=bandwidth).iloc[:, 0]  # lissage par noyau Epanechnikov
    pts = [{"t": float(t), "H": _r(H.loc[t]), "Rfh": _r(np.exp(-H.loc[t]))} for t in H.index]
    hz = [{"t": float(t), "h": _r(v, 6)} for t, v in sm.items() if t > 0]
    return pts, hz


def weibull_mco(times_complete: np.ndarray):
    """Moindres carrés ordinaires sur le diagramme de Weibull (rangs médians de Bernard)."""
    t = np.sort(times_complete)
    n = len(t)
    F = (np.arange(1, n + 1) - 0.3) / (n + 0.4)
    x, y = np.log(t), np.log(-np.log(1 - F))
    res = stats.linregress(x, y)
    beta = res.slope
    eta = np.exp(-res.intercept / beta)
    plot = [{"x": _r(a), "y": _r(b), "fit": _r(res.slope * a + res.intercept)} for a, b in zip(x, y)]
    return {"beta": beta, "eta": eta, "r2": res.rvalue ** 2}, plot


def weibull_mv(life: pd.DataFrame):
    """Maximum de vraisemblance avec censure à droite (moteurs de test)."""
    wf = WeibullFitter(alpha=0.05).fit(life["time"], life["status"])
    s = wf.summary
    return wf, {
        "beta": wf.rho_, "eta": wf.lambda_,
        "beta_ci": [s.loc["rho_", "coef lower 95%"], s.loc["rho_", "coef upper 95%"]],
        "eta_ci": [s.loc["lambda_", "coef lower 95%"], s.loc["lambda_", "coef upper 95%"]],
        "loglik": wf.log_likelihood_, "aic": wf.AIC_,
    }


def model_comparison(c: np.ndarray):
    """MV sur les durées complètes + test KS + AIC pour 4 lois candidates."""
    cands = {
        "Exponentielle": ("expon", dict(floc=0), 1),
        "Weibull 2P": ("weibull_min", dict(floc=0), 2),
        "Log-normale": ("lognorm", dict(floc=0), 2),
        "Weibull 3P": ("weibull_min", dict(), 3),
    }
    out, params = [], {}
    for name, (dist, kw, k) in cands.items():
        D = getattr(stats, dist)
        p = D.fit(c, **kw)
        ll = float(np.sum(D.logpdf(c, *p)))
        ks = stats.kstest(c, dist, args=p)
        params[name] = p
        out.append({"model": name, "k": k, "loglik": _r(ll, 2), "aic": _r(2 * k - 2 * ll, 2),
                    "ks_D": _r(ks.statistic), "ks_p": _r(ks.pvalue), "accept": bool(ks.pvalue > 0.05)})
    return out, params


class Weibull3:
    """R(t) = exp(-((t-γ)/η)^β) pour t > γ, 1 sinon."""
    def __init__(self, beta, gamma, eta):
        self.b, self.g, self.e = beta, gamma, eta

    def R(self, t):
        x = np.maximum(np.asarray(t, float) - self.g, 0) / self.e
        return np.exp(-x ** self.b)

    def lam(self, t):
        x = np.maximum(np.asarray(t, float) - self.g, 1e-9) / self.e
        return np.where(np.asarray(t) > self.g, (self.b / self.e) * x ** (self.b - 1), 0.0)

    def quantile(self, p):  # temps tel que F = p
        return self.g + self.e * (-np.log(1 - p)) ** (1 / self.b)

    def mttf(self):
        return self.g + self.e * G(1 + 1 / self.b)


def fiabilite(life: pd.DataFrame):
    km, km_pts, cens_pts = kaplan_meier(life)
    na_pts, hazard = nelson_aalen(life)
    complete = life[life.status == 1]["time"].values.astype(float)

    # Approche paramétrique (cours) : Weibull 2P par MCO puis par MV
    mco, mco_plot = weibull_mco(complete)
    comp, params = model_comparison(complete)
    b2, _, e2 = params["Weibull 2P"]
    _, mv_cens = weibull_mv(life)            # MV Weibull 2P avec censure à droite (pour comparaison)

    # Modèle retenu : Weibull 3P (période sans défaillance γ) — validé par KS
    b3, g3, e3 = params["Weibull 3P"]
    W = Weibull3(b3, g3, e3)
    ks_w2 = next(d for d in comp if d["model"] == "Weibull 2P")
    ks_w3 = next(d for d in comp if d["model"] == "Weibull 3P")

    tgrid = np.linspace(0, 400, 201)
    R3, lam3 = W.R(tgrid), W.lam(tgrid)
    curves = [{"t": float(t), "R_w3": _r(r), "R_w2": _r(np.exp(-(t / e2) ** b2)),
               "R_mco": _r(np.exp(-(t / mco["eta"]) ** mco["beta"])),
               "lam": _r(l, 6), "lam_w2": _r((b2 / e2) * (max(t, 1e-9) / e2) ** (b2 - 1), 6),
               "F": _r(1 - r), "f": _r(l * r, 6)}
              for t, r, l in zip(tgrid, R3, lam3)]

    km_mean = float(np.trapezoid(km.survival_function_["KM"].values,
                                 km.survival_function_.index.values))
    # Fiabilité conditionnelle : P(survivre 25 cycles de plus | a survécu jusqu'à t)
    cond = [{"t": float(t), "Rc": _r(float(W.R(t + 25) / max(W.R(t), 1e-12)))}
            for t in range(0, 301, 10)]

    return {
        "n_units": int(len(life)), "n_failures": int(life.status.sum()),
        "n_censored": int((life.status == 0).sum()),
        "km": km_pts, "censored": cens_pts, "na": na_pts, "hazard": hazard,
        "weibull_plot": mco_plot, "curves": curves, "conditional": cond,
        "mco": {k: _r(v) for k, v in mco.items()},
        "mv": {"beta": _r(b2), "eta": _r(e2), "ks_p": ks_w2["ks_p"]},
        "mv_cens": {"beta": _r(mv_cens["beta"]), "eta": _r(mv_cens["eta"]),
                    "beta_ci": [_r(x) for x in mv_cens["beta_ci"]],
                    "eta_ci": [_r(x) for x in mv_cens["eta_ci"]]},
        "w3": {"beta": _r(b3), "gamma": _r(g3, 2), "eta": _r(e3, 2), "ks_p": ks_w3["ks_p"]},
        "comparison": comp, "retained": "Weibull 3P",
        "mttf": _r(W.mttf(), 2), "mttf_km": _r(km_mean, 2),
        "median_km": _r(float(km.median_survival_time_), 1),
        "b10": _r(W.quantile(0.10), 1), "b1": _r(W.quantile(0.01), 1),
        "t_min_obs": _r(complete.min(), 0),
        "failure_mode": "croissant (usure)" if b3 > 1 else "constant/décroissant",
    }, W


# ===================================== FMDS-02 Maintenabilité & disponibilité
def maintenabilite(n_repairs: int):
    """Temps de réparation simulés (log-normale) puis ré-estimés par MV."""
    rng = np.random.default_rng(SEED)
    ttr_h = rng.lognormal(np.log(TTR_MEDIAN_H), TTR_SIGMA, n_repairs)
    s, loc, scale = stats.lognorm.fit(ttr_h, floc=0)
    mu, sigma = np.log(scale), s
    mttr_h = np.exp(mu + sigma ** 2 / 2)
    ks = stats.kstest(ttr_h, "lognorm", args=(s, 0, scale))
    tg = np.linspace(0.1, 80, 160)
    M = stats.lognorm.cdf(tg, s, 0, scale)
    hist, edges = np.histogram(ttr_h, bins=14)
    t90 = stats.lognorm.ppf(0.9, s, 0, scale)
    return {
        "mu": _r(mu), "sigma": _r(sigma), "mttr_h": _r(mttr_h, 2),
        "mttr_cycles": _r(mttr_h / HOURS_PER_CYCLE, 2),
        "repair_rate": _r(1 / mttr_h, 4), "t90_h": _r(t90, 2),
        "ks": {"D": _r(ks.statistic), "p": _r(ks.pvalue), "accept": bool(ks.pvalue > 0.05)},
        "M": [{"t": _r(t, 2), "M": _r(m)} for t, m in zip(tg, M)],
        "hist": [{"bin": f"{edges[i]:.0f}–{edges[i+1]:.0f}", "mid": _r((edges[i] + edges[i+1]) / 2, 1),
                  "n": int(hist[i])} for i in range(len(hist))],
        "samples": [_r(x, 2) for x in ttr_h],
    }, mttr_h / HOURS_PER_CYCLE


def disponibilite(mttf, mttr):
    mtbf = mttf + mttr                    # cycle de renouvellement : fonctionnement + réparation
    A = mttf / (mttf + mttr)
    lam, mu = 1 / mttf, 1 / mttr          # modèle markovien à 2 états (équivalent exponentiel)
    tg = np.linspace(0, 60, 121)
    At = mu / (lam + mu) + lam / (lam + mu) * np.exp(-(lam + mu) * tg)
    return {
        "mtbf": _r(mtbf, 2), "mut": _r(mttf, 2), "mdt": _r(mttr, 2),
        "A": _r(A, 5), "unavail_h_per_1000h": _r((1 - A) * 1000, 2),
        "lambda": _r(lam, 6), "mu": _r(mu, 5),
        "A_t": [{"t": _r(t, 1), "A": _r(a, 5)} for t, a in zip(tg, At)],
    }


def remplacement_preventif(W, mttr_corr):
    """Politique de remplacement à âge fixe T (Barlow-Proschan) : coût par cycle."""
    R = lambda t: float(W.R(t))

    def cost_rate(T):
        up = integrate.quad(R, 0, T)[0]
        return (COST_PREVENTIVE * R(T) + COST_CORRECTIVE * (1 - R(T))) / up

    def avail(T, mttr_prev=mttr_corr * 0.4):
        up = integrate.quad(R, 0, T)[0]
        down = mttr_prev * R(T) + mttr_corr * (1 - R(T))
        return up / (up + down)

    Ts = np.arange(100, 361, 4)
    curve = [{"T": int(T), "cost": _r(cost_rate(T), 6), "A": _r(avail(T), 5), "R": _r(R(T))} for T in Ts]
    opt = optimize.minimize_scalar(cost_rate, bounds=(W.g + 1, 400), method="bounded")
    T_star = opt.x
    cost_run_to_failure = COST_CORRECTIVE / W.mttf()
    return {
        "T_opt": _r(T_star, 1), "cost_opt": _r(cost_rate(T_star), 6),
        "cost_rtf": _r(cost_run_to_failure, 6),
        "saving_pct": _r(100 * (1 - cost_rate(T_star) / cost_run_to_failure), 1),
        "R_at_T": _r(R(T_star)), "Cp": COST_PREVENTIVE, "Cc": COST_CORRECTIVE,
        "curve": curve,
    }


def compute_fmds(life: pd.DataFrame):
    fia, W = fiabilite(life)
    mai, mttr_c = maintenabilite(int(life.status.sum()))
    dis = disponibilite(fia["mttf"], mttr_c)
    prev = remplacement_preventif(W, mttr_c)
    return {
        "assumptions": {
            "hours_per_cycle": HOURS_PER_CYCLE, "ttr_median_h": TTR_MEDIAN_H,
            "ttr_sigma": TTR_SIGMA, "Cp": COST_PREVENTIVE, "Cc": COST_CORRECTIVE,
            "censoring": "Moteurs de test traités comme censurés à droite au dernier cycle observé",
        },
        "fiabilite": fia, "maintenabilite": mai, "disponibilite": dis, "preventif": prev,
    }
