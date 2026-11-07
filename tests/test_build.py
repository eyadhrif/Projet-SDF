"""WEB-02 — Les deux builds du front réussissent et les fichiers livrés sont à jour (§0.8, §0.11-4).

Les builds sont faits dans un dossier temporaire (--outDir) : frontend/dist n'est pas modifié.
"""
import filecmp
import shutil
import subprocess

import pytest

from conftest import ROOT

FRONT = ROOT / "frontend"
NPX = shutil.which("npx")

pytestmark = pytest.mark.skipif(NPX is None or not (FRONT / "node_modules").exists(),
                                reason="Node / npm install requis pour tester les builds")


def _build(out, *mode):
    p = subprocess.run([NPX, "vite", "build", *mode, "--outDir", str(out), "--emptyOutDir"], cwd=FRONT,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    assert p.returncode == 0, p.stdout[-1500:] + p.stderr[-1500:]
    return out


def test_build_normal_identique_a_dist(tmp_path):
    out = _build(tmp_path / "dist")
    cmp = filecmp.dircmp(out, FRONT / "dist")
    fichiers = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
    attendus = sorted(p.relative_to(FRONT / "dist").as_posix() for p in (FRONT / "dist").rglob("*") if p.is_file())
    assert fichiers == attendus, "frontend/dist n'est pas à jour : relancer npm run build"
    for f in fichiers:
        assert filecmp.cmp(out / f, FRONT / "dist" / f, shallow=False), f"{f} diffère de frontend/dist"
    assert not cmp.diff_files


def test_build_autonome_identique_au_livrable(tmp_path):
    out = _build(tmp_path / "static", "--mode", "static")
    html = out / "index.html"
    assert html.stat().st_size > 1_000_000                       # résultats JSON intégrés
    assert filecmp.cmp(html, ROOT / "dashboard_autonome.html", shallow=False), \
        "dashboard_autonome.html n'est pas à jour : npm run build:static puis copier dist-static/index.html"
