// Couche d'accès aux données : API FastAPI (mode normal) ou JSON intégrés (mode static)
const STATIC = import.meta.env.MODE === 'static'
// Seuls les 4 JSON affichés sont intégrés : run_info.json (date d'exécution) et dataset.json
// rendraient sinon la version autonome différente à chaque exécution de run_all.py
const files = STATIC ? import.meta.glob('../../backend/results/{fmds,health,rul,engines}.json',
  { eager: true, import: 'default' }) : {}
const pick = (n) => files[`../../backend/results/${n}.json`]

export async function get(path) {
  if (STATIC) {
    if (path.startsWith('/engines/')) return pick('engines')[path.split('/')[2]]
    if (path === '/fleet') return pick('rul').table
    return pick(path.slice(1))
  }
  const r = await fetch(`/api${path}`)
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`)
  return r.json()
}
