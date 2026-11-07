// WEB-02 — Tests du dashboard React (Phase 0, §0.8).
// Deux cibles : le serveur FastAPI (frontend/dist) et la version autonome dashboard_autonome.html en file://.
import { test, expect } from '@playwright/test'
import { readFileSync, mkdirSync } from 'node:fs'
import { fileURLToPath, pathToFileURL } from 'node:url'
import path from 'node:path'

const ICI = path.dirname(fileURLToPath(import.meta.url))
const RACINE = path.resolve(ICI, '..', '..')
const RES = path.join(RACINE, 'backend', 'results')
const CAPTURES = path.join(ICI, 'captures')
mkdirSync(CAPTURES, { recursive: true })

const json = (n) => JSON.parse(readFileSync(path.join(RES, `${n}.json`), 'utf-8'))
const FMDS = json('fmds'), HEALTH = json('health'), RUL = json('rul')

// même formatage que fmt() dans src/ui.jsx
const fmt = (x, d = 2) => Number(x).toLocaleString('fr-FR', { minimumFractionDigits: d, maximumFractionDigits: d })

const CIBLES = [
  { nom: 'serveur', url: (h) => `/#${h}` },
  { nom: 'autonome', url: (h) => `${pathToFileURL(path.join(RACINE, 'dashboard_autonome.html')).href}#${h}` },
]

// id de page, titre h1, nombre de graphiques attendus
const PAGES = [
  { id: 'overview', h1: "Vue d'ensemble", graphiques: 2 },
  { id: 'fiab', h1: 'Fiabilité, maintenabilité, disponibilité', graphiques: 9 },
  { id: 'mon', h1: "Monitoring de l'état de santé", graphiques: 6 },
  { id: 'rul', h1: 'Estimation de la durée de vie résiduelle (RUL)', graphiques: 6 },
]

/** Ouvre une page et enregistre toutes les erreurs de console et exceptions JavaScript. */
async function ouvrir(page, cible, id) {
  const erreurs = []
  page.on('console', (m) => { if (m.type() === 'error') erreurs.push(m.text()) })
  page.on('pageerror', (e) => erreurs.push(e.message))
  // chargement complet : un simple changement de hash ne recharge pas l'application
  await page.goto('about:blank')
  await page.goto(cible.url(id))
  await expect(page.locator('main h1')).toBeVisible()
  await expect(page.locator('.loading')).toHaveCount(0)
  return erreurs
}

const kpi = (page, label) => page.locator('.kpi', { has: page.locator('.l', { hasText: label }) }).locator('.v')
const kpiIndication = (page, label) => page.locator('.kpi', { has: page.locator('.l', { hasText: label }) }).locator('.h')
const carte = (page, titre) => page.locator('.card', { has: page.locator('h3', { hasText: titre }) })

