import React, { useState } from 'react'
import Overview from './pages/Overview.jsx'
import Fiabilite from './pages/Fiabilite.jsx'
import Monitoring from './pages/Monitoring.jsx'
import Rul from './pages/Rul.jsx'

const PAGES = [
  { id: 'overview', label: "Vue d'ensemble", C: Overview },
  { id: 'fiab', label: 'Fiabilité & FMDS', C: Fiabilite },
  { id: 'mon', label: 'Monitoring santé', C: Monitoring },
  { id: 'rul', label: 'Durée de vie résiduelle', C: Rul },
]

export default function App() {
  const [page, setPage] = useState(() => (location.hash.slice(1) || 'overview'))
  const [engine, setEngine] = useState(31)
  const go = (id, eng) => { setPage(id); if (eng) setEngine(eng); location.hash = id; window.scrollTo(0, 0) }
  const P = (PAGES.find((p) => p.id === page) || PAGES[0]).C
  return (
    <div className="app">
      <aside className="side">
        <div className="brand"><small>Projet SdF · ENSIT</small>FMDS & Maintenance Prédictive</div>
        <div className="sub">Turboréacteurs NASA C-MAPSS · FD001</div>
        {PAGES.map((p, i) => (
          <button key={p.id} className={`nav ${page === p.id ? 'on' : ''}`} onClick={() => go(p.id)}>
            <span className="ix">{i + 1}</span>{p.label}
          </button>
        ))}
        <div className="foot">
          <b>Eya DHRIF</b> & <b>Salma MOUEDDEB</b><br />
          Encadrant : M. Fayçal Ben Hmida<br />
          GMAM 3 · Novembre 2026
        </div>
      </aside>
      <main><P go={go} engine={engine} setEngine={setEngine} /></main>
    </div>
  )
}
