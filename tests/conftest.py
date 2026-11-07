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


@pytest.fixture()
def client():
    """Client HTTP de test FastAPI, avec un cache vide à chaque test."""
    from fastapi.testclient import TestClient
    from api import main
    main._cache.clear()
    with TestClient(main.app) as c:
        yield c
    main._cache.clear()
