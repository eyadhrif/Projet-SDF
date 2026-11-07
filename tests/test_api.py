"""WEB-01 — Tests de l'API FastAPI (backend/api/main.py)."""
import pytest

from conftest import ROOT


# ------------------------------------------------------------- endpoints
@pytest.mark.parametrize("path, name", [
    ("/api/fmds", "fmds"), ("/api/health", "health"), ("/api/rul", "rul"),
])
def test_endpoint_identique_au_json(client, results, path, name):
    r = client.get(path)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/json")
    assert r.json() == results[name]


def test_schema_fmds(client):
    d = client.get("/api/fmds").json()
    assert set(d) >= {"assumptions", "fiabilite", "maintenabilite", "disponibilite", "preventif", "dataset"}
    fi = d["fiabilite"]
    for k in ("mttf", "b1", "b10", "median_km"):
        assert isinstance(fi[k], (int, float))
    assert set(fi["w3"]) >= {"beta", "eta", "gamma", "ks_p"}
    assert len(d["dataset"]["lifetimes"]) == 200


def test_schema_health(client):
    d = client.get("/api/health").json()
    assert len(d["selected"]) == 12 and len(d["dropped"]) == 7
    assert d["best"] in d["classifiers"]
    for m in d["classifiers"].values():
        assert set(m) == {"cv", "test"}
        assert set(m["test"]) >= {"auc", "precision", "recall", "f1", "cm", "roc"}


def test_schema_rul(client):
    d = client.get("/api/rul").json()
    assert set(d["metrics"]) == {"deg", "lstm", "ensemble"}
    for m in d["metrics"].values():
        assert set(m) >= {"rmse", "mae", "bias", "score"}
    assert len(d["table"]) == 100


def test_fleet(client, results):
    r = client.get("/api/fleet")
    assert r.status_code == 200
    rows = r.json()
    assert rows == results["rul"]["table"]
    assert sorted(x["unit"] for x in rows) == list(range(1, 101))
    for x in rows:
        assert set(x) >= {"unit", "cycles", "true", "deg", "deg_p10", "deg_p90", "lstm", "state"}


@pytest.mark.parametrize("unit", [1, 31, 100])
def test_engine_valide(client, results, unit):
    r = client.get(f"/api/engines/{unit}")
    assert r.status_code == 200
    e = r.json()
    assert e == results["engines"][str(unit)]
    assert e["unit"] == unit
    assert len(e["series"]) == e["last_cycle"]


@pytest.mark.parametrize("unit", [0, 101, -1])
def test_engine_inconnu_404(client, unit):
    r = client.get(f"/api/engines/{unit}")
    assert r.status_code == 404
    assert "inconnu" in r.json()["detail"]


def test_engine_non_numerique_422(client):
    assert client.get("/api/engines/abc").status_code == 422


def test_resultats_absents_503(client, monkeypatch, tmp_path):
    from api import main
    monkeypatch.setattr(main, "RES", tmp_path)        # dossier vide
    main._cache.clear()
    r = client.get("/api/rul")
    assert r.status_code == 503
    assert "run_all.py" in r.json()["detail"]


# ------------------------------------------------------------- front
def test_racine_sert_le_dashboard(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert '<div id="root">' in r.text


def test_route_front_inconnue_sert_index(client):
    """Routage côté client (SPA) : une URL de page inconnue renvoie index.html."""
    r = client.get("/une-page-quelconque")
    assert r.status_code == 200 and '<div id="root">' in r.text


def test_asset_compile_servi(client):
    js = next((ROOT / "frontend" / "dist" / "assets").glob("*.js")).name
    r = client.get(f"/assets/{js}")
    assert r.status_code == 200 and "javascript" in r.headers["content-type"]


def test_docs_swagger(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").json()["info"]["title"].startswith("FMDS")


# ------------------------------------------------------------- défauts D1 / D2
@pytest.mark.parametrize("path", ["/api/inexistant", "/api/", "/api/engines"])
def test_route_api_inconnue_404(client, path):
    """D2 : une route /api/… inconnue doit répondre 404 en JSON, pas le HTML du dashboard."""
    r = client.get(path)
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/json")


@pytest.mark.parametrize("path", [
    "/%2e%2e/%2e%2e/backend/requirements.txt",
    "/..%2F..%2Fbackend%2Fresults%2Frul.json",
    "/%2e%2e%2f%2e%2e%2fCLAUDE.md",
])
def test_pas_de_lecture_hors_dist(client, path):
    """D1 : aucune remontée d'arborescence (../) ne doit donner accès à un fichier hors de frontend/dist."""
    r = client.get(path)
    assert r.status_code == 404
    assert "Dashboard uniquement" not in r.text and "metrics" not in r.text and "Handoff" not in r.text
