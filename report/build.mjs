// Construction du rapport scientifique (Version 1)
//   node build.mjs            -> build/rapport.html puis Rapport_V1_FMDS_Eya_Salma.pdf (Chromium)
//   node build.mjs --check    -> vérifications seules (pas de PDF)
//   node build.mjs --captures -> captures d'écran du dashboard autonome dans captures/
//
// Source : source/*.md (un fichier par chapitre, dans l'ordre des noms). Syntaxe ajoutée au Markdown :
//   {{cle}}                    valeur de generated/valeurs.json (aucun chiffre de résultat tapé à la main)
//   $...$  et  $$...$$ {#eq:x}  formules (KaTeX) ; les formules étiquetées sont numérotées
//   # Titre {#sec:x}            titres numérotés (1, 1.1, 1.1.1) ; {-} pour un titre non numéroté
//   !figure[nom](légende)      figures/nom.png, numérotée ; {largeur=60} en option (en % de la page)
//   !tableau[nom]              tables/nom.md, numéroté, titre = generated/tableaux.json ; (légende) en option
//   [@fig:x] [@tab:x] [@eq:x] [@sec:x]   renvois numérotés
//   [cite:a,b]                 citations numériques, bibliographie = bibliographie.json (ordre d'apparition)
//   !table-des-matieres  !liste-des-figures  !liste-des-tableaux  !bibliographie
// Toute erreur (valeur, figure, tableau, renvoi ou référence inconnus ; figure, tableau ou référence
// jamais cités ; formule invalide) arrête la construction avec un code de sortie 1.
import { marked } from 'marked'
import katex from 'katex'
import { ieee } from './ieee.mjs'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const ICI = path.dirname(fileURLToPath(import.meta.url))
const P = (...a) => path.join(ICI, ...a)
const ARGS = new Set(process.argv.slice(2))
const PDF_NOM = 'Rapport_V1_FMDS_Eya_Salma.pdf'
const META_ENTETE = JSON.parse(fs.readFileSync(path.join(path.dirname(fileURLToPath(import.meta.url)), 'metadonnees.json'), 'utf-8')).entete
// --sortie=<fichier.pdf> : écrire le PDF ailleurs (utilisé par les tests, pour ne pas toucher au PDF livré)
const SORTIE = (process.argv.find((a) => a.startsWith('--sortie=')) || '').slice(9) || P(PDF_NOM)
const erreurs = []
const err = (m) => erreurs.push(m)
const lire = (f) => fs.readFileSync(f, 'utf-8')

// ------------------------------------------------------------------ captures du dashboard
async function captures() {
  const { chromium } = await import('@playwright/test')
  const out = P('captures'); fs.mkdirSync(out, { recursive: true })
  const url = pathToFileURL(P('..', 'dashboard_autonome.html')).href
  const b = await chromium.launch()
  const page = await b.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 })
  for (const id of ['overview', 'fiab', 'mon', 'rul']) {
    await page.goto('about:blank'); await page.goto(`${url}#${id}`)
    await page.waitForSelector('main h1'); await page.waitForTimeout(2500)      // fin des animations
    await page.screenshot({ path: path.join(out, `dashboard_${id}.png`), fullPage: false })
    console.log(`  -> captures/dashboard_${id}.png`)
  }
  await b.close()
}

// page de garde (métadonnées : metadonnees.json ; logos : logos/), sur le modèle du rapport de référence
function pageDeGardeHtml(M) {
  const logo = (f, h) => `<img src="../logos/${f}" style="height:${h}">`
  return `<div class="page-titre">
<div class="logos"><div>${logo('logo_univ_tunis.png', '21mm')}</div><div>${logo('logo_emblem.png', '22mm')}</div><div>${logo('logo_ensit.png', '15mm')}</div></div>
<div class="filet"></div>
<div class="inst"><b>${M.universite}</b><br><b>${M.ecole}</b><br><span>${M.departement}</span></div>
<div class="filet"></div>
<div class="type">${M.type}</div><div class="formation">${M.formation}</div>
<div class="par">${M.presente_par}</div><div class="auteurs">${M.auteurs.join('<br>')}</div>
<div class="filet fin"></div><div class="titre">${M.titre}</div><div class="sous-titre">${M.sous_titre}</div><div class="filet fin"></div>
<div class="version">${M.version}</div>
<div class="encadrant"><b>Encadré par :</b> ${M.encadrant}</div>
<div class="annee"><b>Année universitaire :</b> ${M.annee}</div>
</div>`
}

