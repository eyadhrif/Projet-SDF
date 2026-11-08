"""Structure du rapport sur le modèle de référence (rapport Sentinel) et version LaTeX / Overleaf.

- pages liminaires, introduction générale avec la problématique encadrée, chapitres numérotés ouverts par
  une Introduction et fermés par une Conclusion, conclusion générale, bibliographie, glossaire, résumés
  en trois langues (mêmes chiffres, générés)
- bibliographie structurée et mise au style IEEE (demande de l'encadrant)
- projet LaTeX généré : cohérent (renvois, citations, fichiers inclus) et compilable (XeLaTeX et pdfLaTeX)
"""
import json
import re
import shutil
import subprocess

import pytest

from test_report import REPORT, SOURCE, NODE, avec_node, verifier_pdf_binaire

CHAPITRES = ["04_cadre_donnees.md", "05_methodologie.md", "06_evaluation_visualisation.md",
             "07_discussion_perspectives.md"]
LATEX = REPORT / "latex"


# ------------------------------------------------------------- structure du modèle
def test_ordre_des_parties():
    noms = [p.name for p in sorted(SOURCE.glob("*.md"))]
    assert noms[:4] == ["00_titre.md", "01_front.md", "02_listes.md", "03_introduction_generale.md"]
    assert noms[4:8] == CHAPITRES
    assert noms[8:] == ["08_conclusion_generale.md", "09_bibliographie.md", "10_annexes.md", "11_resumes.md"]
    front = (SOURCE / "01_front.md").read_text(encoding="utf-8")
    assert "# Dédicaces {-}" in front and "# Remerciements {-}" in front and ":::dedicace" in front
    # remarque de relecture : introduction homogène, sans encadré gris
    assert ":::encadre" not in (SOURCE / "03_introduction_generale.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("nom", CHAPITRES)
def test_chaque_chapitre_a_introduction_et_conclusion(nom):
    md = (SOURCE / nom).read_text(encoding="utf-8")
    h1 = [l for l in md.splitlines() if l.startswith("# ")]
    assert len(h1) == 1 and "{#sec:" in h1[0]
    h2 = [l for l in md.splitlines() if l.startswith("## ")]
    assert h2[0] == "## Introduction {-}" and h2[-1] == "## Conclusion {-}"
    intro = md.split("## Introduction {-}")[1].split("\n## ")[0].strip()
    assert intro.startswith("Ce chapitre")
    assert intro.count("Ce chapitre") == 1, "introduction redondante"


def test_resumes_trilingues_et_glossaire():
    md = (SOURCE / "11_resumes.md").read_text(encoding="utf-8")
    assert "## Résumé {-}" in md and "## Abstract {-}" in md and "## ملخص {-}" in md and ":::arabe" in md
    for cle in ("n_moteurs_test", "mttf", "dispo", "t_opt_arrondi", "gain_preventif", "n_retenus", "gb_auc",
                "deg_rmse", "lstm_rmse"):
        assert md.count("{{" + cle + "}}") == 3, f"{cle} : mêmes chiffres dans les trois langues"
    glo = (SOURCE / "02_listes.md").read_text(encoding="utf-8")   # liste des abréviations
    assert len(re.findall(r"^\*\*[^*]+\*\* :", glo, flags=re.M)) >= 20


def test_page_de_garde_et_logos():
    m = json.loads((REPORT / "metadonnees.json").read_text(encoding="utf-8"))
    assert m["auteurs"] == ["Salma Moueddeb", "Eya Dhrif"] and "Ben Hmida" in m["encadrant"]
    for logo in ("logo_univ_tunis.png", "logo_emblem.png", "logo_ensit.png"):
        assert (REPORT / "logos" / logo).stat().st_size > 1000


# ------------------------------------------------------------- bibliographie IEEE
REQUIS = {"article": {"journal"}, "inproceedings": {"booktitle"}, "book": {"publisher", "address"},
          "incollection": {"booktitle", "publisher"}, "techreport": {"institution"}, "misc": {"howpublished"},
          "standard": {"number"}}


def test_bibliographie_structuree():
    for e in json.loads((REPORT / "bibliographie.json").read_text(encoding="utf-8")):
        assert e["type"] in REQUIS, e["cle"]
        assert {"author", "title", "year"} <= set(e) and REQUIS[e["type"]] <= set(e), e["cle"]


@avec_node
def test_format_ieee():
    code = ("import('./ieee.mjs').then(({ieee}) => console.log(JSON.stringify(["
            "ieee({type:'article',author:['A. B','C. D','E. F'],title:'T',journal:'J',volume:'5',number:'2',pages:'1–9',year:2020}),"
            "ieee({type:'inproceedings',author:['A. B','et al.'],title:'T',booktitle:'Conf',year:2019}),"
            "ieee({type:'book',author:['A. B','C. D'],title:'L',address:'New York',publisher:'W',year:1965})])))")
    p = subprocess.run([NODE, "-e", code], cwd=REPORT, capture_output=True, text=True, encoding="utf-8")
    a, b, c = json.loads(p.stdout)
    assert a == "A. B, C. D, and E. F, “T,” *J*, vol. 5, no. 2, pp. 1–9, 2020."
    assert b == "A. B et al., “T,” in *Conf*, 2019."
    assert c == "A. B and C. D, *L*. New York: W, 1965."


# ------------------------------------------------------------- version LaTeX / Overleaf
@avec_node
def test_generation_latex_coherente():
    p = subprocess.run([NODE, "build.mjs", "--latex"], cwd=REPORT, capture_output=True, text=True,
                       encoding="utf-8", timeout=600)
    assert p.returncode == 0, p.stdout + p.stderr
    main = (LATEX / "main.tex").read_text(encoding="utf-8")
    tex = main + "".join(f.read_text(encoding="utf-8") for f in sorted((LATEX / "chapters").glob("*.tex")))
    for inc in re.findall(r"\\input\{(chapters/\w+)\}", main):
        assert (LATEX / f"{inc}.tex").exists(), inc
    labels = set(re.findall(r"\\label\{([^}]+)\}", tex))
    refs = set(re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", tex)) | set(re.findall(r"\\hyperref\[([^\]]+)\]", tex))
    assert refs and refs <= labels, refs - labels
    bibitems = set(re.findall(r"\\bibitem\{([^}]+)\}", tex))
    cites = {c for g in re.findall(r"\\cite\{([^}]+)\}", tex) for c in g.split(",")}
    nb = len(json.loads((REPORT / "bibliographie.json").read_text(encoding="utf-8")))
    assert cites == bibitems and len(bibitems) == nb
    for img in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex):
        assert (LATEX / img).exists(), img
    md = "".join(p.read_text(encoding="utf-8") for p in SOURCE.glob("*.md"))
    assert len(re.findall(r"\\begin\{figure\}", tex)) == len(re.findall(r"^!figure\[", md, flags=re.M))
    assert len(re.findall(r"\\begin\{table\}", tex)) == len(re.findall(r"^!tableau\[", md, flags=re.M))
    for env in ("figure", "table", "equation", "itemize", "enumerate", "center", "titlepage", "multicols",
                "problembox", "thebibliography"):
        assert tex.count(f"\\begin{{{env}}}") == tex.count(f"\\end{{{env}}}"), env
    # aucun marqueur non résolu (« {{ » seul est légitime en LaTeX, par exemple dans la macro \code du modèle)
    assert not re.search(r"@@|\{\{\s*\w+\s*\}\}|\[cite:|\[@|\*\*", tex)
    assert "$pdf_mode = 5" in (LATEX / ".latexmkrc").read_text(encoding="utf-8")
    verifier_pdf_binaire((LATEX / "figures" / "resume_arabe.pdf").read_bytes())


