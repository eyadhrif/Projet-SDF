"""PDM-02 (Eya) — Tests de la classification normal / critique (backend/pipeline/health.py)."""
import joblib
import numpy as np
import pytest
from sklearn.metrics import (roc_auc_score, accuracy_score, precision_score, recall_score, f1_score,
                             confusion_matrix)
from sklearn.model_selection import GroupKFold

from conftest import MODELS
from pipeline.health import (CRITICAL_RUL, PROB_WATCH, _metrics, make_models, state_from_prob,
                             train_health_classifier)


@pytest.fixture(scope="module")
def clf():
    return joblib.load(MODELS / "health_clf.joblib")


@pytest.fixture(scope="module")
def p_test(clf, sprint2):
    return clf["model"].predict_proba(sprint2["Fte"][clf["features"]])[:, 1]


def labels(df):
    return (df.RUL <= CRITICAL_RUL).astype(int)


# ------------------------------------------------------------- étiquettes et validation
def test_seuil_de_criticite():
    assert CRITICAL_RUL == 30 and PROB_WATCH == 0.2


def test_etiquette_critique_si_rul_inferieur_ou_egal_30(sprint2):
    for df in (sprint2["train"], sprint2["test"]):
        y = labels(df)
        assert (y[df.RUL <= 30] == 1).all() and (y[df.RUL > 30] == 0).all()
    assert labels(sprint2["train"]).sum() == 100 * 31          # 31 derniers cycles de chaque moteur


def test_groupkfold_aucun_moteur_partage(sprint2):
    train = sprint2["train"]
    for tr, va in GroupKFold(5).split(sprint2["Ftr"], labels(train), groups=train.unit):
        assert not set(train.unit.iloc[tr]) & set(train.unit.iloc[va])
        assert len(set(train.unit.iloc[va])) == 20


def test_matrice_de_confusion_somme_et_positifs(results, sprint2):
    n_crit = int(labels(sprint2["test"]).sum())
    for m in results["health"]["classifiers"].values():
        cm = m["test"]["cm"]
        assert sum(cm.values()) == 13096
        assert cm["tp"] + cm["fn"] == n_crit


# ------------------------------------------------------------- métriques
def test_metrics_cas_calcule_a_la_main():
    m = _metrics(np.array([0, 0, 1, 1]), np.array([0.1, 0.6, 0.4, 0.9]))
    assert m["cm"] == {"tn": 1, "fp": 1, "fn": 1, "tp": 1}
    assert (m["accuracy"], m["precision"], m["recall"], m["f1"]) == (0.5, 0.5, 0.5, 0.5)
    assert m["auc"] == 0.75
    assert m["roc"][0] == {"fpr": 0.0, "tpr": 0.0} and m["roc"][-1] == {"fpr": 1.0, "tpr": 1.0}


def test_metriques_recalculees_avec_sklearn(clf, p_test, sprint2, results):
    """Le modèle sauvegardé, appliqué au jeu de test, redonne les métriques du JSON."""
    y = labels(sprint2["test"]).values
    yhat = (p_test >= 0.5).astype(int)
    ref = results["health"]["classifiers"][results["health"]["best"]]["test"]
    assert round(roc_auc_score(y, p_test), 4) == ref["auc"]
    assert round(accuracy_score(y, yhat), 4) == ref["accuracy"]
    assert round(precision_score(y, yhat), 4) == ref["precision"]
    assert round(recall_score(y, yhat), 4) == ref["recall"]
    assert round(f1_score(y, yhat), 4) == ref["f1"]
    tn, fp, fn, tp = confusion_matrix(y, yhat).ravel()
    assert ref["cm"] == {"tn": tn, "fp": fp, "fn": fn, "tp": tp}
    assert _metrics(y, p_test) == ref


def test_modele_sauvegarde(clf, sprint2, results):
    assert results["health"]["best"] == "Gradient Boosting"
    assert clf["features"] == list(sprint2["Ftr"].columns)


def test_probabilites_exportees(p_test, sprint2, results):
    """p_crit au dernier cycle (rul.json) et série p (engines.json) = sortie du modèle sauvegardé."""
    test = sprint2["test"].assign(p=p_test)
    last = test.groupby("unit").p.last()
    for row in results["rul"]["table"]:
        assert row["p_crit"] == pytest.approx(last[row["unit"]], abs=5e-4)
        assert row["state"] == state_from_prob(np.array([last[row["unit"]]]))[0]
    e = results["engines"]["31"]["series"]
    np.testing.assert_allclose([s["p"] for s in e], test[test.unit == 31].p, atol=5e-4)


def test_non_regression_classifieurs(results):
    c = results["health"]["classifiers"]
    gb, svm = c["Gradient Boosting"]["test"], c["SVM (RBF)"]["test"]
    assert gb["auc"] == pytest.approx(0.991, abs=0.0005)
    assert gb["recall"] == pytest.approx(0.657, abs=0.0005)
    assert svm["auc"] == pytest.approx(0.974, abs=0.0005)
    assert results["health"]["fleet_states"] == {"Normal": 76, "Critique": 20, "Surveillance": 4}


# ------------------------------------------------------------- état
def test_etat_a_partir_de_la_probabilite():
    s = state_from_prob(np.array([0.0, 0.19, 0.2, 0.49, 0.5, 1.0]))
    assert list(s) == ["Normal", "Normal", "Surveillance", "Surveillance", "Critique", "Critique"]


# ------------------------------------------------------------- apprentissage
def test_modeles_candidats():
    assert set(make_models()) == {"Gradient Boosting", "SVM (RBF)"}


def test_entrainement_sur_un_sous_ensemble(sprint2):
    tr, te = sprint2["train"], sprint2["test"]
    # sous-ensemble de test contenant les deux classes (sinon l'AUC n'est pas définie)
    last = te.groupby("unit").RUL.last()
    units_te = list(last[last <= 30].index[:5]) + list(last[last > 30].index[:5])
    mtr, mte = tr.unit <= 15, te.unit.isin(units_te)
    assert labels(te)[mte].nunique() == 2
    res, fitted, best = train_health_classifier(
        sprint2["Ftr"][mtr], labels(tr)[mtr], tr.unit[mtr], sprint2["Fte"][mte], labels(te)[mte])
    assert set(res) == set(fitted) == {"Gradient Boosting", "SVM (RBF)"}
    assert best in res
    for r in res.values():
        assert 0.5 < r["cv"]["auc"] <= 1 and 0 <= r["test"]["auc"] <= 1


@pytest.mark.slow
def test_reentrainement_complet_identique(sprint2, results):
    tr, te = sprint2["train"], sprint2["test"]
    res, _, best = train_health_classifier(sprint2["Ftr"], labels(tr), tr.unit, sprint2["Fte"], labels(te))
    assert best == results["health"]["best"]
    assert res == results["health"]["classifiers"]