for (const cible of CIBLES) {
  test.describe(`dashboard (${cible.nom})`, () => {
    // ----------------------------------------------------------- chargement des 4 pages
    for (const p of PAGES) {
      test(`page « ${p.id} » : chargement, graphiques, KPI, sans erreur`, async ({ page }, info) => {
        const erreurs = await ouvrir(page, cible, p.id)
        await expect(page.locator('main h1')).toHaveText(p.h1)
        await expect(page.locator('.err')).toHaveCount(0)

        // chaque graphique est rendu avec des DONNÉES tracées (pas seulement axes et grille) ;
        // l'attente couvre les animations (le camembert n'apparaît qu'après ≈ 1,5 s)
        const graphiques = page.locator('.recharts-wrapper > svg.recharts-surface')
        await expect(graphiques).toHaveCount(p.graphiques)
        const MARQUES = '.recharts-line-curve, .recharts-bar-rectangle path, .recharts-area-area, '
          + '.recharts-symbols, .recharts-pie-sector path, .recharts-scatter-symbol'
        for (const svg of await graphiques.all()) {
          await expect(svg.locator(MARQUES).first()).toBeAttached({ timeout: 5000 })
          const b = await svg.boundingBox()
          expect(b.width).toBeGreaterThan(50)
        }
        if (p.id === 'overview') await expect(page.locator('.recharts-pie-sector path')).toHaveCount(3)

        // aucun KPI ni paramètre ne vaut « — »
        for (const v of await page.locator('.kpi .v, .param .v').allTextContents()) {
          expect(v.trim()).not.toBe('')
          expect(v).not.toContain('—')
        }

        await page.screenshot({ path: path.join(CAPTURES, `${cible.nom}-${info.project.name}-${p.id}.png`), fullPage: true })
        expect(erreurs, 'erreurs dans la console').toEqual([])
      })

      test(`page « ${p.id} » : pas de défilement horizontal (D7)`, async ({ page }) => {
        // D7 (corrigé) : colonne minmax(0, 1fr) et badge .tag autorisé à passer à la ligne
        await ouvrir(page, cible, p.id)
        const deborde = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
        expect(deborde, 'débordement horizontal (px)').toBeLessThanOrEqual(1)
      })
    }

    // ----------------------------------------------------------- KPI = JSON
    test('KPI de la vue d\'ensemble = JSON', async ({ page }) => {
      await ouvrir(page, cible, 'overview')
      const fi = FMDS.fiabilite
      await expect(kpi(page, 'MTTF')).toContainText(fmt(fi.mttf, 1))
      await expect(kpi(page, 'Disponibilité')).toContainText(fmt(FMDS.disponibilite.A * 100, 2))
      await expect(kpi(page, 'forme β')).toContainText(fmt(fi.w3.beta, 2))
      await expect(kpi(page, 'RMSE')).toContainText(fmt(RUL.metrics.lstm.rmse, 1))
      // valeurs attendues en clair (section 1 du prompt maître)
      await expect(kpi(page, 'MTTF')).toContainText('206,3')
      await expect(kpiIndication(page, 'MTTF')).toContainText(`B50 : ${fmt(fi.b50, 1)}`)
      await expect(kpi(page, 'Disponibilité')).toContainText('95,98')
      await expect(kpi(page, 'forme β')).toContainText('1,83')
    })

    test('KPI des pages Fiabilité et RUL = JSON', async ({ page }) => {
      await ouvrir(page, cible, 'fiab')
      const fi = FMDS.fiabilite
      await expect(kpi(page, 'MTTF')).toContainText(fmt(fi.mttf, 1))
      await expect(kpi(page, 'Médiane KM')).toContainText(fmt(fi.median_km, 0))
      await expect(kpi(page, 'B10')).toContainText(fmt(fi.b10, 0))
      await expect(kpiIndication(page, 'B10')).toContainText(`B50 = ${fmt(fi.b50, 0)}`)
      await expect(page.locator('.param', { hasText: 'B50 (médiane)' })).toContainText(fmt(fi.b50, 1))
      await expect(page.locator('.param', { hasText: 'B50 (médiane)' })).toContainText('199,9')
      await expect(kpi(page, 'Disponibilité A')).toContainText(fmt(FMDS.disponibilite.A * 100, 2))

      await ouvrir(page, cible, 'rul')
      await expect(kpi(page, 'RMSE · LSTM')).toContainText(fmt(RUL.metrics.lstm.rmse, 2))
      await expect(kpi(page, 'RMSE · Dégradation')).toContainText(fmt(RUL.metrics.deg.rmse, 2))
      await expect(kpi(page, 'Score NASA')).toContainText(fmt(RUL.metrics.lstm.score, 0))
      await expect(kpi(page, 'Couverture')).toContainText(fmt(RUL.deg_info.coverage_10_90, 0))
      const cal = carte(page, 'Calibration du modèle de dégradation')
      for (const c of RUL.deg_info.calibration) await expect(cal).toContainText(`${fmt(c.couverture, 0)} %`)
      await expect(cal.locator('tbody tr')).toHaveCount(6)
    })

    test('tableau de classification = JSON', async ({ page }) => {
      await ouvrir(page, cible, 'mon')
      const t = carte(page, 'Performances')
      for (const m of Object.values(HEALTH.classifiers)) {
        await expect(t).toContainText(fmt(m.test.auc, 3))
        await expect(t).toContainText(fmt(m.test.recall, 3))
      }
    })

    // ----------------------------------------------------------- interactions
    test('navigation par la barre latérale et par l\'adresse', async ({ page }) => {
      await ouvrir(page, cible, 'overview')
      for (const [bouton, p] of [['Fiabilité & FMDS', PAGES[1]], ['Monitoring santé', PAGES[2]],
        ['Durée de vie résiduelle', PAGES[3]], ["Vue d'ensemble", PAGES[0]]]) {
        await page.locator('button.nav', { hasText: bouton }).click()
        await expect(page.locator('main h1')).toHaveText(p.h1)
        expect(new URL(page.url()).hash).toBe(`#${p.id}`)
      }
      await ouvrir(page, cible, 'inconnue')
      await expect(page.locator('main h1')).toHaveText(PAGES[0].h1)          // page par défaut
    })

    test("bouton « Précédent » et changement d'adresse (D6)", async ({ page }) => {
      // D6 (corrigé) : App.jsx écoute hashchange ; « Précédent » et la saisie d'adresse changent la page
      await ouvrir(page, cible, 'overview')
      await page.locator('button.nav', { hasText: 'Fiabilité & FMDS' }).click()
      await expect(page.locator('main h1')).toHaveText(PAGES[1].h1)
      await page.goBack()
      await expect(page.locator('main h1')).toHaveText(PAGES[0].h1, { timeout: 3000 })
      await page.goForward()
      await expect(page.locator('main h1')).toHaveText(PAGES[1].h1)
      await page.evaluate(() => { location.hash = 'rul' })                    // saisie d'adresse
      await expect(page.locator('main h1')).toHaveText(PAGES[3].h1)
    })

    test('cartes « Démarche » et priorités d\'intervention', async ({ page }) => {
      await ouvrir(page, cible, 'overview')
      await page.locator('.card.click', { hasText: '4 · Pronostic RUL' }).click()
      await expect(page.locator('main h1')).toHaveText(PAGES[3].h1)

      await ouvrir(page, cible, 'overview')
      const urgent = [...RUL.table].sort((a, b) => a.lstm - b.lstm)[0]
      const ligne = carte(page, "Priorités d'intervention").locator('tbody tr').first()
      await expect(ligne.locator('td').first()).toHaveText(`#${urgent.unit}`)
      await ligne.click()
      await expect(page.locator('main h1')).toHaveText(PAGES[3].h1)
      await expect(page.locator('h3', { hasText: `Moteur de test n°${urgent.unit}` })).toBeVisible()
    })

    test('sélecteur de moteur (Monitoring)', async ({ page }) => {
      await ouvrir(page, cible, 'mon')
      const c = page.locator('.card', { has: page.locator('h3', { hasText: 'Suivi du moteur de test' }) })
      await c.locator('select').selectOption('49')
      await expect(c.locator('h3')).toHaveText('Suivi du moteur de test n°49')
      await expect(c.locator('.recharts-wrapper')).toHaveCount(1)
      await expect(page.locator('.loading')).toHaveCount(0)
    })

    test('sélecteur de moteur (RUL)', async ({ page }) => {
      await ouvrir(page, cible, 'rul')
      const row = RUL.table.find((r) => r.unit === 12)
      const c = carte(page, 'Moteur de test n°')
      await c.locator('select').selectOption('12')
      await expect(c.locator('h3')).toHaveText('Moteur de test n°12')
      await expect(c.locator('.cs').first()).toContainText(`${row.cycles} cycles observés · RUL réel ${row.true}`)
      await expect(c.locator('.recharts-wrapper')).toHaveCount(2)
    })

    test('tri du tableau de flotte et clic sur une ligne', async ({ page }) => {
      await ouvrir(page, cible, 'rul')
      const c = carte(page, 'Tableau de flotte')
      const premier = () => c.locator('tbody tr').first().locator('td').first()
      for (const cle of ['lstm', 'deg', 'unit']) {
        await c.locator('select').selectOption(cle)
        const attendu = [...RUL.table].sort((a, b) => a[cle] - b[cle])[0].unit
        await expect(premier()).toHaveText(String(attendu))
        await expect(c.locator('tbody tr')).toHaveCount(100)
      }
      await c.locator('tbody tr').filter({ has: page.locator('td:first-child', { hasText: /^77$/ }) }).click()
      await expect(page.locator('h3', { hasText: 'Moteur de test n°77' })).toBeVisible()
    })
  })
}
