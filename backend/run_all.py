"""Exécute toute la chaîne (sprints 1 à 3) et exporte les résultats JSON pour le dashboard.

    python run_all.py            # ~2-4 min sur CPU
"""
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from pipeline.data import load_fd001, lifetime_table, SENSOR_INFO
from pipeline.fmds import compute_fmds
from pipeline.features import sensor_ranking, window_features, HealthIndicator
from pipeline.health import train_health_classifier, state_from_prob, CRITICAL_RUL
from pipeline.rul_degradation import DegradationRUL
from pipeline.rul_lstm import LSTMRUL, RUL_CAP, SEQ

ROOT = Path(__file__).resolve().parent
RES = ROOT / "results"
MOD = ROOT / "models"
RES.mkdir(exist_ok=True)
MOD.mkdir(exist_ok=True)


def dump(name, obj):
    with open(RES / name, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  -> results/{name} ({(RES / name).stat().st_size / 1024:.0f} Ko)")


def nasa_score(pred, true):
    d = np.asarray(pred) - np.asarray(true)
    return float(np.sum(np.where(d < 0, np.exp(-d / 13) - 1, np.exp(d / 10) - 1)))


def r(x, n=2):
    return round(float(x), n)


def main():
    t0 = time.time()
    print("[S0] Chargement C-MAPSS FD001")
    train, test, rul_end = load_fd001()
    life = lifetime_table(train, test)

    # ------------------------------------------------------------ Sprint 1
    print("[S1] Indices FMDS")
    fmds = compute_fmds(life)
    fmds["dataset"] = {
        "name": "NASA C-MAPSS FD001", "train_units": int(train.unit.nunique()),
        "test_units": int(test.unit.nunique()), "train_rows": int(len(train)),
        "test_rows": int(len(test)), "sensors": 21,
        "life_min": int(life[life.status == 1].time.min()),
        "life_max": int(life[life.status == 1].time.max()),
        "life_mean": r(life[life.status == 1].time.mean(), 1),
        "lifetimes": [{"unit": int(u), "time": int(t), "status": int(s), "source": src}
                      for u, t, s, src in life[["unit", "time", "status", "source"]].values],
    }
    dump("fmds.json", fmds)

    # ------------------------------------------------------------ Sprint 2
    print("[S2] Features, indicateur de santé, classification")
    rank, selected, dropped = sensor_ranking(train)
    hi = HealthIndicator(selected).fit(train)
    for df in (train, test):
        df["HI_raw"] = hi.raw(df)
        df["HI"] = hi.transform(df)

    Ftr = window_features(train, selected)
    Fte = window_features(test, selected)
    for F, df in ((Ftr, train), (Fte, test)):
        F["HI"] = df["HI"]
        F["cycle"] = df["cycle"]
    ytr = (train.RUL <= CRITICAL_RUL).astype(int)
    yte = (test.RUL <= CRITICAL_RUL).astype(int)
    clf_res, clf_models, best_clf = train_health_classifier(Ftr, ytr, train.unit, Fte, yte)
    for k, v in clf_res.items():
        print(f"  {k:18s} AUC CV {v['cv']['auc']:.3f} | test AUC {v['test']['auc']:.3f} "
              f"F1 {v['test']['f1']:.3f}")
    test["p_crit"] = clf_models[best_clf].predict_proba(Fte)[:, 1]
    joblib.dump({"model": clf_models[best_clf], "features": list(Ftr.columns)}, MOD / "health_clf.joblib")
    joblib.dump(hi, MOD / "health_indicator.joblib")

    sample_units = [1, 12, 24, 34, 49, 66, 69, 81, 92, 100]
    hi_train = []
    for u in sample_units:
        g = train[train.unit == u]
        hi_train.append({"unit": u, "life": int(g.cycle.max()),
                         "pts": [{"c": int(c), "hi": r(h, 3)} for c, h in zip(g.cycle, g.HI)]})
    # trajectoires brutes de 4 capteurs illustratifs (moteur 1)
    g1 = train[train.unit == 1]
    raw_sensors = [{"c": int(c), **{s: r(g1.loc[i, s], 3) for s in ["s2", "s4", "s7", "s11", "s12", "s15"]}}
                   for i, c in zip(g1.index, g1.cycle)]

    # ------------------------------------------------------------ Sprint 3
    print("[S3a] RUL — modèle de dégradation (Eya)")
    deg = DegradationRUL().fit([(g.cycle.values, g.HI_raw.values) for _, g in train.groupby("unit")])
    print(f"  seuil HI = {deg.threshold:.3f} ± {deg.threshold_std:.3f}, σ = {deg.sigma2 ** .5:.3f}")
    joblib.dump(deg, MOD / "degradation_model.joblib")

    print("[S3b] RUL — LSTM (Salma)")
    lstm = LSTMRUL(selected).fit(train)
    lstm.save(MOD / "lstm_rul.pt")

    print("[S3c] Prédictions sur le jeu de test")
    rng = np.random.default_rng(0)
    rows, engines = [], {}
    for u, g in test.groupby("unit"):
        t, h = g.cycle.values, g.HI_raw.values
        d = deg.predict(t, h, rng)
        cyc, pl = lstm.predict_unit(g)
        true_rul = int(g.RUL.values[-1])
        p_now = float(g.p_crit.values[-1])
        rows.append({
            "unit": int(u), "cycles": int(t[-1]), "true": true_rul,
            "deg": r(d["rul"], 1), "deg_p10": r(d["p10"], 1), "deg_p90": r(d["p90"], 1),
            "lstm": r(pl[-1], 1), "hi": r(g.HI.values[-1], 3), "p_crit": r(p_now, 3),
            "state": str(state_from_prob(np.array([p_now]))[0]),
        })
        # trajectoire du RUL prédit au fil des cycles (pour la page RUL)
        traj_deg = {}
        for k in range(max(10, len(t) % 5), len(t) + 1, 5):
            traj_deg[int(t[k - 1])] = r(deg.predict(t[:k], h[:k], rng)["rul"], 1)
        traj_deg[int(t[-1])] = r(d["rul"], 1)
        lstm_map = dict(zip(cyc.astype(int), pl))
        gc, gm = deg.mean_curve(d["m"], 1, int(t[-1] + max(d["rul"], 5) + 20))
        engines[int(u)] = {
            "unit": int(u), "true_end": true_rul, "last_cycle": int(t[-1]),
            "series": [{"c": int(c), "hi": r(hh, 3), "hr": r(hr, 3), "p": r(pp, 3),
                        "true": int(rr), "lstm": (r(lstm_map[c], 1) if c in lstm_map else None),
                        "deg": traj_deg.get(int(c))}
                       for c, hh, hr, pp, rr in zip(g.cycle, g.HI, g.HI_raw, g.p_crit, g.RUL)],
            "projection": [{"c": int(c), "proj": r(v, 3)} for c, v in zip(gc, gm)],
            "deg_ci": [r(d["p10"], 1), r(d["p90"], 1)],
        }

    tab = pd.DataFrame(rows)
    metrics = {}
    for m in ("deg", "lstm"):
        e = tab[m] - tab["true"]
        metrics[m] = {
            "rmse": r(np.sqrt(np.mean(e ** 2))), "mae": r(np.mean(np.abs(e))),
            "bias": r(np.mean(e)), "score": r(nasa_score(tab[m], tab["true"]), 1),
            "within15": r(100 * np.mean(np.abs(e) <= 15), 1),
            "late_pct": r(100 * np.mean(e > 0), 1),
        }
        print(f"  {m:5s} RMSE {metrics[m]['rmse']:.2f}  MAE {metrics[m]['mae']:.2f}  "
              f"score NASA {metrics[m]['score']:.0f}")
    ens = (tab["deg"] + tab["lstm"]) / 2
    e = ens - tab["true"]
    metrics["ensemble"] = {"rmse": r(np.sqrt(np.mean(e ** 2))), "mae": r(np.mean(np.abs(e))),
                           "bias": r(np.mean(e)), "score": r(nasa_score(ens, tab["true"]), 1),
                           "within15": r(100 * np.mean(np.abs(e) <= 15), 1),
                           "late_pct": r(100 * np.mean(e > 0), 1)}
    cover = np.mean((tab["true"] >= tab["deg_p10"]) & (tab["true"] <= tab["deg_p90"]))
    bins = np.arange(-80, 81, 10)
    hist = []
    for lo in bins[:-1]:
        hist.append({"bin": f"{lo}", "deg": int(((tab.deg - tab.true) >= lo).mul((tab.deg - tab.true) < lo + 10).sum()),
                     "lstm": int(((tab.lstm - tab.true) >= lo).mul((tab.lstm - tab.true) < lo + 10).sum())})

    health = {
        "critical_rul": CRITICAL_RUL, "sensor_ranking": rank, "selected": selected, "dropped": dropped,
        "sensor_info": SENSOR_INFO, "hi_weights": hi.weights(), "hi_train": hi_train,
        "raw_sensors": raw_sensors, "hi_threshold": r(deg.threshold, 3),
        "classifiers": clf_res, "best": best_clf,
        "fleet_states": tab["state"].value_counts().to_dict(),
        "n_features": int(Ftr.shape[1]),
    }
    dump("health.json", health)
    dump("rul.json", {
        "metrics": metrics, "table": rows, "error_hist": hist,
        "deg_info": {"threshold": r(deg.threshold, 4), "threshold_std": r(deg.threshold_std, 4),
                     "sigma": r(deg.sigma2 ** .5, 4), "prior_mean": [r(x, 4) for x in deg.m0],
                     "coverage_10_90": r(100 * cover, 1)},
        "lstm_info": {"seq": SEQ, "cap": RUL_CAP, "history": lstm.history,
                      "best_val_rmse": r(lstm.best_val_rmse), "n_features": len(selected)},
    })
    dump("engines.json", engines)
    print(f"Terminé en {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
