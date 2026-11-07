// Couche d'accès aux données : API FastAPI (mode normal) ou JSON intégrés (mode static)
const STATIC = import.meta.env.MODE === 'static'
const files = STATIC ? import.meta.glob('../../backend/results/*.json', { eager: true, import: 'default' }) : {}
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