def _wsl_latex():
    wsl = shutil.which("wsl.exe") or shutil.which("wsl")
    if not wsl:
        return None
    p = subprocess.run([wsl, "-d", "Ubuntu", "--", "bash", "-lc", "command -v latexmk"], capture_output=True)
    return wsl if p.returncode == 0 else None


@pytest.mark.slow
@avec_node
@pytest.mark.parametrize("moteur, option", [("xelatex", "-xelatex"), ("pdflatex", "-pdf")])
def test_compilation_latex(moteur, option):
    """Compilation réelle (TeX Live dans WSL) : sans erreur, sans renvoi ni citation indéfinis, sans glyphe manquant."""
    wsl = _wsl_latex()
    if wsl is None:
        pytest.skip("TeX Live (latexmk) indisponible dans WSL")
    src = subprocess.run([wsl, "-d", "Ubuntu", "--", "wslpath", "-u", str(LATEX).replace("\\", "/")],
                         capture_output=True, text=True).stdout.strip()
    # script passé par l'entrée standard : wsl.exe réinterprète sa ligne de commande (les « $ » y seraient développés)
    script = (f"rm -rf /tmp/t_{moteur} && cp -r '{src}' /tmp/t_{moteur} && cd /tmp/t_{moteur} && "
              f"latexmk {option} -interaction=nonstopmode -halt-on-error main.tex > /dev/null 2>&1; "
              "echo CODE=$?; grep -c '^!' main.log; grep -c 'undefined' main.log; "
              "grep -c 'Missing character' main.log; ls main.pdf\n")
    # octets bruts : en mode texte, Windows ajouterait des « \r » que bash lirait comme des caractères
    p = subprocess.run([wsl, "-d", "Ubuntu", "--", "bash", "-s"], input=script.encode("utf-8"), capture_output=True,
                       timeout=1200)
    sortie = p.stdout.decode("utf-8", "replace")
    lignes = sortie.split()
    assert lignes and lignes[0] == "CODE=0", f"sortie : {sortie!r} ; erreurs : {p.stderr.decode('utf-8', 'replace')!r}"
    assert lignes[1:4] == ["0", "0", "0"], f"erreurs / indéfinis / glyphes manquants : {lignes[1:4]}"
    assert lignes[4] == "main.pdf"
