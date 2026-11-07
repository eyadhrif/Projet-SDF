"""Tests du rapport scientifique (§0.9) — activés à partir de la phase B.

Prévu quand report/ existera :
- chaque nombre cité dans le rapport est extrait et confronté à sa source JSON
  (les chiffres sont générés depuis les JSON par des macros, pas tapés à la main)
- chaque figure et chaque tableau sont référencés ; aucune référence cassée ;
  toute citation existe dans la bibliographie
- le document compile sans erreur
- chapitre Perspectives : aucune perspective au passé ni présentée comme un résultat
"""
import pytest

from conftest import ROOT

REPORT = ROOT / "report"

pytestmark = pytest.mark.skipif(not REPORT.exists(), reason="rapport pas encore rédigé (phase B)")


def test_dossier_du_rapport():
    assert any(REPORT.iterdir())
