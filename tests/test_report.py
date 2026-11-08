"""Tests du rapport scientifique (§0.9) : report/source/*.md construit par report/build.mjs.

- aucun chiffre tapé à la main : tout nombre du texte vient de report/generated/valeurs.json ({{cle}}),
  hors formules mathématiques, code et identifiants techniques (FD001, s11, B10, tickets…)
- chaque figure et chaque tableau générés sont inclus et cités ; chaque renvoi et chaque citation existent
  (contrôlés par build.mjs, qui échoue sinon) ; chaque référence de la bibliographie est citée
- le document se construit sans erreur, jusqu'au PDF
- chapitre Perspectives : aucune perspective formulée au passé ni présentée comme un résultat
"""
import json
import re
import shutil
import subprocess

import pytest

from conftest import ROOT

REPORT = ROOT / "report"
SOURCE = REPORT / "source"
NODE = shutil.which("node")
avec_node = pytest.mark.skipif(NODE is None or not (REPORT / "node_modules").exists(),
                               reason="Node et npm install dans report/ requis")

# identifiants techniques qui contiennent des chiffres sans être des résultats
IDENTIFIANTS = [
    r"FD00\d", r"\bs\d{1,2}\b", r"\bset\d\b", r"\b[BP]\d{1,2}\b", r"\bt90\b", r"\b[23]P\b",
    r"\b(?:SET|FMDS|PDM|RUL|WEB)-0\d\b", r"\bVersions? [123](?: et [123])?\b", r"\bGMAM 3\b", r"\bNF EN 13306\b",
    r"(?m)^\s*\d+\.\s",                       # numéros de liste ordonnée (mise en forme)
    r"\(\*\*\d\*\*\)",                        # numéros d'objectifs « (**1**) » (mise en forme)
    r"niveaux nominaux de 50, 80 et 90",      # niveaux nominaux choisis (entrées de la calibration, pas des résultats)
]


def _sources():
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(SOURCE.glob("*.md"))}


def texte_sans_valeurs(md):
    """Texte où ne restent que les mots écrits à la main (valeurs, maths, code, renvois et balises retirés)."""
    md = re.sub(r"<!--.*?-->", " ", md, flags=re.S)
    md = re.sub(r"```.*?```", " ", md, flags=re.S)
    md = re.sub(r"`[^`]*`", " ", md)
    md = re.sub(r"\{\{\s*\w+\s*\}\}", " ", md)
    md = re.sub(r"\$\$.*?\$\$(?:\s*\{#eq:[\w-]+\})?", " ", md, flags=re.S)
    md = re.sub(r"\$[^$\n]+?\$", " ", md)
    md = re.sub(r"\[@[\w:-]+\]|\[cite:[\w,\s-]+\]", " ", md)
    md = re.sub(r"^!(figure|tableau)\[[\w-]+\]\(?", " ", md, flags=re.M)
    md = re.sub(r"\)?\{largeur=\d+\}", " ", md)
    md = re.sub(r"\{#sec:[\w-]+\}|\{-\}", " ", md)
    md = re.sub(r"<[^>]+>", " ", md)
    for motif in IDENTIFIANTS:
        md = re.sub(motif, " ", md)
    return md


def test_sources_presentes():
    assert len(_sources()) >= 12


def test_aucun_chiffre_tape_a_la_main():
    fautes = []
    for nom, md in _sources().items():
        for ligne in texte_sans_valeurs(md).splitlines():
            for m in re.finditer(r"\d", ligne):
                fautes.append(f"{nom} : « …{ligne[max(0, m.start() - 40):m.end() + 20].strip()}… »")
    assert not fautes, "chiffres écrits à la main (utiliser {{cle}}) :\n" + "\n".join(fautes[:20])


def test_le_filtre_detecte_un_chiffre():
    """Contrôle du test lui-même : un chiffre écrit à la main est bien détecté, les valeurs non."""
    assert re.search(r"\d", texte_sans_valeurs("Le MTTF vaut 206,3 cycles."))
    assert not re.search(r"\d", texte_sans_valeurs("Le MTTF vaut {{mttf}} cycles ($\\beta > 1$) sur FD001, capteur s11."))


def test_toutes_les_valeurs_citees_existent():
    v = json.loads((REPORT / "generated" / "valeurs.json").read_text(encoding="utf-8"))
    cles = set(re.findall(r"\{\{\s*(\w+)\s*\}\}", "".join(_sources().values())))
    assert cles and cles <= set(v), cles - set(v)


def test_chaque_figure_et_chaque_tableau_sont_inclus():
    """Version courte (4 chapitres) : le rapport retient une sélection des figures et tableaux générés.

    Chaque figure ou tableau inclus doit exister (généré par le code ou capture du tableau de bord)
    et être cité dans le texte.
    """
    import report_figures
    import report_tables  # noqa: F401
    md = "".join(_sources().values())
    figs = set(re.findall(r"^!figure\[([\w-]+)\]", md, flags=re.M))
    tabs = set(re.findall(r"^!tableau\[([\w-]+)\]", md, flags=re.M))
    captures = {f"dashboard_{p}" for p in ("overview", "fiab", "mon", "rul")}
    assert figs and figs <= {n for n, _ in report_figures.FIGURES} | captures, figs
    assert tabs and tabs <= {p.stem for p in (REPORT / "tables").glob("*.md")}, tabs
    assert figs & captures, "au moins une capture du tableau de bord"
    for nom in figs:
        assert f"[@fig:{nom}]" in md, f"figure {nom} jamais citée"
    for nom in tabs:
        assert f"[@tab:{nom}]" in md, f"tableau {nom} jamais cité"


