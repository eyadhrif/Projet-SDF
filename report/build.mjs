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
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const ICI = path.dirname(fileURLToPath(import.meta.url))
const P = (...a) => path.join(ICI, ...a)
const ARGS = new Set(process.argv.slice(2))
const PDF_NOM = 'Rapport_V1_FMDS_Eya_Salma.pdf'
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
  md = md.replace(/^!table-des-matieres[ \t]*$/m, () => '<nav class="toc">' + toc.filter((t) => t.niv <= 2).map((t) =>
    `<div class="toc${t.niv}">${lien(t.id, `${t.num ? `<span class="num">${t.num}</span> ` : ''}${marked.parseInline(t.titre)}`)}</div>`).join('\n') + '</nav>')
  md = md.replace(/^!liste-des-figures[ \t]*$/m, () => '<div class="liste">' + figs.map((f, i) =>
    `<div>${lien(f.id, `Figure ${i + 1}`)} – ${marked.parseInline(f.leg)}</div>`).join('\n') + '</div>')
  md = md.replace(/^!liste-des-tableaux[ \t]*$/m, () => '<div class="liste">' + tabs.map((t, i) =>
    `<div>${lien(t.id, `Tableau ${i + 1}`)} – ${marked.parseInline(t.titre)}</div>`).join('\n') + '</div>')
  md = md.replace(/^!bibliographie[ \t]*$/m, () => '<ol class="biblio">' + ordre.map((c) =>
    `<li id="ref-${c}">${marked.parseInline(bibCles.get(c).texte)}</li>`).join('\n') + '</ol>')

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
@page { size: A4; margin: 22mm 20mm 22mm 22mm; }
:root { --encre: #111; --gris: #555; --bleu: #1f4e8c; --filet: #c9c9c9; }
html { font-family: Cambria, "Times New Roman", Georgia, serif; font-size: 10.5pt; color: var(--encre); background: #fff; }
body { margin: 0; line-height: 1.42; text-align: justify; hyphens: auto; }
h1, h2, h3 { font-family: Calibri, "Segoe UI", Arial, sans-serif; color: var(--bleu); text-align: left; break-after: avoid; }
h1.chapitre { font-size: 19pt; margin: 0 0 14pt; padding-bottom: 6pt; border-bottom: 1.5pt solid var(--bleu); break-before: page; }
h2 { font-size: 13pt; margin: 16pt 0 6pt; } h3 { font-size: 11pt; margin: 12pt 0 4pt; }
.num { color: var(--gris); font-weight: 600; margin-right: 4pt; }
p { margin: 0 0 7pt; orphans: 3; widows: 3; }
a { color: var(--bleu); text-decoration: none; }
figure { margin: 10pt 0 12pt; text-align: center; break-inside: avoid; }
figure img { max-width: 100%; }
figcaption, .legende { font-size: 9pt; color: var(--gris); margin-top: 4pt; text-align: center; }
.legende { margin: 0 0 4pt; }
.tableau { margin: 10pt 0 12pt; break-inside: avoid; }
table { border-collapse: collapse; margin: 0 auto; font-size: 8.8pt; font-family: Calibri, "Segoe UI", Arial, sans-serif; }
th { border-top: 1.2pt solid var(--encre); border-bottom: 0.6pt solid var(--encre); padding: 3pt 7pt; font-weight: 600; }
td { padding: 2.2pt 7pt; border-bottom: 0.3pt solid #e3e3e3; }
tbody tr:last-child td { border-bottom: 1.2pt solid var(--encre); }
.equation { display: flex; align-items: center; justify-content: center; position: relative; margin: 6pt 0; break-inside: avoid; }
.equation .eqn { position: absolute; right: 0; color: var(--gris); }
.katex { font-size: 1.05em; }
ul, ol { margin: 0 0 7pt; padding-left: 18pt; } li { margin-bottom: 2pt; }
blockquote { margin: 8pt 0; padding: 6pt 10pt; border-left: 3pt solid var(--bleu); background: #f3f6fa; break-inside: avoid; }
blockquote p:last-child { margin-bottom: 0; }
code { font-family: Consolas, monospace; font-size: 8.8pt; background: #f2f2f2; padding: 0 2pt; }
pre { background: #f6f6f6; padding: 6pt 8pt; font-size: 8.3pt; line-height: 1.3; white-space: pre-wrap; break-inside: avoid; text-align: left; }
pre code { background: none; padding: 0; }
.toc div, .liste div { margin: 2pt 0; text-align: left; } .toc1 { font-weight: 600; margin-top: 6pt !important; } .toc2 { padding-left: 16pt; }
.biblio li { margin-bottom: 4pt; text-align: left; font-size: 9.5pt; }
.page-titre { height: 245mm; display: flex; flex-direction: column; justify-content: space-between; text-align: center; }
.page-titre .haut { font-family: Calibri, Arial, sans-serif; font-size: 11pt; color: var(--gris); line-height: 1.5; }
.page-titre h1.titre { font-family: Calibri, Arial, sans-serif; font-size: 24pt; color: var(--bleu); border: none; margin: 0 0 10pt; }
.page-titre .sous-titre { font-size: 13pt; color: var(--gris); }
.page-titre .auteurs { font-size: 12pt; line-height: 1.7; }
.saut { break-after: page; }
.encadre { border: 0.8pt solid var(--filet); padding: 8pt 10pt; margin: 8pt 0; background: #fafafa; break-inside: avoid; }
`

async function main() {
  if (ARGS.has('--captures')) { await captures(); return }
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
    headerTemplate: '<div style="font-size:7.5pt;color:#777;width:100%;padding:0 20mm 0 22mm;font-family:Calibri,Arial;text-align:right">FMDS et maintenance prédictive — C-MAPSS FD001 · Version 1</div>',
    footerTemplate: '<div style="font-size:8pt;color:#777;width:100%;text-align:center;font-family:Calibri,Arial"><span class="pageNumber"></span> / <span class="totalPages"></span></div>',
  })
  await b.close()
  const pdf = fs.readFileSync(SORTIE, 'latin1')
  const pages = (pdf.match(/\/Type\s*\/Page[^s]/g) || []).length
  verif.pages = pages
  fs.writeFileSync(P('build', 'verification.json'), JSON.stringify(verif, null, 1))
  console.log(`  -> ${path.relative(ICI, SORTIE)} (${pages} pages)`)
}

main().catch((e) => { console.error(e); process.exit(1) })
