import React from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts'
import { useData, Guard, Card, Kpi, Section, fmt, tip, axis, C } from '../ui.jsx'

const STATE_COL = { Normal: C.green, Surveillance: C.amber, Critique: C.red }

export default function Overview({ go }) {
  const f = useData('/fmds'), h = useData('/health'), r = useData('/rul')
  return (
    <Guard state={f}>{(fm) => <Guard state={h}>{(he) => <Guard state={r}>{(ru) => {
      const fi = fm.fiabilite, ds = fm.dataset
      const bins = []
      for (let b = 120; b < 380; b += 20) bins.push({ b: `${b}`, n: ds.lifetimes.filter((l) => l.status === 1 && l.time >= b && l.time < b + 20).length })
      const states = ['Normal', 'Surveillance', 'Critique'].map((s) => ({ name: s, value: he.fleet_states[s] || 0 }))
      const urgent = [...ru.table].sort((a, b) => a.lstm - b.lstm).slice(0, 8)
      return (<>
        <div className="head">
          <div>
            <h1>Vue d'ensemble</h1>
            <p className="lede">Estimation des indices FMDS et maintenance prédictive d'une flotte de turboréacteurs
              simulés (NASA C-MAPSS, sous-ensemble FD001 : une condition opératoire, un mode de défaillance — dégradation
              du compresseur haute pression).</p>
          </div>
          <span className="tag">{ds.train_units} moteurs run-to-failure · {ds.test_units} moteurs en service · 21 capteurs</span>
        </div>

        <div className="grid">
          <Kpi label="MTTF (Weibull 3P)" value={fmt(fi.mttf, 1)} unit="cycles" hint={`B50 : ${fmt(fi.b50, 1)} · KM : ${fmt(fi.mttf_km, 1)} cycles`} />
          <Kpi label="Disponibilité intrinsèque" value={fmt(fm.disponibilite.A * 100, 2)} unit="%"
            hint={`MTTR ${fmt(fm.maintenabilite.mttr_h, 1)} h`} />
          <Kpi label="Paramètre de forme β" value={fmt(fi.w3.beta, 2)} hint={`Taux de défaillance ${fi.failure_mode}`} />
          <Kpi label="RMSE RUL — meilleur modèle" value={fmt(ru.metrics.lstm.rmse, 1)} unit="cycles"
            hint={`LSTM · dégradation : ${fmt(ru.metrics.deg.rmse, 1)}`} />

          <Card title="Distribution des durées de vie" sub="100 moteurs d'entraînement suivis jusqu'à la défaillance" span={5}>
            <ResponsiveContainer width="100%" height={230}>
              <BarChart data={bins} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <CartesianGrid stroke={C.grid} vertical={false} />
                <XAxis dataKey="b" {...axis} label={{ value: 'cycles', position: 'insideBottomRight', offset: -2, fontSize: 11 }} />
                <YAxis {...axis} allowDecimals={false} />
                <Tooltip {...tip} formatter={(v) => [v, 'moteurs']} labelFormatter={(l) => `${l}–${+l + 20} cycles`} />
                <Bar dataKey="n" fill={C.blue} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <div className="note">Aucune défaillance avant <b>{ds.life_min} cycles</b> : c'est ce qui justifie une loi de
              Weibull à 3 paramètres (seuil γ ≈ {fmt(fi.w3.gamma, 0)} cycles).</div>
          </Card>

          <Card title="État de santé de la flotte en service" sub="Classification au dernier cycle observé" span={3}>
            <ResponsiveContainer width="100%" height={190}>
              <PieChart>
                <Pie data={states} dataKey="value" innerRadius={50} outerRadius={78} paddingAngle={2} stroke="none">
                  {states.map((s) => <Cell key={s.name} fill={STATE_COL[s.name]} />)}
                </Pie>
                <Tooltip {...tip} />
              </PieChart>
            </ResponsiveContainer>
            <div className="legend-inline" style={{ justifyContent: 'center' }}>
              {states.map((s) => <span key={s.name}><i style={{ background: STATE_COL[s.name] }} />{s.name} · {s.value}</span>)}
            </div>
          </Card>

          <Card title="Priorités d'intervention" sub="Moteurs au RUL prédit le plus faible (LSTM)" span={4}>
            <table>
              <thead><tr><th>Moteur</th><th className="num">RUL LSTM</th><th className="num">RUL dégr.</th><th>État</th></tr></thead>
              <tbody>{urgent.map((u) => (
                <tr key={u.unit} className="click" onClick={() => go('rul', u.unit)}>
                  <td>#{u.unit}</td><td className="num">{fmt(u.lstm, 0)}</td><td className="num">{fmt(u.deg, 0)}</td>
                  <td><span className={`pill ${u.state}`}>{u.state}</span></td></tr>))}
              </tbody>
            </table>
          </Card>
        </div>

        <Section>Démarche</Section>
        <div className="grid">
          {[
            ['1 · Fiabilité', 'Kaplan-Meier avec IC 95 %, Nelson-Aalen, Weibull par MCO et par MV, tests KS et AIC, avec censure à droite des moteurs en service.', 'fiab', 'Eya'],
            ['2 · Maintenabilité & disponibilité', 'Temps de réparation log-normaux, MTTR, disponibilité intrinsèque et A(t), âge optimal de remplacement préventif.', 'fiab', 'Salma'],
            ['3 · Détection', `Sélection de ${he.selected.length} capteurs pronostiques, indicateur de santé, classification normal / critique (AUC ${fmt(he.classifiers[he.best].test.auc, 3)}).`, 'mon', 'Salma + Eya'],
            ['4 · Pronostic RUL', `Modèle de dégradation bayésien (Eya) et LSTM (Salma) comparés sur les 100 moteurs de test NASA.`, 'rul', 'Eya + Salma'],
          ].map(([t, d, p, o]) => (
            <div key={t} className="card s3 click" style={{ cursor: 'pointer' }} onClick={() => go(p)}>
              <h3>{t}</h3><div className="cs" style={{ marginBottom: 8 }}>{d}</div>
              {o.split('+').map((x) => <span key={x} className={`owner ${x.trim().toLowerCase()}`} style={{ marginRight: 6 }}>{x.trim()}</span>)}
            </div>))}
        </div>
      </>)
    }}</Guard>}</Guard>}</Guard>
  )
}
