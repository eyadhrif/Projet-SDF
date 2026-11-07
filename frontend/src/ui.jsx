import React, { useEffect, useState } from 'react'
import { get } from './api.js'

export const C = {
  ink: '#0f172a', muted: '#64748b', grid: '#eef0f3', blue: '#1d4ed8', teal: '#0e7c86',
  orange: '#c2410c', red: '#dc2626', amber: '#d97706', green: '#15803d', gray: '#94a3b8',
  violet: '#7c3aed',
}

export function useData(path) {
  const [state, set] = useState({ data: null, error: null })
  useEffect(() => {
    let live = true
    set((s) => ({ ...s, data: null }))
    get(path).then((d) => live && set({ data: d, error: null }))
      .catch((e) => live && set({ data: null, error: e.message }))
    return () => { live = false }
  }, [path])
  return state
}

export function Guard({ state, children }) {
  if (state.error) return <div className="err">Erreur de chargement : {state.error}</div>
  if (!state.data) return <div className="loading">Chargement…</div>
  return children(state.data)
}

export const Card = ({ title, sub, span = 6, children, right }) => (
  <div className={`card s${span}`}>
    {(title || right) && (
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div><h3>{title}</h3>{sub && <div className="cs">{sub}</div>}</div>{right}
      </div>
    )}
    {children}
  </div>
)

export const Kpi = ({ label, value, unit, hint, span = 3, color }) => (
  <div className={`card kpi s${span}`}>
    <div className="l">{label}</div>
    <div className="v" style={color ? { color } : null}>{value}{unit && <small>{unit}</small>}</div>
    {hint && <div className="h">{hint}</div>}
  </div>
)

export const Section = ({ children, owner }) => (
  <div className="section">{children}
    {owner && owner.split('+').map((o) => (
      <span key={o} className={`owner ${o.trim().toLowerCase()}`}>{o.trim()}</span>))}
  </div>
)

export const Param = ({ l, v }) => <div className="param"><div className="l">{l}</div><div className="v">{v}</div></div>

export const fmt = (x, d = 2) => (x === null || x === undefined ? '—' : Number(x).toLocaleString('fr-FR', {
  minimumFractionDigits: d, maximumFractionDigits: d }))

export const tip = {
  contentStyle: { fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb', boxShadow: '0 4px 12px rgba(0,0,0,.06)' },
  labelStyle: { fontWeight: 600, color: '#0f172a' },
}
export const axis = { stroke: '#cbd5e1', tickLine: false }
export const tticks = [0, 50, 100, 150, 200, 250, 300, 350]
