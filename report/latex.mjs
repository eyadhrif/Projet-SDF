// Version LaTeX / Overleaf du rapport, générée à partir des MÊMES sources que le PDF (source/*.md),
// sur le modèle du rapport de référence (préambule XeLaTeX, page de garde, chapitres avec Introduction et
// Conclusion, bibliographie IEEE sur deux colonnes, glossaire, résumés trilingues).
//   node build.mjs --latex   ->  latex/ (main.tex, chapters/, figures/, .latexmkrc, LISEZMOI.md)
// Les chiffres viennent de generated/valeurs.json, comme dans le PDF : rien n'est recopié à la main.
import { marked } from 'marked'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { ieee } from './ieee.mjs'

const ICI = path.dirname(fileURLToPath(import.meta.url))
const P = (...a) => path.join(ICI, ...a)
const OUT = P('latex')
const lire = (f) => fs.readFileSync(f, 'utf-8')

// ------------------------------------------------------------------ texte -> LaTeX
// caractères hors Latin-1 du texte courant : rendus en mode mathématique ou par une commande,
// pour compiler aussi bien avec XeLaTeX qu'avec pdfLaTeX (compilateur par défaut d'Overleaf)
const UNICODE = {
  'α': '\\ensuremath{\\alpha}', 'β': '\\ensuremath{\\beta}', 'γ': '\\ensuremath{\\gamma}', 'δ': '\\ensuremath{\\delta}',
  'η': '\\ensuremath{\\eta}', 'λ': '\\ensuremath{\\lambda}', 'μ': '\\ensuremath{\\mu}', 'ρ': '\\ensuremath{\\rho}',
  'σ': '\\ensuremath{\\sigma}', 'τ': '\\ensuremath{\\tau}', 'Δ': '\\ensuremath{\\Delta}', 'Γ': '\\ensuremath{\\Gamma}',
  '≤': '\\ensuremath{\\le}', '≥': '\\ensuremath{\\ge}', '≈': '\\ensuremath{\\approx}', '−': '\\ensuremath{-}',
  '→': '\\ensuremath{\\rightarrow}', '⇔': '\\ensuremath{\\Leftrightarrow}', '×': '\\ensuremath{\\times}',
  '²': '\\textsuperscript{2}', ' ': '\\,', ' ': '~', '…': '\\dots{}', '“': '``', '”': "''",
}
export function esc(s) {
  return s.replace(/[\\{}$&%#_^~]/g, (c) => ({ '\\': '\\textbackslash{}', '^': '\\textasciicircum{}', '~': '\\textasciitilde{}' }[c] || `\\${c}`))
    .replace(/[αβγδηλμρστΔΓ≤≥≈−→⇔×²  …“”]/g, (c) => UNICODE[c])
}

// placeholders « @@Tn@@ » : fragments déjà en LaTeX, protégés de l'échappement
function coffre() {
  const t = []
  const garder = (s) => `@@T${t.push(s) - 1}@@`
  const rendre = (s) => { let n; do { n = s; s = s.replace(/@@T(\d+)@@/g, (_, i) => t[+i]) } while (s !== n); return s }
  return { garder, rendre }
}

function inline(tokens) {
  return (tokens || []).map((t) => {
    switch (t.type) {
      case 'text': return t.tokens ? inline(t.tokens) : esc(t.text)
      case 'escape': return esc(t.text)
      case 'strong': return `\\textbf{${inline(t.tokens)}}`
      case 'em': return `\\emph{${inline(t.tokens)}}`
      case 'codespan': return `\\code{${esc(t.text)}}`
      case 'link': return `\\href{${t.href}}{${inline(t.tokens)}}`
      case 'br': return '\\\\'
      case 'del': return inline(t.tokens)
      case 'html': throw new Error(`HTML non converti en LaTeX : ${t.text.slice(0, 60)}`)
      default: throw new Error(`élément en ligne non géré : ${t.type}`)
    }
  }).join('')
}
const ligne = (s) => inline(marked.Lexer.lexInline(s))

const ASCII_DIAGRAMME = { '│': '|', '▼': 'v', '├': '+', '└': '`', '─': '-', '►': '>' }
function tableau(t, { centre = true } = {}) {
  const al = t.align.map((a) => (a === 'right' ? 'r' : a === 'center' ? 'c' : 'l')).join('')
  const cell = (c) => inline(c.tokens)
  const lignes = [`\\begin{tabular}{${al}}`, '\\toprule', t.header.map(cell).join(' & ') + ' \\\\', '\\midrule',
    ...t.rows.map((r) => r.map(cell).join(' & ') + ' \\\\'), '\\bottomrule', '\\end{tabular}']
  return `\\begin{adjustbox}{max width=\\linewidth${centre ? ',center' : ''}}\n${lignes.join('\n')}\n\\end{adjustbox}`
}

function blocs(tokens) {
  return tokens.map((t) => {
    switch (t.type) {
      case 'space': return ''
      case 'paragraph': return inline(t.tokens) + '\n'
      case 'heading': throw new Error(`titre non converti : ${t.text}`)
      case 'list': {
        const env = t.ordered ? 'enumerate' : 'itemize'
        return `\\begin{${env}}\n${t.items.map((i) => `\\item ${blocs(i.tokens).trim()}`).join('\n')}\n\\end{${env}}\n`
      }
      case 'blockquote': return `\\begin{problembox}\\normalfont\\raggedright\n${blocs(t.tokens).trim()}\n\\end{problembox}\n`
      case 'code': return `\\begin{verbatim}\n${t.text.replace(/[│▼├└─►]/g, (c) => ASCII_DIAGRAMME[c])}\n\\end{verbatim}\n`
      case 'table': return `\\begin{center}\\small\n${tableau(t, { centre: false })}\n\\end{center}\n`
      case 'text': return (t.tokens ? inline(t.tokens) : esc(t.text)) + '\n'
      case 'html': {
        if (/^@@T\d+@@\s*$/.test(t.text.trim())) return t.text.trim() + '\n'
        throw new Error(`HTML non converti en LaTeX : ${t.text.slice(0, 60)}`)
      }
      case 'hr': return '\\noindent\\rule{\\linewidth}{0.4pt}\n'
      default: throw new Error(`bloc non géré : ${t.type}`)
    }
  }).join('\n')
}

// ------------------------------------------------------------------ gabarits (d'après le rapport de référence)
function preambule(M) {
  return String.raw`% Rapport du projet SdF — version LaTeX générée par report/build.mjs --latex (ne pas modifier à la main :
% modifier report/source/*.md puis régénérer). Compiler de préférence avec XeLaTeX (latexmk lit .latexmkrc) ;
% pdfLaTeX (défaut d'Overleaf) fonctionne aussi : le résumé arabe est alors inclus en image.
\documentclass[12pt,a4paper,oneside]{report}

% ---------- polices et langues ----------
\usepackage{iftex}
\usepackage{amsmath}
\ifXeTeX
  \usepackage{mathptmx}
  \usepackage{fontspec}
  % Times New Roman si elle est installée, sinon son clone libre TeX Gyre Termes, désigné par ses fichiers
  % (trouvés par TeX Live partout, Overleaf compris, même quand la police n'est pas déclarée au système)
  \IfFontExistsTF{Times New Roman}{\setmainfont{Times New Roman}}
    {\IfFontExistsTF{TeX Gyre Termes}{\setmainfont{TeX Gyre Termes}}
      {\setmainfont{texgyretermes}[Extension=.otf,UprightFont=*-regular,BoldFont=*-bold,ItalicFont=*-italic,BoldItalicFont=*-bolditalic]}}
  \setmonofont{lmmono10-regular}[Extension=.otf,Scale=0.95]
  \usepackage[bidi=default,english,french]{babel}
  \frenchsetup{StandardLists=true,SmallCapsFigTabCaptions=false}
  \babelprovide[import]{arabic}
  \babelfont[arabic]{rm}[Scale=1.15]{Amiri}
  \newcommand{\arabicabstract}{\begin{otherlanguage}{arabic}\input{chapters/resume_arabe}\end{otherlanguage}}
\else
  \usepackage[T1]{fontenc}
  \usepackage[utf8]{inputenc}
  \usepackage{mathptmx}
  \usepackage[scaled=0.92]{helvet}
  \usepackage{lmodern}\renewcommand{\rmdefault}{ptm}\renewcommand{\ttdefault}{lmtt}
  \usepackage[english,french]{babel}
  \frenchsetup{StandardLists=true,SmallCapsFigTabCaptions=false}
  \newcommand{\arabicabstract}{\noindent\includegraphics[width=\linewidth]{figures/resume_arabe.pdf}}
\fi

% ---------- mise en page ----------
\usepackage[a4paper,top=2.6cm,bottom=2.6cm,left=2.5cm,right=2.5cm,headheight=15pt]{geometry}
\usepackage{setspace}\setstretch{1.3}
\setlength{\parindent}{0pt}
\setlength{\parskip}{4pt}
\usepackage{xcolor}
\definecolor{navy}{RGB}{20,30,110}
\definecolor{linkblue}{RGB}{28,84,140}
\definecolor{headgray}{RGB}{90,90,90}
\definecolor{boxgray}{RGB}{244,244,244}

\usepackage{titlesec}
\titleformat{\chapter}[display]{\normalfont\bfseries\fontsize{26}{30}\selectfont}
  {\chaptertitlename\ \thechapter}{14pt}{\fontsize{24}{28}\selectfont}
\titlespacing*{\chapter}{0pt}{20pt}{24pt}
\titleformat{name=\chapter,numberless}[display]{\normalfont\bfseries\fontsize{26}{30}\selectfont}{}{0pt}{}
\titlespacing*{name=\chapter,numberless}{0pt}{20pt}{24pt}
\titleformat{\section}{\normalfont\Large\bfseries\color{headgray}}{\thesection}{0.8em}{}
\titleformat{\subsection}{\normalfont\large\bfseries\color{headgray}}{\thesubsection}{0.8em}{}

\usepackage{fancyhdr}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small\color{headgray}${M.entete}}
\fancyhead[R]{\small\color{headgray}\nouppercase{\leftmark}}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.5pt}
\renewcommand{\chaptermark}[1]{\markboth{\chaptername\ \thechapter.\ #1}{}}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[C]{\thepage}\renewcommand{\headrulewidth}{0pt}}
\newcommand{\frontmark}[1]{\markboth{#1}{#1}}

% ---------- contenu ----------
\usepackage{graphicx}
\usepackage{booktabs,tabularx,array}
\usepackage{adjustbox}
\usepackage{amssymb}
\usepackage{enumitem}\setlist{itemsep=2pt,topsep=4pt}\setlist[itemize]{label=\textbullet}
\usepackage{caption}\captionsetup{labelsep=colon,font=normalsize,skip=8pt}
\usepackage{float}
\usepackage{multicol}
\usepackage[most]{tcolorbox}
\usepackage[hidelinks,colorlinks=true,linkcolor=linkblue,citecolor=teal,urlcolor=linkblue]{hyperref}

\newcommand{\codeus}{\textunderscore\allowbreak}
\newcommand{\code}[1]{{\ttfamily\let\_\codeus #1}}
\newtcolorbox{problembox}{colback=boxgray,colframe=boxgray,boxrule=0pt,arc=0pt,
  left=10pt,right=10pt,top=8pt,bottom=8pt,fontupper=\itshape,halign=center}

% Introduction / Conclusion non numérotées dans chaque chapitre
\newcommand{\chapintro}{\section*{Introduction}}
\newcommand{\chapconclusion}{\section*{Conclusion}}

\addto\captionsfrench{\renewcommand{\listfigurename}{Liste des figures}\renewcommand{\listtablename}{Liste des tableaux}%
  \renewcommand{\tablename}{Tableau}%
  \renewcommand{\contentsname}{Table des matières}\renewcommand{\bibname}{Bibliographie}}

\setcounter{tocdepth}{1}
`
}

function pageDeGarde(M) {
  const e = (s) => esc(s)
  return String.raw`% =================== PAGE DE GARDE ===================
\begin{titlepage}
\newgeometry{top=1.4cm,bottom=1.6cm,left=2.4cm,right=2.4cm}
\setstretch{1.05}
\centering
\noindent
\begin{minipage}[c]{0.3\linewidth}\raggedright
  \IfFileExists{figures/logo_univ_tunis.png}{\includegraphics[height=2.1cm,keepaspectratio]{figures/logo_univ_tunis.png}}{}
\end{minipage}%
\begin{minipage}[c]{0.4\linewidth}\centering
  \includegraphics[height=2.2cm,keepaspectratio]{figures/logo_emblem.png}
\end{minipage}%
\begin{minipage}[c]{0.3\linewidth}\raggedleft
  \includegraphics[height=1.5cm,keepaspectratio]{figures/logo_ensit.png}
\end{minipage}

\vspace{0.5cm}
\rule{\linewidth}{1pt}\par
\vspace{0.35cm}
{\large\bfseries ${e(M.universite)}\par}
\vspace{2pt}
{\large\bfseries ${e(M.ecole)}\par}
\vspace{2pt}
{\bfseries ${e(M.departement)}\par}
\vspace{0.3cm}
\rule{\linewidth}{1pt}\par

\vfill
{\LARGE\bfseries ${e(M.type)}\par}
\vspace{0.35em}
{\normalsize\bfseries ${e(M.formation)}\par}

${M.auteurs.length ? `\\vspace{0.7cm}
{\\normalsize ${e(M.presente_par)}\\par}
\\vspace{0.4em}
{\\LARGE\\bfseries ${M.auteurs.map(e).join('\\\\[0.2em] ')}\\par}
` : ''}
\vfill
\rule{0.85\linewidth}{0.6pt}\par
\vspace{0.7em}
{\fontsize{24}{30}\selectfont\bfseries ${e(M.titre).replace(' et maintenance', '\\\\ et maintenance')}\par}
\vspace{0.5em}
{\large\bfseries ${e(M.sous_titre)}\par}
\vspace{0.7em}
\rule{0.85\linewidth}{0.6pt}\par

\vfill
\IfFileExists{figures/logo_projet.pdf}{\includegraphics[height=4.6cm,keepaspectratio]{figures/logo_projet.pdf}\par}{}

\vfill
{\normalsize ${e(M.version)}\par}
\vspace{0.5em}
{\normalsize\textbf{Encadré par :} ${e(M.encadrant)}\par}

\vfill
{\normalsize\textbf{Année universitaire :} ${e(M.annee)}\par}

\restoregeometry
\end{titlepage}
% =================== FIN DE LA PAGE DE GARDE ===================
`
}

// ------------------------------------------------------------------ génération
export function genererLatex() {
  const V = JSON.parse(lire(P('generated', 'valeurs.json')))
  const TITRES = JSON.parse(lire(P('generated', 'tableaux.json')))
  const BIB = JSON.parse(lire(P('bibliographie.json')))
  const META = JSON.parse(lire(P('metadonnees.json')))
  const bibCles = new Map(BIB.map((e) => [e.cle, e]))
  const fichiers = fs.readdirSync(P('source')).filter((f) => f.endsWith('.md')).sort()
  const { garder, rendre } = coffre()
  const texDecimal = (tex) => tex.replace(/(\d),(\d)/g, '$1{,}$2').replace(/ /g, '\\,')

  // étiquettes (numéros attribués par LaTeX) : on ne retient que le type des sections, pour le mot du renvoi
  const niveauSec = {}, titreSec = {}, ordreCites = []
  const sortie = {}
  let horsNumerotation = false
  let arabe = ''

  for (const f of fichiers) {
    let md = lire(P('source', f)).replace(/\r\n?/g, '\n').replace(/<!--[\s\S]*?-->/g, '')
    md = md.replace(/\{\{\s*(\w+)\s*\}\}/g, (_, k) => { if (!(k in V)) throw new Error(`valeur inconnue ${k}`); return V[k] })

    // formules
    md = md.replace(/\$\$([\s\S]+?)\$\$(?:\s*\{#(eq:[\w-]+)\})?/g, (_, tex, id) =>
      '\n\n' + garder(id ? `\\begin{equation}\\label{${id}}\n${texDecimal(tex.trim())}\n\\end{equation}`
        : `\\begin{equation*}\n${texDecimal(tex.trim())}\n\\end{equation*}`) + '\n\n')
    md = md.replace(/(?<![\\$])\$([^$\n]+?)\$/g, (_, tex) => garder(`$${texDecimal(tex)}$`))

    // directives de page
    md = md.replace(/^!page-de-garde[ \t]*$/m, () => garder(pageDeGarde(META)))
    md = md.replace(/^!table-des-matieres[ \t]*$/m, () => garder('\\tableofcontents'))
    md = md.replace(/^!liste-des-figures[ \t]*$/m, () => garder('\\clearpage\\frontmark{Liste des figures}\n\\listoffigures'))
    md = md.replace(/^!liste-des-tableaux[ \t]*$/m, () => garder('\\clearpage\\frontmark{Liste des tableaux}\n\\listoftables'))
    md = md.replace(/^!bibliographie[ \t]*$/m, () => '@@BIBLIOGRAPHIE@@')

    // titres
    let dansCode = false
    md = md.split('\n').map((l) => {
      if (/^```/.test(l)) dansCode = !dansCode
      if (dansCode) return l
      const m = l.match(/^(#{1,3})\s+(.+?)(?:\s*\{(#sec:[\w-]+|-)\})?[ \t]*$/)
      if (!m) return l
      const niv = m[1].length, titre = m[2], att = m[3]
      const id = att && att !== '-' ? att.slice(1) : null
      const T = ligne(titre)
      if (niv === 1) horsNumerotation = att === '-'
      if (id) { niveauSec[id] = niv; if (horsNumerotation) titreSec[id] = titre }
      const label = id ? `\\label{${id}}` : ''
      if (niv === 1) {
        if (['Table des matières', 'Liste des figures', 'Liste des tableaux'].includes(titre)) return ''   // titres produits par LaTeX
        if (titre === 'Bibliographie') return ''
        if (titre === 'Résumé') return garder(`\\clearpage\\pagestyle{empty}\\thispagestyle{empty}\n\\addcontentsline{toc}{chapter}{${T}}\n\\setstretch{1.1}\\small`)
        if (att === '-') return garder(`\\chapter*{${T}}\n\\addcontentsline{toc}{chapter}{${T}}\n\\frontmark{${T}}`)
        return garder(`\\chapter{${T}}${label}`)
      }
      if (niv === 2 && !id && titre === 'Introduction') return garder('\\chapintro')
      if (niv === 2 && !id && titre === 'Conclusion') return garder('\\chapconclusion')
      const cmd = niv === 2 ? 'section' : 'subsection'
      if (horsNumerotation || att === '-') {
        if (['Résumé', 'Abstract', 'ملخص'].includes(titre)) return garder(`\\noindent{\\large\\bfseries ${T}}\\par\\medskip`)
        return garder(`\\${cmd}*{${T}}${id ? `\\phantomsection${label}` : ''}`)
      }
      return garder(`\\${cmd}{${T}}${label}`)
    }).join('\n')

    // figures et tableaux
    md = md.replace(/^!figure\[([\w-]+)\]\((.*)\)(?:\{largeur=(\d+)\})?[ \t]*$/gm, (_, nom, leg, larg) => {
      const src = nom.startsWith('dashboard_') ? `figures/${nom}.png` : `figures/${nom}.pdf`
      const w = larg ? (larg / 100).toFixed(2) : '1'
      return garder(`\\begin{figure}[htbp]\n\\centering\n\\includegraphics[width=${w}\\linewidth]{${src}}\n\\caption{${ligne(leg)}}\\label{fig:${nom}}\n\\end{figure}`)
    })
    md = md.replace(/^!tableau\[([\w-]+)\](?:\(([^)]*)\))?[ \t]*$/gm, (_, nom, leg) => {
      const t = marked.lexer(lire(P('tables', `${nom}.md`))).find((x) => x.type === 'table')
      return garder(`\\begin{table}[htbp]\n\\centering\\small\n${tableau(t)}\n\\caption{${ligne(leg || TITRES[nom])}}\\label{tab:${nom}}\n\\end{table}`)
    })

    // renvois et citations
    md = md.replace(/\[@((fig|tab|eq|sec):[\w-]+)\]/g, (_, id, type) => {
      if (type === 'eq') return garder(`\\eqref{${id}}`)
      if (type === 'fig') return garder(`figure~\\ref{${id}}`)
      if (type === 'tab') return garder(`tableau~\\ref{${id}}`)
      return garder(`@@SEC:${id}@@`)                      // résolu une fois tous les titres connus
    })
    md = md.replace(/\[cite:([\w,\s-]+)\]/g, (_, liste) => {
      const cles = liste.split(',').map((c) => c.trim())
      for (const c of cles) { if (!bibCles.has(c)) throw new Error(`référence inconnue ${c}`); if (!ordreCites.includes(c)) ordreCites.push(c) }
      return garder(`\\cite{${cles.join(',')}}`)
    })

    // blocs « ::: »
    md = md.replace(/^:::(\w+)[ \t]*\n([\s\S]*?)\n:::[ \t]*$/gm, (_, nom, corps) => {
      if (nom === 'dedicace') {
        const strophes = corps.trim().split(/\n\s*\n/).map((s) => s.trim().split('\n').map(ligne).join('\\\\\n'))
        return garder(`\\vspace*{2.5cm}\n\\begin{center}\n\\itshape\n${strophes.join('\\\\[1.4em]\n')}\n\\end{center}`)
      }
      if (nom === 'encadre') return garder(`\\begin{problembox}\n${ligne(corps.trim())}\n\\end{problembox}`)
      if (nom === 'glossaire') return garder(`{\\setstretch{1.1}\\small\\setlength{\\parskip}{3pt}\n${rendre(blocs(marked.lexer(corps)))}}`)
      if (nom === 'resumes') {
        const parties = rendre(blocs(marked.lexer(corps))).replace(/(\\noindent\{\\large\\bfseries Abstract\})/, '\\par\\medskip\\noindent\\rule{\\linewidth}{0.4pt}\\par\\medskip\n$1')
        return garder(parties)
      }
      if (nom === 'arabe') {
        arabe = rendre(blocs(marked.lexer(corps)))
        return garder('\\par\\medskip\\noindent\\rule{\\linewidth}{0.4pt}\\par\\medskip\n\\arabicabstract')
      }
      throw new Error(`bloc inconnu ${nom}`)
    })
    sortie[f] = md
  }

  // conversion Markdown -> LaTeX, renvois de sections, bibliographie
  const bibliographie = String.raw`\chapter*{Bibliographie}
\addcontentsline{toc}{chapter}{Bibliographie}
\frontmark{Bibliographie}
\begin{multicols}{2}
\small\setstretch{1.15}\sloppy
\begingroup
\renewcommand{\chapter}[2]{}% le titre est déjà imprimé
\begin{thebibliography}{99}
\setlength{\itemsep}{2pt}
${ordreCites.map((c) => `\\bibitem{${c}} ${ligne(ieee(bibCles.get(c), { it: (s) => `*${s}*`, q: (s) => `“${s},”` }))}`).join('\n')}
\end{thebibliography}
\endgroup
\end{multicols}`
  const chapitres = []
  for (const [f, md] of Object.entries(sortie)) {
    let tex = rendre(blocs(marked.lexer(md)))
    tex = tex.replace(/@@SEC:([\w:-]+)@@/g, (_, id) => {
      if (!(id in niveauSec)) throw new Error(`renvoi inconnu ${id}`)
      if (titreSec[id]) return `\\hyperref[${id}]{«~${esc(titreSec[id])}~»}`
      return `${niveauSec[id] === 1 ? 'chapitre' : 'section'}~\\ref{${id}}`
    })
    tex = tex.replace('@@BIBLIOGRAPHIE@@', bibliographie)
    if (/@@|\*\*|\{\{|\[cite:|\[@/.test(tex)) throw new Error(`marqueur non résolu dans ${f}`)
    const nom = f.replace(/\.md$/, '.tex')
    chapitres.push(nom)
    fs.mkdirSync(path.join(OUT, 'chapters'), { recursive: true })
    fs.writeFileSync(path.join(OUT, 'chapters', nom), `% généré depuis source/${f} — ne pas modifier à la main\n${tex.replace(/\n{3,}/g, '\n\n')}`)
  }
  fs.writeFileSync(path.join(OUT, 'chapters', 'resume_arabe.tex'), `% généré depuis source/15_resumes.md\n${arabe}`)

  // document principal : la page de garde puis les pages liminaires, comme le modèle
  const corps = chapitres.map((c) => {
    const inp = `\\input{chapters/${c.replace(/\.tex$/, '')}}`
    if (c.startsWith('00_')) return `${inp}\n\n\\pagenumbering{arabic}`
    if (c.startsWith('03_')) return `\\clearpage\n\\setcounter{page}{1}\n${inp}`
    return inp
  }).join('\n')
  fs.writeFileSync(path.join(OUT, 'main.tex'), `${preambule(META)}\n\\begin{document}\n${corps}\n\\end{document}\n`)
  fs.writeFileSync(path.join(OUT, '.latexmkrc'), '# Compiler avec XeLaTeX (Times New Roman et résumé arabe)\n$pdf_mode = 5;\n')

  // figures : PDF vectoriels du rapport, captures du dashboard, logos
  const FIG = path.join(OUT, 'figures'); fs.mkdirSync(FIG, { recursive: true })
  for (const f of fs.readdirSync(P('figures')).filter((x) => x.endsWith('.pdf'))) fs.copyFileSync(P('figures', f), path.join(FIG, f))
  for (const f of fs.readdirSync(P('captures'))) fs.copyFileSync(P('captures', f), path.join(FIG, f))
  for (const f of fs.readdirSync(P('logos'))) fs.copyFileSync(P('logos', f), path.join(FIG, f))
  fs.writeFileSync(path.join(OUT, 'LISEZMOI.md'), `# Rapport — version LaTeX (Overleaf)

Projet généré automatiquement par \`report/build.mjs --latex\` à partir de \`report/source/*.md\`.
Pour modifier le texte, modifier les sources Markdown puis régénérer : ne pas modifier ces fichiers à la main.

## Overleaf

1. *New Project* → *Upload Project* → choisir \`Rapport_Overleaf.zip\`.
2. *Menu* → *Compiler* : **XeLaTeX** (recommandé : police Times New Roman et résumé arabe en texte).
   Avec pdfLaTeX (défaut d'Overleaf), le document compile aussi ; le résumé arabe est alors inclus en image.
3. Fichier principal : \`main.tex\`.

## En local

\`\`\`bash
latexmk main.tex        # lit .latexmkrc : XeLaTeX
\`\`\`
`)
  return { chapitres: chapitres.length, references: ordreCites.length }
}
