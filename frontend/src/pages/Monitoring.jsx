import React from 'react'
import {
  ComposedChart, LineChart, Line, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine, Cell,
} from 'recharts'
import { useData, Guard, Card, Section, Param, fmt, tip, axis, C } from '../ui.jsx'

const PAL = ['#1d4ed8', '#0e7c86', '#c2410c', '#7c3aed', '#15803d', '#be185d', '#0369a1', '#a16207', '#4d7c0f', '#475569']

function EngineHealth({ unit, threshold }) {
  const s = useData(`/engines/${unit}`)
  return <Guard state={s}>{(e) => (
    <ResponsiveContainer width="100%" height={260}>
      <ComposedChart data={e.series} margin={{ top: 8, right: 30, left: -10, bottom: 8 }}>
        <CartesianGrid stroke={C.grid} />
        <XAxis dataKey="c" type="number" domain={['dataMin', 'dataMax']} {...axis}
          label={{ value: 'cycle', position: 'insideBottomRight', offset: -4, fontSize: 11 }} />
        <YAxis yAxisId="hi" domain={[-0.2, 1.2]} {...axis} tickFormatter={(v) => v.toFixed(1)} />
        <YAxis yAxisId="p" orientation="right" domain={[0, 1]} {...axis} tickFormatter={(v) => `${v * 100}%`} />
        <Tooltip {...tip} formatter={(v, n) => [n.startsWith('P') ? `${fmt(v * 100, 1)} %` : fmt(v, 3), n]} labelFormatter={(l) => `Cycle ${l}`} />
        <Legend verticalAlign="top" height={24} iconType="plainline" />
        <Line yAxisId="hi" dataKey="hr" stroke="#cbd5e1" dot={false} name="HI brut" isAnimationActive={false} />
        <Line yAxisId="hi" dataKey="hi" stroke={C.blue} strokeWidth={2} dot={false} name="HI lissé" isAnimationActive={false} />
        <Area yAxisId="p" dataKey="p" stroke={C.red} fill={C.red} fillOpacity={0.1} name="P(critique)" isAnimationActive={false} />
        <ReferenceLine yAxisId="hi" y={threshold} stroke={C.ink} strokeDasharray="4 4" label={{ value: 'seuil défaillance', fontSize: 11, position: 'insideBottomLeft' }} />
        <ReferenceLine yAxisId="p" y={0.5} stroke={C.red} strokeDasharray="2 3" />
      </ComposedChart>
    </ResponsiveContainer>)}</Guard>
}

function CM({ m }) {
  const { tn, fp, fn, tp } = m.cm, n = tn + fp + fn + tp
  const cell = (v, good) => (
    <div className="c" style={{ background: good ? `rgba(21,128,61,${0.08 + 0.5 * v / n})` : `rgba(220,38,38,${0.06 + 2 * v / n})` }}>
      {v.toLocaleString('fr-FR')}<small>{fmt(100 * v / n, 1)} %</small></div>)
  return (
    <div className="cm">
      <div className="hd" /><div className="hd">Prédit normal</div><div className="hd">Prédit critique</div>
      <div className="hd" style={{ alignSelf: 'center' }}>Réel normal</div>{cell(tn, true)}{cell(fp, false)}
      <div className="hd" style={{ alignSelf: 'center' }}>Réel critique</div>{cell(fn, false)}{cell(tp, true)}
    </div>)
}

