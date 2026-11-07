"""Fixtures partagées par toute la suite de tests (Phase 0)."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
RESULTS = BACKEND / "results"
MODELS = BACKEND / "models"


def load_json(name: str):
    return json.loads((RESULTS / f"{name}.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def fd001():
    """(train, test, rul_test) chargés une seule fois pour toute la session."""
    from pipeline.data import load_fd001
    return load_fd001()


@pytest.fixture(scope="session")
def results():
    """Contenu des 4 fichiers JSON commités dans backend/results/."""
    return {n: load_json(n) for n in ("fmds", "health", "rul", "engines")}


@pytest.fixture(scope="session")
def sprint2(fd001):
    """Chaîne du sprint 2 refaite comme dans run_all.py : capteurs, HI, features fenêtrées.

    Travaille sur des copies : les DataFrames de la fixture fd001 ne sont pas modifiés.
    """
    from pipeline.features import sensor_ranking, window_features, HealthIndicator
    train, test = fd001[0].copy(), fd001[1].copy()
    rank, selected, dropped = sensor_ranking(train)
    hi = HealthIndicator(selected).fit(train)
    for df in (train, test):
        df["HI_raw"] = hi.raw(df)
        df["HI"] = hi.transform(df)
    Ftr, Fte = window_features(train, selected), window_features(test, selected)
    for F, df in ((Ftr, train), (Fte, test)):
        F["HI"] = df["HI"]
        F["cycle"] = df["cycle"]
    return {"train": train, "test": test, "rank": rank, "selected": selected, "dropped": dropped,
            "hi": hi, "Ftr": Ftr, "Fte": Fte}


@pytest.fixture()
def client():
    """Client HTTP de test FastAPI, avec un cache vide à chaque test."""
    from fastapi.testclient import TestClient
    from api import main
    main._cache.clear()
    with TestClient(main.app) as c:
        yield c
    main._cache.clear()
