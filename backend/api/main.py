"""WEB-01 — API FastAPI (Eya) : sert les résultats des sprints 1 à 3 + le front React compilé.

    uvicorn api.main:app --reload --port 8000
"""
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
DIST = ROOT.parent / "frontend" / "dist"

app = FastAPI(title="FMDS & Maintenance Prédictive — C-MAPSS FD001", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

_cache: dict = {}


def load(name: str):
    if name not in _cache:
        path = RES / f"{name}.json"
        if not path.exists():
            raise HTTPException(503, f"{path.name} absent : lancez d'abord `python run_all.py`")
        _cache[name] = json.loads(path.read_text(encoding="utf-8"))
    return _cache[name]


@app.get("/api/fmds", summary="Indices FMDS : fiabilité, maintenabilité, disponibilité, préventif")
def fmds():
    return load("fmds")


@app.get("/api/health", summary="Indicateur de santé et classification normal / critique")
def health():
    return load("health")


@app.get("/api/rul", summary="Comparaison des deux modèles de RUL sur le jeu de test")
def rul():
    return load("rul")


@app.get("/api/engines/{unit}", summary="Historique d'un moteur de test : HI, probabilité, RUL")
def engine(unit: int):
    eng = load("engines")
    if str(unit) not in eng:
        raise HTTPException(404, f"Moteur {unit} inconnu (1–100)")
    return eng[str(unit)]


@app.get("/api/fleet", summary="État actuel de la flotte de test (tableau de bord)")
def fleet():
    return load("rul")["table"]


# Front React compilé (npm run build) servi à la racine
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    DIST_ROOT = DIST.resolve()

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        # Une route /api/… inconnue est une erreur d'API (404 JSON), pas une page du dashboard
        if path == "api" or path.startswith("api/"):
            raise HTTPException(404, f"Route /{path} inconnue")
        f = (DIST_ROOT / path).resolve()
        # Refuser toute remontée d'arborescence (../) hors de frontend/dist
        if not f.is_relative_to(DIST_ROOT):
            raise HTTPException(404, "Fichier introuvable")
        return FileResponse(f if path and f.is_file() else DIST_ROOT / "index.html")