export default function Monitoring({ engine, setEngine }) {
  const h = useData('/health'), r = useData('/rul')
  return <Guard state={h}>{(he) => <Guard state={r}>{(ru) => {
    const names = Object.keys(he.classifiers)
    const best = he.classifiers[he.best]
    const rawZ = (() => {
      const keys = ['s2', 's4', 's7', 's11', 's12', 's15']
      const st = Object.fromEntries(keys.map((k) => {
        const v = he.raw_sensors.map((p) => p[k]); const m = v.reduce((a, b) => a + b) / v.length
        const sd = Math.sqrt(v.reduce((a, b) => a + (b - m) ** 2, 0) / v.length); return [k, [m, sd]]
      }))
      return { keys, data: he.raw_sensors.map((p) => ({ c: p.c, ...Object.fromEntries(keys.map((k) => [k, (p[k] - st[k][0]) / st[k][1]])) })) }
    })()
    const rocData = names.map((n) => he.classifiers[n].test.roc)
    return (<>
      <div className="head">
        <div><h1>Monitoring de l'état de santé</h1>
          <p className="lede">Sélection des capteurs pronostiques, construction d'un indicateur de santé (HI) puis
            détection des moteurs en état <b>critique</b> (RUL ≤ {he.critical_rul} cycles, soit la fenêtre d'intervention).</p></div>
        <span className="tag">{he.selected.length} capteurs retenus · {he.n_features} features</span>
      </div>

      <Section owner="Salma">PDM-01 · Feature engineering & indicateur de santé</Section>
      <div className="grid">
        <Card title="Sélection des capteurs" span={5}
          sub={`Tendance (corrélation avec le temps) ; seuil |ρ| ≥ 0,5. Capteurs constants écartés : ${he.dropped.join(', ')}`}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={he.sensor_ranking} layout="vertical" margin={{ top: 0, right: 16, left: 4, bottom: 0 }}>
              <CartesianGrid stroke={C.grid} horizontal={false} />
              <XAxis type="number" domain={[-1, 1]} {...axis} />
              <YAxis type="category" dataKey="sensor" width={34} {...axis} />
              <Tooltip {...tip} formatter={(v, n, p) => [fmt(v, 3), n === 'trend' ? 'tendance' : 'monotonie']}
                labelFormatter={(l) => he.sensor_info[l]} />
              <ReferenceLine x={0.5} stroke={C.gray} strokeDasharray="3 3" /><ReferenceLine x={-0.5} stroke={C.gray} strokeDasharray="3 3" />
              <Bar dataKey="trend" radius={3} name="trend">
                {he.sensor_ranking.map((s) => <Cell key={s.sensor} fill={s.selected ? (s.trend > 0 ? C.red : C.blue) : '#cbd5e1'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Signaux bruts du moteur n°1" span={7} sub="Capteurs retenus, centrés-réduits : dérive progressive jusqu'à la défaillance">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={rawZ.data} margin={{ top: 5, right: 10, left: -20, bottom: 8 }}>
              <CartesianGrid stroke={C.grid} />
              <XAxis dataKey="c" type="number" domain={['dataMin', 'dataMax']} {...axis} />
              <YAxis {...axis} domain={[-4, 4]} />
              <Tooltip {...tip} formatter={(v, n) => [fmt(v, 2), he.sensor_info[n]]} />
              <Legend verticalAlign="top" height={24} iconType="plainline" />
              {rawZ.keys.map((k, i) => <Line key={k} dataKey={k} stroke={PAL[i]} dot={false} strokeWidth={1.3} isAnimationActive={false} />)}
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Indicateur de santé — moteurs d'entraînement" span={8}
          sub="HI = combinaison linéaire des 12 capteurs, cible 1 (début de vie) → 0 (défaillance), lissage glissant 10 cycles">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart margin={{ top: 5, right: 10, left: -14, bottom: 8 }}>
              <CartesianGrid stroke={C.grid} />
              <XAxis dataKey="c" type="number" domain={[0, 370]} {...axis}
                label={{ value: 'cycle', position: 'insideBottomRight', offset: -4, fontSize: 11 }} />
              <YAxis domain={[-0.3, 1.3]} {...axis} tickFormatter={(v) => v.toFixed(1)} />
              <Tooltip {...tip} formatter={(v) => fmt(v, 3)} labelFormatter={(l) => `Cycle ${l}`} />
              <ReferenceLine y={he.hi_threshold} stroke={C.red} strokeDasharray="5 4" label={{ value: `seuil = ${fmt(he.hi_threshold, 3)}`, fontSize: 11, fill: C.red, position: 'insideTopRight' }} />
              {he.hi_train.map((u, i) => <Line key={u.unit} data={u.pts} dataKey="hi" name={`Moteur ${u.unit}`} stroke={PAL[i]} dot={false} strokeWidth={1.4} isAnimationActive={false} />)}
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Poids du HI" span={4} sub="Coefficients de la régression (capteurs standardisés)">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={[...he.hi_weights].sort((a, b) => a.w - b.w)} layout="vertical" margin={{ left: 4, right: 10 }}>
              <CartesianGrid stroke={C.grid} horizontal={false} />
              <XAxis type="number" {...axis} />
              <YAxis type="category" dataKey="sensor" width={34} {...axis} />
              <Tooltip {...tip} formatter={(v) => fmt(v, 4)} labelFormatter={(l) => he.sensor_info[l]} />
              <Bar dataKey="w" radius={3}>{he.hi_weights.map((w) => <Cell key={w.sensor} fill={w.w > 0 ? C.blue : C.red} />)}</Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Section owner="Eya">PDM-02 · Classification normal / critique</Section>
      <div className="grid">
        <Card title="Performances" span={5} sub="Validation croisée par groupes de moteurs (GroupKFold 5) puis jeu de test NASA">
          <table>
            <thead><tr><th>Modèle</th><th></th><th className="num">AUC</th><th className="num">Préc.</th><th className="num">Rappel</th><th className="num">F1</th></tr></thead>
            <tbody>{names.flatMap((n) => ['cv', 'test'].map((k) => {
              const m = he.classifiers[n][k]
              return (<tr key={n + k} className={n === he.best && k === 'test' ? 'best' : ''}>
                <td>{k === 'cv' ? n : ''}</td><td style={{ color: C.muted }}>{k === 'cv' ? 'CV' : 'Test'}</td>
                <td className="num">{fmt(m.auc, 3)}</td><td className="num">{fmt(m.precision, 3)}</td>
                <td className="num">{fmt(m.recall, 3)}</td><td className="num">{fmt(m.f1, 3)}</td></tr>)
            }))}</tbody>
          </table>
          <div className="note">Le jeu de test contient peu de cycles critiques (moteurs tronqués tôt). La <b>précision</b> y est donc plus faible :
            un faux positif signifie une inspection anticipée, coût bien inférieur à celui d'une défaillance manquée.</div>
        </Card>

        <Card title="Courbes ROC (test)" span={4} sub="Taux de vrais positifs en fonction du taux de faux positifs">
          <ResponsiveContainer width="100%" height={250}>
            <LineChart margin={{ top: 5, right: 10, left: -18, bottom: 8 }}>
              <CartesianGrid stroke={C.grid} />
              <XAxis dataKey="fpr" type="number" domain={[0, 1]} {...axis} label={{ value: 'FPR', position: 'insideBottomRight', offset: -4, fontSize: 11 }} />
              <YAxis domain={[0, 1]} {...axis} />
              <Tooltip {...tip} formatter={(v) => fmt(v, 3)} />
              <Legend verticalAlign="top" height={44} iconType="plainline" />
              <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="#cbd5e1" strokeDasharray="4 4" />
              {names.map((n, i) => <Line key={n} data={rocData[i]} dataKey="tpr" name={`${n} (${fmt(he.classifiers[n].test.auc, 3)})`}
                stroke={i ? C.violet : C.teal} strokeWidth={2} dot={false} isAnimationActive={false} />)}
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Matrice de confusion" span={3} sub={`${he.best}, jeu de test, seuil 0,5`}>
          <CM m={best.test} />
          <div className="params" style={{ marginTop: 12, gridTemplateColumns: '1fr 1fr' }}>
            <Param l="Exactitude" v={`${fmt(best.test.accuracy * 100, 1)} %`} /><Param l="Rappel" v={`${fmt(best.test.recall * 100, 1)} %`} />
          </div>
        </Card>

        <Card title={`Suivi du moteur de test n°${engine}`} span={12}
          sub="Évolution du HI et de la probabilité d'état critique au fil des cycles"
          right={<select value={engine} onChange={(e) => setEngine(+e.target.value)}>
            {ru.table.map((u) => <option key={u.unit} value={u.unit}>Moteur {u.unit} · {u.state}</option>)}</select>}>
          <EngineHealth unit={engine} threshold={he.hi_threshold} />
        </Card>
      </div>
    </>)
  }}</Guard>}</Guard>
}