const SANS_TOC = new Set(['Introduction', 'Conclusion', 'Résumé', 'Abstract', 'ملخص', 'Table des matières',
  'Liste des figures', 'Liste des tableaux'])

// ------------------------------------------------------------------ assemblage du document
function construire() {
  const V = JSON.parse(lire(P('generated', 'valeurs.json')))
  const TITRES = JSON.parse(lire(P('generated', 'tableaux.json')))
  const BIB = JSON.parse(lire(P('bibliographie.json')))
  const bibCles = new Map(BIB.map((e) => [e.cle, e]))
  const chapitres = fs.readdirSync(P('source')).filter((f) => f.endsWith('.md')).sort()
  let md = chapitres.map((f) => lire(P('source', f))).join('\n\n')
  md = md.replace(/\r\n?/g, '\n')                              // fins de ligne Windows
  md = md.replace(/<!--[\s\S]*?-->/g, '')

  // 1. valeurs
  const utilisees = new Set()
  md = md.replace(/\{\{\s*([\w]+)\s*\}\}/g, (_, k) => {
    if (!(k in V)) { err(`valeur inconnue {{${k}}}`); return `??${k}??` }
    utilisees.add(k); return V[k]
  })
  const META = JSON.parse(lire(P('metadonnees.json')))
  md = md.replace(/^!page-de-garde[ \t]*$/m, () => pageDeGardeHtml(META))

  // 2. formules : mises de côté (marked ne doit pas toucher au TeX)
  const maths = []
  const garder = (html) => `@@MATH${maths.push(html) - 1}@@`
  // dans une formule, la virgule décimale s'écrit {,} et l'espace des milliers \, (valeurs au format français)
  const texDecimal = (tex) => tex.replace(/(\d),(\d)/g, '$1{,}$2').replace(/ /g, '\\,')
  const labels = { fig: [], tab: [], eq: [], sec: [] }
  const numero = {}
  const niveau = {}
  const titreSec = {}
  md = md.replace(/\$\$([\s\S]+?)\$\$(?:\s*\{#(eq:[\w-]+)\})?/g, (_, tex, id) => {
    let html
    try { html = katex.renderToString(texDecimal(tex.trim()), { displayMode: true, throwOnError: true, strict: 'ignore' }) }
    catch (e) { err(`formule invalide : ${tex.trim().slice(0, 60)} (${e.message})`); html = '' }
    if (id) { labels.eq.push(id); numero[id] = labels.eq.length }
    const n = id ? `<span class="eqn">(${labels.eq.length})</span>` : ''
    return `\n\n${garder(`<div class="equation"${id ? ` id="${id}"` : ''}>${html}${n}</div>`)}\n\n`
  })
  md = md.replace(/(?<![\\$])\$([^$\n]+?)\$/g, (_, tex) => {
    try { return garder(katex.renderToString(texDecimal(tex), { throwOnError: true, strict: 'ignore' })) }
    catch (e) { err(`formule invalide : $${tex}$ (${e.message})`); return '' }
  })

  // 3. titres numérotés
  const compte = [0, 0, 0]
  const toc = []
  let horsNumerotation = false          // sous un chapitre non numéroté (annexes) : titres non numérotés
  let dansCode = false                   // les « # » d'un bloc de code (commentaires bash) ne sont pas des titres
  md = md.split('\n').map((l) => {
    if (/^```/.test(l)) dansCode = !dansCode
    if (dansCode) return l
    const m = l.match(/^(#{1,3})\s+(.+?)(?:\s*\{(#sec:[\w-]+|-)\})?[ \t]*$/)
    if (!m) return l
    const niv = m[1].length, titre = m[2], att = m[3]
    if (niv === 1) horsNumerotation = att === '-'
    let num = ''
    if (att !== '-' && !horsNumerotation) {
      compte[niv - 1] += 1; for (let i = niv; i < 3; i++) compte[i] = 0
      num = compte.slice(0, niv).join('.')
    }
    const id = att && att !== '-' ? att.slice(1) : `t${toc.length}`
    if (att && att !== '-') {
      labels.sec.push(id); niveau[id] = niv
      numero[id] = num || null; if (!num) titreSec[id] = titre          // renvoi par le titre (annexes)
    }
    toc.push({ niv, num, titre, id })
    const titreHtml = marked.parseInline(titre)
    return `<h${niv} id="${id}"${niv === 1 ? ' class="chapitre"' : ''}>${num ? `<span class="num">${num}</span> ` : ''}${titreHtml}</h${niv}>`
  }).join('\n')

  // 4. figures et tableaux
  const figs = [], tabs = []
  md = md.replace(/^!figure\[([\w-]+)\]\((.*)\)(?:\{largeur=(\d+)\})?[ \t]*$/gm, (_, nom, leg, larg) => {
    const f = P('figures', `${nom}.png`)
    const capt = nom.startsWith('dashboard_') ? P('captures', `${nom}.png`) : null
    const src = capt && fs.existsSync(capt) ? `../captures/${nom}.png` : `../figures/${nom}.png`
    if (!fs.existsSync(capt || f)) err(`figure introuvable : ${nom}`)
    const id = `fig:${nom}`; labels.fig.push(id); numero[id] = labels.fig.length; figs.push({ id, leg })
    return `<figure id="${id}"><img src="${src}" style="width:${larg || 100}%"><figcaption><b>Figure ${labels.fig.length}</b> – ${marked.parseInline(leg)}</figcaption></figure>`
  })
  md = md.replace(/^!tableau\[([\w-]+)\](?:\(([^)]*)\))?[ \t]*$/gm, (_, nom, leg) => {
    const f = P('tables', `${nom}.md`)
    if (!fs.existsSync(f)) { err(`tableau introuvable : ${nom}`); return '' }
    const titre = leg || TITRES[nom] || nom
    const id = `tab:${nom}`; labels.tab.push(id); numero[id] = labels.tab.length; tabs.push({ id, titre })
    return `<div class="tableau" id="${id}"><div class="legende"><b>Tableau ${labels.tab.length}</b> – ${marked.parseInline(titre)}</div>\n\n${lire(f)}\n</div>`
  })

  // 5. renvois
  const cites = new Set()
  const NOMS = { fig: 'figure', tab: 'tableau', eq: 'équation', sec: 'section' }
  md = md.replace(/\[@((fig|tab|eq|sec):[\w-]+)\]/g, (_, id, type) => {
    cites.add(id)
    if (!(id in numero)) { err(`renvoi inconnu : ${id}`); return `??${id}??` }
    const nom = type === 'sec' && niveau[id] === 1 ? 'chapitre' : NOMS[type]
    const n = titreSec[id] ? `« ${titreSec[id]} »` : type === 'eq' ? `(${numero[id]})` : `${nom} ${numero[id]}`
    return `<a href="#${id}">${n}</a>`
  })
  for (const id of [...labels.fig, ...labels.tab]) if (!cites.has(id)) err(`${id} n'est jamais cité dans le texte`)

  // 6. citations bibliographiques (numérotées par ordre d'apparition)
  const ordre = []
  md = md.replace(/\[cite:([\w,\s-]+)\]/g, (_, liste) => {
    const nums = liste.split(',').map((c) => c.trim()).map((c) => {
      if (!bibCles.has(c)) { err(`référence inconnue : ${c}`); return '?' }
      if (!ordre.includes(c)) ordre.push(c)
      return `<a href="#ref-${c}">${ordre.indexOf(c) + 1}</a>`
    })
    return `[${nums.join(', ')}]`
  })
  for (const e of BIB) if (!ordre.includes(e.cle)) err(`référence jamais citée : ${e.cle}`)

  // 7. listes générées
  const lien = (id, t) => `<a href="#${id}">${t}</a>`
  // profondeur 1 comme le modèle : chapitres et sections ; ni « Introduction / Conclusion » de chapitre, ni les listes
  const dansToc = (t) => t.niv === 1 ? !SANS_TOC.has(t.titre) : t.niv === 2 && !(!t.num && SANS_TOC.has(t.titre))
  md = md.replace(/^!table-des-matieres[ \t]*$/m, () => '<nav class="toc">' + toc.filter(dansToc).map((t) =>
    `<div class="toc${t.niv}">${lien(t.id, `${t.num ? `<span class="num">${t.num}</span> ` : ''}${marked.parseInline(t.titre)}`)}</div>`).join('\n') + '</nav>')
  md = md.replace(/^!liste-des-figures[ \t]*$/m, () => '<div class="liste">' + figs.map((f, i) =>
    `<div>${lien(f.id, `Figure ${i + 1}`)} – ${marked.parseInline(f.leg)}</div>`).join('\n') + '</div>')
  md = md.replace(/^!liste-des-tableaux[ \t]*$/m, () => '<div class="liste">' + tabs.map((t, i) =>
    `<div>${lien(t.id, `Tableau ${i + 1}`)} – ${marked.parseInline(t.titre)}</div>`).join('\n') + '</div>')
  md = md.replace(/^!bibliographie[ \t]*$/m, () => '<ol class="biblio">' + ordre.map((c) =>
    `<li id="ref-${c}">${marked.parseInline(ieee(bibCles.get(c)))}</li>`).join('\n') + '</ol>')

  // 7 bis. blocs « :::nom … ::: » (dédicace, encadré, glossaire, résumés, texte arabe de droite à gauche)
  md = md.replace(/^:::(\w+)[ \t]*\n([\s\S]*?)\n:::[ \t]*$/gm, (_, nom, corps) =>
    `<div class="${nom}"${nom === 'arabe' ? ' dir="rtl" lang="ar"' : ''}>\n\n${corps}\n\n</div>`)
  if (/^:::/m.test(md)) err('bloc « ::: » non fermé')

  // 8. Markdown -> HTML, puis formules
  fs.mkdirSync(P('build'), { recursive: true })
  fs.writeFileSync(P('build', 'rapport.md'), md)               // Markdown intermédiaire (diagnostic)
  let html = marked.parse(md, { gfm: true })
  html = html.replace(/@@MATH(\d+)@@/g, (_, i) => maths[+i])
  if (/@@MATH|\?\?[\w:]+\?\?|\{\{|\[cite:|\[@|\*\*/.test(html)) err('marqueur non résolu (ou gras Markdown non rendu) dans le HTML final')

  const nonUtilisees = Object.keys(V).filter((k) => !utilisees.has(k))
  return { html, stats: { chapitres: chapitres.length, figures: labels.fig.length, tableaux: labels.tab.length,
    equations: labels.eq.length, sections: toc.length, references: ordre.length, valeurs_citees: utilisees.size,
    valeurs_non_citees: nonUtilisees.length } }
}

const CSS = `
@page { size: A4; margin: 26mm 25mm 26mm 25mm; }
:root { --encre: #000; --gris: #5a5a5a; --navy: #141e6e; --lien: #1c548c; --boite: #f4f4f4; }
html { font-family: "Times New Roman", "TeX Gyre Termes", Times, serif; font-size: 12pt; color: var(--encre); background: #fff; }
body { margin: 0; line-height: 1.45; text-align: justify; hyphens: auto; }
h1, h2, h3 { font-family: inherit; text-align: left; break-after: avoid; }
h1 { font-size: 26pt; font-weight: 700; margin: 30mm 0 12mm; break-before: page; }
h1 .num { display: block; font-size: 24pt; margin-bottom: 6mm; color: var(--encre); }
h1 .num::before { content: "Chapitre "; }
h2 { font-size: 16pt; color: var(--gris); margin: 16pt 0 7pt; }
h3 { font-size: 13pt; color: var(--gris); margin: 12pt 0 5pt; }
h2 .num, h3 .num { margin-right: 8pt; }
p { margin: 0 0 6pt; orphans: 3; widows: 3; }
a { color: var(--lien); text-decoration: none; }
figure { margin: 10pt 0 12pt; text-align: center; break-inside: avoid; }
figure img { max-width: 100%; }
figcaption, .legende { font-size: 10.5pt; margin-top: 4pt; text-align: center; }
.tableau { margin: 10pt 0 12pt; break-inside: avoid; }
.tableau .legende { margin: 0 0 5pt; }
table { border-collapse: collapse; margin: 0 auto; font-size: 10pt; line-height: 1.3; }
th { border-top: 1.2pt solid var(--encre); border-bottom: 0.6pt solid var(--encre); padding: 3pt 7pt; font-weight: 700; }
td { padding: 2.5pt 7pt; }
tbody tr:last-child td { border-bottom: 1.2pt solid var(--encre); }
.equation { display: flex; align-items: center; justify-content: center; position: relative; margin: 6pt 0; break-inside: avoid; }
.equation .eqn { position: absolute; right: 0; }
.katex { font-size: 1.05em; }
ul, ol { margin: 0 0 6pt; padding-left: 20pt; } li { margin-bottom: 2pt; }
blockquote { margin: 8pt 0; padding: 7pt 11pt; background: var(--boite); break-inside: avoid; }
blockquote p:last-child { margin-bottom: 0; }
code { font-family: "Latin Modern Mono", Consolas, monospace; font-size: 10pt; }
pre { background: #f6f6f6; padding: 6pt 8pt; font-size: 8.8pt; line-height: 1.3; white-space: pre-wrap; break-inside: avoid; text-align: left; }
.toc div, .liste div { margin: 3pt 0; text-align: left; } .toc1 { font-weight: 700; margin-top: 9pt !important; } .toc2 { padding-left: 18pt; }
.toc .num { margin-right: 10pt; }
.biblio { columns: 2; column-gap: 9mm; font-size: 10.5pt; line-height: 1.3; padding-left: 22pt; }
.biblio li { margin-bottom: 4pt; text-align: left; break-inside: avoid; }
/* page de garde, sur le modèle du rapport de référence */
.page-titre { height: 240mm; display: flex; flex-direction: column; align-items: center; text-align: center; line-height: 1.25; }
.page-titre .logos { display: flex; justify-content: space-between; align-items: center; width: 100%; }
.page-titre .logos div { width: 33%; } .page-titre .logos div:first-child { text-align: left; } .page-titre .logos div:last-child { text-align: right; }
.page-titre .filet { width: 100%; border-top: 1pt solid var(--navy); margin: 5mm 0; }
.page-titre .filet.fin { width: 85%; border-top: 0.6pt solid var(--encre); margin: 4mm 0; }
.page-titre .inst { font-size: 13pt; line-height: 1.5; } .page-titre .inst span { font-size: 11.5pt; font-weight: 700; }
.page-titre .type { font-size: 19pt; font-weight: 700; margin-top: 6mm; } .page-titre .formation { font-size: 12.5pt; font-weight: 700; margin-top: 2mm; }
.page-titre .par { margin-top: 7mm; } .page-titre .auteurs { font-size: 19pt; font-weight: 700; margin: 3mm 0 4mm; line-height: 1.3; }
.page-titre .titre { font-size: 23pt; font-weight: 700; color: var(--navy); } .page-titre .sous-titre { font-size: 15pt; font-weight: 700; margin-top: 2mm; }
.page-titre .version { margin-top: 6mm; } .page-titre .encadrant { margin-top: 8mm; } .page-titre .annee { margin-top: auto; }
.dedicace { margin-top: 25mm; text-align: center; font-style: italic; line-height: 1.6; }
.dedicace p { margin-bottom: 14pt; text-align: center; white-space: pre-line; }
.encadre { background: var(--boite); padding: 9pt 14pt; margin: 10pt 8%; font-style: italic; text-align: center; }
.encadre p { margin: 0; text-align: center; }
.glossaire { font-size: 11pt; line-height: 1.35; } .glossaire p { margin-bottom: 4pt; text-align: left; }
.resumes h2, .arabe h2 { color: var(--encre); font-size: 13pt; margin: 8pt 0 4pt; }
.resumes, .arabe { font-size: 11pt; line-height: 1.35; }
.resumes h2:nth-of-type(2) { border-top: 0.6pt solid var(--encre); padding-top: 8pt; margin-top: 12pt; }
.arabe { border-top: 0.6pt solid var(--encre); padding-top: 6pt; margin-top: 12pt; font-family: "Amiri", "Traditional Arabic", "Arial", serif; font-size: 13pt; text-align: justify; }
.arabe h2 { text-align: right; }
.saut { break-after: page; }
`

// résumé arabe en PDF (image de repli du gabarit quand Overleaf compile avec pdfLaTeX), rendu par Chromium
async function resumeArabePdf(sortie) {
  const { html } = construire()
  const bloc = html.match(/<div class="arabe"[\s\S]*?<\/div>/)
  if (!bloc) throw new Error('bloc arabe introuvable')
  const { chromium } = await import('@playwright/test')
  const b = await chromium.launch()
  const page = await b.newPage()
  await page.setContent(`<!doctype html><html lang="ar"><meta charset="utf-8"><style>
    body{margin:0;width:160mm;font-family:Amiri,"Traditional Arabic",Arial,serif;font-size:12.5pt;line-height:1.55;text-align:justify}
    h2{font-size:14pt;margin:0 0 6pt;text-align:right}p{margin:0 0 6pt}</style><body>${bloc[0]}</body></html>`)
  const h = await page.evaluate(() => Math.ceil(document.body.scrollHeight))
  await page.pdf({ path: sortie, width: '160mm', height: `${h + 4}px`, printBackground: true, pageRanges: '1' })
  await b.close()
}

async function main() {
  if (ARGS.has('--captures')) { await captures(); return }
  if (ARGS.has('--latex')) {
    const { genererLatex } = await import('./latex.mjs')
    const r = genererLatex()
    await resumeArabePdf(P('latex', 'figures', 'resume_arabe.pdf'))
    console.log(`  -> latex/ (main.tex, ${r.chapitres} fichiers de chapitres, ${r.references} références IEEE, figures)`)
    return
  }
  const { html, stats } = construire()
  fs.mkdirSync(P('build'), { recursive: true })
  const katexCss = path.join(path.dirname(fileURLToPath(import.meta.resolve('katex'))), 'katex.min.css')
  fs.cpSync(path.join(path.dirname(katexCss), 'fonts'), P('build', 'fonts'), { recursive: true })
  fs.copyFileSync(katexCss, P('build', 'katex.min.css'))
  const doc = `<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Rapport V1 — FMDS et maintenance prédictive</title>
<link rel="stylesheet" href="katex.min.css"><style>${CSS}</style></head><body>${html}</body></html>`
  fs.writeFileSync(P('build', 'rapport.html'), doc)
  const verif = { ...stats, erreurs }
  fs.writeFileSync(P('build', 'verification.json'), JSON.stringify(verif, null, 1))
  if (erreurs.length) {
    console.error(`ÉCHEC : ${erreurs.length} erreur(s)\n - ` + erreurs.join('\n - '))
    process.exit(1)
  }
  console.log(`  -> build/rapport.html (${stats.chapitres} chapitres, ${stats.figures} figures, ${stats.tableaux} tableaux, ` +
    `${stats.equations} équations, ${stats.references} références, ${stats.valeurs_citees} valeurs citées)`)
  if (ARGS.has('--check')) return
  const { chromium } = await import('@playwright/test')
  const b = await chromium.launch()
  const page = await b.newPage()
  const pageErr = []
  page.on('pageerror', (e) => pageErr.push(e.message))
  await page.goto(pathToFileURL(P('build', 'rapport.html')).href, { waitUntil: 'load' })
  await page.evaluate(() => document.fonts.ready)
  const imgKo = await page.evaluate(() => [...document.images].filter((i) => !i.complete || i.naturalWidth === 0).map((i) => i.src))
  if (imgKo.length || pageErr.length) { console.error('ÉCHEC : images non chargées ou erreurs', imgKo, pageErr); process.exit(1) }
  await page.pdf({
    path: SORTIE, format: 'A4', printBackground: true, preferCSSPageSize: true, displayHeaderFooter: true,
    headerTemplate: `<div style="font-size:8.5pt;color:#5a5a5a;width:100%;margin:0 25mm;padding-bottom:2pt;border-bottom:0.5pt solid #5a5a5a;font-family:'Times New Roman',serif;display:flex;justify-content:space-between"><span>${META_ENTETE}</span><span>C-MAPSS FD001 · Version 1</span></div>`,
    footerTemplate: `<div style="font-size:10pt;width:100%;text-align:center;font-family:'Times New Roman',serif"><span class="pageNumber"></span></div>`,
  })
  await b.close()
  const pdf = fs.readFileSync(SORTIE, 'latin1')
  const pages = (pdf.match(/\/Type\s*\/Page[^s]/g) || []).length
  verif.pages = pages
  fs.writeFileSync(P('build', 'verification.json'), JSON.stringify(verif, null, 1))
  console.log(`  -> ${path.relative(ICI, SORTIE)} (${pages} pages)`)
}

main().catch((e) => { console.error(e); process.exit(1) })
