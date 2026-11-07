"""Génère tests/RAPPORT_TESTS.md à partir des sorties de pytest et de Playwright.

Entrées (produites par run_tests.bat / run_tests.sh) :
    tests/junit_pytest.xml, tests/junit_playwright.xml, tests/couverture.json
Usage : python tests/generer_rapport.py --mode rapide|complet
"""
import argparse
import json
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
OBJECTIF_COUVERTURE = 90.0


def lire_junit(path, outil):
    """Liste de dicts {fichier, nom, statut, duree, message} ; statut ∈ réussi, échec, erreur, ignoré, échec attendu."""
    if not path.exists():
        return None
    tests = []
    for tc in ET.parse(path).getroot().iter("testcase"):
        cls, nom = tc.get("classname", ""), tc.get("name", "")
        if outil == "pytest":
            fichier = cls.split(".")[1] + ".py" if cls.startswith("tests.") else cls
        else:
            fichier = "dashboard.spec.js"
            nom = f"{cls} › {nom}" if cls and cls not in nom else nom
        statut, message = "réussi", ""
        for enfant in tc:
            if enfant.tag == "failure":
                statut, message = "échec", enfant.get("message", "")
            elif enfant.tag == "error":
                statut, message = "erreur", enfant.get("message", "")
            elif enfant.tag == "skipped":
                xfail = "xfail" in (enfant.get("type") or "")
                statut, message = ("échec attendu" if xfail else "ignoré"), enfant.get("message", "")
            elif enfant.tag == "properties":
                for p in enfant.iter("property"):
                    if p.get("name") == "fail" and statut == "réussi":
                        statut, message = "échec attendu", p.get("value") or p.text or ""
        tests.append({"fichier": fichier, "nom": nom, "statut": statut,
                      "duree": float(tc.get("time") or 0), "message": " ".join(message.split())[:160]})
    return tests


def compter(tests):
    c = defaultdict(int)
    for t in tests:
        c[t["statut"]] += 1
    c["total"] = len(tests)
    c["duree"] = sum(t["duree"] for t in tests)
    return c


def versions():
    out = {"Python": platform.python_version(), "Système": f"{platform.system()} {platform.release()}"}
    for p in ("numpy", "pandas", "scikit-learn", "lifelines", "torch", "fastapi", "pytest"):
        try:
            out[p] = version(p)
        except PackageNotFoundError:
            out[p] = "absent"
    try:
        pw = json.loads((RACINE / "frontend" / "node_modules" / "@playwright" / "test" / "package.json")
                        .read_text(encoding="utf-8"))["version"]
        out["Playwright"] = pw
    except OSError:
        out["Playwright"] = "absent"
    return out


