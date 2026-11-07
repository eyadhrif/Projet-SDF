"""A3 — Figures du rapport (backend/report_figures.py) : complètes, au bon format, à jour avec les JSON."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np                # noqa: E402
import pytest                     # noqa: E402
from PIL import Image             # noqa: E402

import report_figures as rf       # noqa: E402
from conftest import ROOT         # noqa: E402

FIGS = ROOT / "report" / "figures"
NOMS = [n for n, _ in rf.FIGURES]


def test_liste_des_figures():
    assert len(NOMS) == len(set(NOMS)) == 21


@pytest.mark.parametrize("nom", NOMS)
def test_figure_png_300_dpi_et_pdf(nom):
    png, pdf = FIGS / f"{nom}.png", FIGS / f"{nom}.pdf"
    assert png.stat().st_size > 10_000 and pdf.stat().st_size > 5_000
    with Image.open(png) as im:
        assert im.info["dpi"] == pytest.approx((300, 300), abs=1)
        # ≥ 5 cm imprimés à 300 dpi ; les demi-largeurs (8 cm prévus) font 766 à 890 px après le
        # recadrage serré (bbox_inches="tight"), qui retire les marges blanches
        assert im.width >= 600
    assert pdf.read_bytes()[:5] == b"%PDF-"


def test_aucune_figure_orpheline():
    fichiers = {p.stem for p in FIGS.glob("*.png")} | {p.stem for p in FIGS.glob("*.pdf")}
    assert fichiers == set(NOMS)


def test_figures_a_jour(tmp_path, monkeypatch):
    """Régénérées depuis results/*.json, les figures sont identiques (au pixel près) à celles du dépôt."""
    monkeypatch.setattr(rf, "OUT", tmp_path)
    rf.main()
    for nom in NOMS:
        a, b = plt.imread(tmp_path / f"{nom}.png"), plt.imread(FIGS / f"{nom}.png")
        assert a.shape == b.shape, f"{nom} : taille différente, relancer python report_figures.py"
        assert np.abs(a - b).mean() < 1e-3, f"{nom} n'est pas à jour : relancer python report_figures.py"


def test_format_decimal_francais():
    assert rf._virgule(0.25, 0) == "0,25" and rf._virgule(-1.5, 0) == "−1,5"
    assert rf.fr(13.52, 1) == "13,5"
