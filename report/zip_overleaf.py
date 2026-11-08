"""Archive du projet LaTeX pour Overleaf (New Project -> Upload Project).

    node build.mjs --latex      # génère report/latex/
    python zip_overleaf.py      # -> report/Rapport_Overleaf.zip
"""
import zipfile
from pathlib import Path

ICI = Path(__file__).resolve().parent
SRC = ICI / "latex"
ZIP = ICI / "Rapport_Overleaf.zip"


def main():
    fichiers = sorted(p for p in SRC.rglob("*") if p.is_file())
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for p in fichiers:
            # date fixe : l'archive ne change que si son contenu change
            info = zipfile.ZipInfo(p.relative_to(SRC).as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, p.read_bytes())
    print(f"  -> {ZIP.name} ({len(fichiers)} fichiers)")


if __name__ == "__main__":
    main()