def commit():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=RACINE, capture_output=True,
                              text=True).stdout.strip() or "?"
    except OSError:
        return "?"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="rapide", choices=["rapide", "complet"])
    args = ap.parse_args()

    suites = {"pytest (backend)": lire_junit(ICI / "junit_pytest.xml", "pytest"),
              "Playwright (dashboard)": lire_junit(ICI / "junit_playwright.xml", "playwright")}
    L = ["# Rapport de tests", "",
         f"- **Date :** {datetime.now():%Y-%m-%d %H:%M}",
         f"- **Commit :** `{commit()}`",
         f"- **Mode :** {args.mode} "
         + ("(tests lents inclus : réentraînements, run_all.py complet)" if args.mode == "complet"
            else "(tests lents exclus ; lancer `run_tests --slow` pour la suite complète)"),
         "- **Généré par :** `tests/generer_rapport.py` (ne pas modifier à la main)", ""]

    # ------------------------------------------------------------ synthèse
    L += ["## Synthèse", "",
          "| Suite | Tests | Réussis | Échecs | Erreurs | Échecs attendus | Ignorés | Durée |",
          "|---|---|---|---|---|---|---|---|"]
    tous = []
    for nom, tests in suites.items():
        if tests is None:
            L.append(f"| {nom} | non exécutée | | | | | | |")
            continue
        tous += tests
        c = compter(tests)
        L.append(f"| {nom} | {c['total']} | {c['réussi']} | {c['échec']} | {c['erreur']} | "
                 f"{c['échec attendu']} | {c['ignoré']} | {c['duree']:.0f} s |")
    c = compter(tous)
    verdict = "✅ **Tout est vert**" if c["échec"] + c["erreur"] == 0 and None not in suites.values() \
        else "❌ **Des tests échouent ou n'ont pas été exécutés**"
    L += [f"| **Total** | **{c['total']}** | **{c['réussi']}** | **{c['échec']}** | **{c['erreur']}** | "
          f"**{c['échec attendu']}** | **{c['ignoré']}** | **{c['duree']:.0f} s** |", "", verdict, "",
          "« Échec attendu » : test d'un défaut connu, qui échoue comme prévu tant que le défaut n'est pas "
          "corrigé (xfail strict pour pytest, `test.fail()` pour Playwright). Si le défaut est corrigé "
          "sans retirer le marqueur, le test devient rouge.", ""]

    # ------------------------------------------------------------ par fichier
    L += ["## Détail par fichier", "", "| Fichier | Tests | Réussis | Échecs | Échecs attendus | Ignorés | Durée |",
          "|---|---|---|---|---|---|---|"]
    par_fichier = defaultdict(list)
    for t in tous:
        par_fichier[t["fichier"]].append(t)
    for f in sorted(par_fichier):
        c = compter(par_fichier[f])
        L.append(f"| `{f}` | {c['total']} | {c['réussi']} | {c['échec'] + c['erreur']} | {c['échec attendu']} | "
                 f"{c['ignoré']} | {c['duree']:.1f} s |")
    L.append("")

    # ------------------------------------------------------------ couverture
    cov_path = ICI / "couverture.json"
    L += ["## Couverture du code Python", ""]
    if cov_path.exists():
        cov = json.loads(cov_path.read_text(encoding="utf-8"))
        L += [f"Objectif : **≥ {OBJECTIF_COUVERTURE:.0f} %** sur `backend/pipeline/` et `backend/api/`.", "",
              "| Fichier | Instructions | Non couvertes | Couverture |", "|---|---|---|---|"]
        for f, d in sorted(cov["files"].items()):
            s = d["summary"]
            L.append(f"| `{Path(f).as_posix()}` | {s['num_statements']} | {s['missing_lines']} | "
                     f"{s['percent_covered']:.0f} % |")
        tot = cov["totals"]["percent_covered"]
        ok = "atteint ✅" if tot >= OBJECTIF_COUVERTURE else "non atteint ❌"
        L += [f"| **Total** | **{cov['totals']['num_statements']}** | **{cov['totals']['missing_lines']}** | "
              f"**{tot:.1f} %** |", "", f"Objectif {ok}.", ""]
    else:
        L += ["Pas de mesure de couverture (`tests/couverture.json` absent).", ""]

    # ------------------------------------------------------------ anomalies
    for titre, statuts in (("Échecs et erreurs", ("échec", "erreur")), ("Échecs attendus (défauts connus)",
                           ("échec attendu",)), ("Tests ignorés", ("ignoré",))):
        lst = [t for t in tous if t["statut"] in statuts]
        L += [f"## {titre}", ""]
        if not lst:
            L += ["Aucun.", ""]
            continue
        vus = set()
        for t in lst:
            cle = (t["fichier"], t["message"]) if t["statut"] != "échec" else (t["fichier"], t["nom"])
            if t["statut"] == "échec attendu" and cle in vus:
                continue
            vus.add(cle)
            n = sum(1 for u in lst if (u["fichier"], u["message"]) == cle) if t["statut"] == "échec attendu" else 1
            fois = f" (×{n})" if n > 1 else ""
            L.append(f"- `{t['fichier']}` — {t['nom'] if n == 1 else 'plusieurs tests'}{fois} : {t['message'] or '—'}")
        L.append("")

    # ------------------------------------------------------------ environnement
    L += ["## Environnement", "", "| Élément | Version |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in versions().items()]
    L += ["", "## Relancer", "", "```bash", "run_tests.bat            # Windows (tests rapides + dashboard)",
          "run_tests.bat --slow     # suite complète (~10 min)", "./run_tests.sh [--slow]  # Linux / macOS / Git Bash",
          "```", ""]

    (ICI / "RAPPORT_TESTS.md").write_text("\n".join(L), encoding="utf-8")
    print(f"-> tests/RAPPORT_TESTS.md ({c['total'] if tous else 0} tests)")


if __name__ == "__main__":
    sys.exit(main())