def test_bibliographie():
    bib = json.loads((REPORT / "bibliographie.json").read_text(encoding="utf-8"))
    cles = [e["cle"] for e in bib]
    assert len(cles) == len(set(cles)) >= 30
    cites = {c.strip() for l in re.findall(r"\[cite:([\w,\s-]+)\]", "".join(_sources().values())) for c in l.split(",")}
    assert cites == set(cles), {"non citées": set(cles) - cites, "inconnues": cites - set(cles)}


PASSE = [r"\bnous avons\b", r"\b(?:a|ont|avait|avaient) été\b", r"\b(?:a|ont) (?:permis|montré|démontré|réalisé|"
         r"implémenté|développé|obtenu|amélioré|réduit|validé|intégré|corrigé)\b", r"\bavons\b", r"\bTODO\b"]


def test_perspectives_jamais_au_passe():
    """Section « Travaux futurs » du chapitre Discussion et perspectives (version courte)."""
    md = (SOURCE / "07_discussion_perspectives.md").read_text(encoding="utf-8")
    futurs = md.split("## Travaux futurs")[1].split("\n## ")[0]
    assert "aucun n'est réalisé à ce stade" in futurs
    fautes = [m.group(0) for p in PASSE for m in re.finditer(p, futurs, flags=re.I)]
    assert not fautes, fautes
    # chaque travail futur : un titre en gras puis sa description
    assert len(re.findall(r"^- \*\*[^*]+\.\*\* \S", futurs, flags=re.M)) >= 5


def test_hypotheses_signalees():
    md = "".join(_sources().values())
    assert "**simulés**" in md and "Hypothèses simulées" in md
    assert "{{h_par_cycle}} h" in md                  # conversion cycle -> heures explicitement citée


def test_aucune_marque_de_brouillon():
    md = "".join(_sources().values())
    assert not re.search(r"TODO|XXX|\?\?\?|à compléter", md, flags=re.I)


@avec_node
def test_construction_verification():
    p = subprocess.run([NODE, "build.mjs", "--check"], cwd=REPORT, capture_output=True, text=True,
                       encoding="utf-8", timeout=600)
    assert p.returncode == 0, p.stdout + p.stderr
    v = json.loads((REPORT / "build" / "verification.json").read_text(encoding="utf-8"))
    assert v["erreurs"] == []
    md = "".join(_sources().values())
    assert v["figures"] == len(re.findall(r"^!figure\[", md, flags=re.M))
    assert v["tableaux"] == len(re.findall(r"^!tableau\[", md, flags=re.M))
    assert v["references"] >= 30 and v["equations"] >= 10


@avec_node
@pytest.mark.slow
def test_construction_du_pdf(tmp_path):
    pdf = tmp_path / "rapport.pdf"                       # le PDF livré n'est pas réécrit
    p = subprocess.run([NODE, "build.mjs", f"--sortie={pdf}"], cwd=REPORT, capture_output=True, text=True,
                       encoding="utf-8", timeout=900)
    assert p.returncode == 0, p.stdout + p.stderr
    verifier_pdf_binaire(pdf.read_bytes())
    v = json.loads((REPORT / "build" / "verification.json").read_text(encoding="utf-8"))
    assert v["pages"] >= 25


def verifier_pdf_binaire(data):
    """PDF binaire intact : en-tête, fin de fichier, et aucune trace de réécriture en texte.

    Un PDF lu comme du texte puis réécrit en UTF-8 voit ses octets ≥ 0x80 remplacés par U+FFFD
    (EF BF BD) : sa taille double et ses flux compressés deviennent illisibles (constaté sur le
    tag v1.0.1-rapport).
    """
    assert data[:5] == b"%PDF-", "en-tête PDF absent"
    assert b"%%EOF" in data[-1024:], "fin de fichier PDF absente"
    fffd = "�".encode("utf-8")                      # EF BF BD
    debut = data.index(b"\n%") + 2                      # commentaire binaire après « %PDF-1.x »
    assert data[debut] >= 0x80 and data[debut:debut + 3] != fffd, "commentaire binaire de l'en-tête altéré"
    assert data.count(fffd) < 100, "octets remplacés par U+FFFD : PDF réécrit comme du texte"


def test_pdf_livre_present_et_intact():
    data = (REPORT / "Rapport_FMDS_Eya_DHRIF_Salma_MOUEDDEB.pdf").read_bytes()
    assert len(data) > 1_000_000
    verifier_pdf_binaire(data)


def test_verification_pdf_detecte_une_reecriture_en_texte():
    """Contrôle du test : un PDF décodé en texte puis réécrit en UTF-8 est bien rejeté."""
    sain = (REPORT / "Rapport_FMDS_Eya_DHRIF_Salma_MOUEDDEB.pdf").read_bytes()
    abime = sain.decode("utf-8", errors="replace").encode("utf-8")
    with pytest.raises(AssertionError):
        verifier_pdf_binaire(abime)
