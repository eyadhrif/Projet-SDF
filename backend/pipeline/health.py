"""PDM-02 — Classification de l'état de santé : normal / critique (Eya).

Étiquette : un cycle est « critique » si le RUL réel est ≤ 30 cycles (fenêtre d'intervention).
Modèles : Gradient Boosting et SVM (RBF) sur les features temporelles + HI.
Validation : GroupKFold par moteur (pas de fuite entre moteurs), puis jeu de test NASA.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.metrics import (roc_auc_score, roc_curve, confusion_matrix, accuracy_score,
                             precision_score, recall_score, f1_score)

CRITICAL_RUL = 30
PROB_WATCH = 0.2       # seuil « surveillance » sur la probabilité de criticité


def make_models():
    return {
        "Gradient Boosting": HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.05, max_leaf_nodes=31, random_state=0),
        "SVM (RBF)": make_pipeline(StandardScaler(), CalibratedClassifierCV(
            SVC(C=3.0, gamma="scale", random_state=0), ensemble=False)),
    }


def _metrics(y, p, thr=0.5):
    yhat = (p >= thr).astype(int)
    fpr, tpr, _ = roc_curve(y, p)
    keep = np.unique(np.linspace(0, len(fpr) - 1, min(120, len(fpr))).astype(int))
    tn, fp, fn, tp = confusion_matrix(y, yhat, labels=[0, 1]).ravel()
    return {
        "auc": round(float(roc_auc_score(y, p)), 4),
        "accuracy": round(float(accuracy_score(y, yhat)), 4),
        "precision": round(float(precision_score(y, yhat, zero_division=0)), 4),
        "recall": round(float(recall_score(y, yhat)), 4),
        "f1": round(float(f1_score(y, yhat)), 4),
        "cm": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "roc": [{"fpr": round(float(fpr[i]), 4), "tpr": round(float(tpr[i]), 4)} for i in keep],
    }


def train_health_classifier(Xtr, ytr, groups, Xte, yte):
    results, fitted = {}, {}
    # sous-échantillonnage pour le SVM (coût O(n²))
    rng = np.random.default_rng(0)
    for name, model in make_models().items():
        if name.startswith("SVM"):
            idx = rng.choice(len(Xtr), size=min(6000, len(Xtr)), replace=False)
            Xf, yf, gf = Xtr.iloc[idx], ytr.iloc[idx], groups.iloc[idx]
        else:
            Xf, yf, gf = Xtr, ytr, groups
        p_cv = cross_val_predict(model, Xf, yf, groups=gf, cv=GroupKFold(5), method="predict_proba")[:, 1]
        model.fit(Xf, yf)
        p_te = model.predict_proba(Xte)[:, 1]
        results[name] = {"cv": _metrics(yf.values, p_cv), "test": _metrics(yte.values, p_te)}
        fitted[name] = model
    best = max(results, key=lambda k: results[k]["test"]["auc"])
    return results, fitted, best


def state_from_prob(p):
    return np.where(p >= 0.5, "Critique", np.where(p >= PROB_WATCH, "Surveillance", "Normal"))
