// Tests du dashboard (Phase 0, §0.8) : npx playwright test
// Le serveur FastAPI est démarré automatiquement sur le port 8001 (frontend/dist + backend/results).
import { defineConfig } from '@playwright/test'
import { existsSync } from 'node:fs'

const VENV = process.platform === 'win32' ? '../.venv/Scripts/python.exe' : '../.venv/bin/python'
const PY = existsSync(VENV) ? VENV : 'python'
const PORT = 8001

export default defineConfig({
  testDir: './tests',
  outputDir: './tests/resultats',
  timeout: 60_000,
  fullyParallel: false,
  workers: 2,
  reporter: [['list'], ['junit', { outputFile: '../tests/junit_playwright.xml' }]],
  use: { baseURL: `http://127.0.0.1:${PORT}` },
  webServer: {
    command: `"${PY}" -m uvicorn api.main:app --port ${PORT}`,
    cwd: '../backend',
    url: `http://127.0.0.1:${PORT}/api/fmds`,
    reuseExistingServer: false,
    timeout: 60_000,
  },
  projects: [
    { name: 'bureau-1440', use: { viewport: { width: 1440, height: 900 } } },
    { name: 'mobile-390', use: { viewport: { width: 390, height: 844 } } },
  ],
})
