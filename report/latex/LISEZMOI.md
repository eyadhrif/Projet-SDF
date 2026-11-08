# Rapport — version LaTeX (Overleaf)

Projet généré automatiquement par `report/build.mjs --latex` à partir de `report/source/*.md`.
Pour modifier le texte, modifier les sources Markdown puis régénérer : ne pas modifier ces fichiers à la main.

## Overleaf

1. *New Project* → *Upload Project* → choisir `Rapport_Overleaf.zip`.
2. *Menu* → *Compiler* : **XeLaTeX** (recommandé : police Times New Roman et résumé arabe en texte).
   Avec pdfLaTeX (défaut d'Overleaf), le document compile aussi ; le résumé arabe est alors inclus en image.
3. Fichier principal : `main.tex`.

## En local

```bash
latexmk main.tex        # lit .latexmkrc : XeLaTeX
```
