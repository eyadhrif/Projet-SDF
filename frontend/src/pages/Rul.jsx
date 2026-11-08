import React, { useState } from 'react'
import {
  ComposedChart, LineChart, Line, Scatter, ScatterChart, BarChart, Bar, XAxis, YAxis, ZAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine, ReferenceArea,
} from 'recharts'
import { useData, Guard, Card, Kpi, Section, Param, fmt, tip, axis, C } from '../ui.jsx'

const NAMES = { deg: 'Dégradation bayésienne', lstm: 'LSTM', ensemble: 'Moyenne des deux' }

function EngineRul({ unit, row, thr }) {
  const s = useData(`/engines/${unit}`)
  return <Guard state={s}>{(e) => {
    const fail = e.last_cycle + row.deg, lo = e.last_cycle + row.deg_p10, hi = e.last_cycle + row.deg_p90
    const trueFail = e.last_cycle + e.true_end
    const xmax = Math.max(trueFail, hi, e.last_cycle + row.lstm) + 15
    return (<div className="grid" style={{ gap: 12 }}>
      <div className="s6">
        <div className="cs" style={{ margin: '0 0 6px' }}>RUL prédit à chaque cycle par les deux modèles, comparé au RUL réel</div>
        <ResponsiveContainer width="100%" height={270}>
          <LineChart data={e.series} margin={{ top: 5, right: 10, left: -14, bottom: 8 }}>
            <CartesianGrid stroke={C.grid} />
            <XAxis dataKey="c" type="number" domain={['dataMin', 'dataMax']} {...axis}
              label={{ value: 'cycle', position: 'insideBottomRight', offset: -4, fontSize: 11 }} />
            <YAxis {...axis} domain={[0, 'auto']} />
            <Tooltip {...tip} formatter={(v, n) => [fmt(v, 0), n]} labelFormatter={(l) => `Cycle ${l}`} />
            <Legend verticalAlign="top" height={24} iconType="plainline" />
            <Line dataKey="true" stroke={C.ink} strokeWidth={2} dot={false} name="RUL réel" isAnimationActive={false} />
            <Line dataKey="lstm" stroke={C.orange} strokeWidth={2} dot={false} name="LSTM" isAnimationActive={false} />
            <Line dataKey="deg" stroke={C.teal} strokeWidth={2} dot={{ r: 2 }} connectNulls name="Dégradation" isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="s6">
        <div className="cs" style={{ margin: '0 0 6px' }}>Projection du HI (moyenne a posteriori) jusqu'au seuil, avec intervalle 10–90 % du RUL</div>
        <ResponsiveContainer width="100%" height={270}>
          <ComposedChart margin={{ top: 5, right: 10, left: -14, bottom: 8 }}>
            <CartesianGrid stroke={C.grid} />
            <XAxis dataKey="c" type="number" domain={[0, xmax]} {...axis} allowDataOverflow />
            <YAxis domain={[-0.4, 1.3]} {...axis} tickFormatter={(v) => v.toFixed(1)} allowDataOverflow />
            <Tooltip {...tip} formatter={(v, n) => [fmt(v, 3), n]} labelFormatter={(l) => `Cycle ${l}`} />
            <Legend verticalAlign="top" height={24} iconType="plainline" />
            <ReferenceArea x1={lo} x2={hi} fill={C.teal} fillOpacity={0.1} />
            <Line data={e.series} dataKey="hr" stroke="#cbd5e1" dot={false} name="HI mesuré" isAnimationActive={false} />
            <Line data={e.projection} dataKey="proj" stroke={C.teal} strokeWidth={2.2} dot={false} name="Projection" isAnimationActive={false} />
            <ReferenceLine y={thr} stroke={C.red} strokeDasharray="5 4" label={{ value: 'seuil', fontSize: 11, fill: C.red, position: 'insideTopLeft' }} />
            <ReferenceLine x={e.last_cycle} stroke={C.muted} label={{ value: 'aujourd’hui', fontSize: 11, position: 'top' }} />
            <ReferenceLine x={fail} stroke={C.teal} strokeDasharray="4 3" />
            <ReferenceLine x={trueFail} stroke={C.ink} strokeDasharray="2 2" label={{ value: 'défaillance réelle', fontSize: 11, position: 'insideBottomRight' }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>)
  }}</Guard>
}

export default function Rul({ engine, setEngine }) {
  const s = useData('/rul')
  const [sortKey, setSort] = useState('lstm')
  return <Guard state={s}>{(d) => {
    const m = d.metrics, T = d.table
    const sorted = [...T].sort((a, b) => a.true - b.true).map((r, i) => ({ ...r, i: i + 1 }))
    const row = T.find((r) => r.unit === engine) || T[0]
    const tableRows = [...T].sort((a, b) => a[sortKey] - b[sortKey])
    return (<>
      <div className="head">
        <div><h1>Estimation de la durée de vie résiduelle (RUL)</h1>
          <p className="lede">Deux approches complémentaires, comparées sur les 100 moteurs de test NASA (RUL réel connu) :
            un modèle de dégradation <b>interprétable et probabiliste</b> et un réseau <b>LSTM</b> sur les séquences
            de capteurs.</p></div>
        <span className="tag">Score NASA : pénalise davantage les prédictions tardives</span>
      </div>

      <div className="grid">
        <Kpi label="RMSE · LSTM" value={fmt(m.lstm.rmse, 2)} unit="cycles" color={C.orange} hint={`MAE ${fmt(m.lstm.mae, 1)}`} />
        <Kpi label="RMSE · Dégradation" value={fmt(m.deg.rmse, 2)} unit="cycles" color={C.teal} hint={`MAE ${fmt(m.deg.mae, 1)}`} />
        <Kpi label="Score NASA · LSTM" value={fmt(m.lstm.score, 0)} hint={`Dégradation : ${fmt(m.deg.score, 0)}`} />
        <Kpi label="Couverture IC 10–90 %" value={fmt(d.deg_info.coverage_10_90, 0)} unit="%" hint="RUL réel dans l'intervalle (dégr.)" />
      </div>

      <Section>Comparaison des modèles</Section>
      <div className="grid">
        <Card title="Métriques sur le jeu de test" span={5} sub="Erreur = RUL prédit − RUL réel (positive = prédiction tardive, donc dangereuse)">
          <table>
            <thead><tr><th>Modèle</th><th className="num">RMSE</th><th className="num">MAE</th><th className="num">Biais</th><th className="num">Score</th><th className="num">|e|≤15</th></tr></thead>
            <tbody>{['deg', 'lstm', 'ensemble'].map((k) => (
              <tr key={k} className={k === 'lstm' ? 'best' : ''}>
                <td>{NAMES[k]}</td><td className="num">{fmt(m[k].rmse)}</td><td className="num">{fmt(m[k].mae)}</td>
                <td className="num">{fmt(m[k].bias, 1)}</td><td className="num">{fmt(m[k].score, 0)}</td>
                <td className="num">{fmt(m[k].within15, 0)} %</td></tr>))}
            </tbody>
          </table>
          <div className="note">Le <b>LSTM</b> est le plus précis : il exploite la dynamique conjointe des 12 capteurs.
            Le <b>modèle de dégradation</b> est moins précis mais <b>explicable</b> (trajectoire du HI, seuil physique) et fournit
            un <b>intervalle de confiance</b> du RUL, utile pour planifier la maintenance avec un niveau de risque maîtrisé.</div>
        </Card>

        <Card title="RUL prédit vs réel" span={4} sub="Chaque point est un moteur de test ; la diagonale correspond à une prédiction parfaite">
          <ResponsiveContainer width="100%" height={280}>
            <ScatterChart margin={{ top: 5, right: 10, left: -14, bottom: 8 }}>
              <CartesianGrid stroke={C.grid} />
              <XAxis type="number" dataKey="true" domain={[0, 220]} {...axis} label={{ value: 'RUL réel', position: 'insideBottomRight', offset: -4, fontSize: 11 }} />
              <YAxis type="number" dataKey="y" domain={[0, 220]} {...axis} allowDataOverflow />
              <ZAxis range={[28, 28]} />
              <Tooltip {...tip} formatter={(v, n) => [fmt(v, 0), n]} />
              <Legend verticalAlign="top" height={24} />
              <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 220, y: 220 }]} stroke={C.gray} strokeDasharray="4 4" />
              <Scatter name="Dégradation" data={T.map((r) => ({ true: r.true, y: r.deg, unit: r.unit }))} fill={C.teal} fillOpacity={0.75} isAnimationActive={false} />
              <Scatter name="LSTM" data={T.map((r) => ({ true: r.true, y: r.lstm, unit: r.unit }))} fill={C.orange} fillOpacity={0.75} isAnimationActive={false} />
            </ScatterChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Distribution des erreurs" span={3} sub="Nombre de moteurs par classe d'erreur (cycles)">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={d.error_hist} barGap={0} barCategoryGap={2} margin={{ top: 5, right: 5, left: -26, bottom: 8 }}>
              <CartesianGrid stroke={C.grid} vertical={false} />
              <XAxis dataKey="bin" {...axis} interval={3} />
              <YAxis {...axis} allowDecimals={false} />
              <Tooltip {...tip} labelFormatter={(l) => `[${l} ; ${+l + 10}[`} />
              <ReferenceLine x="0" stroke={C.ink} />
              <Bar dataKey="deg" fill={C.teal} name="Dégradation" />
              <Bar dataKey="lstm" fill={C.orange} name="LSTM" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Prédictions pour les 100 moteurs de test" span={12} sub="Moteurs triés par RUL réel croissant ; barres = intervalle 10–90 % du modèle de dégradation">
          <ResponsiveContainer width="100%" height={280}>
            <ComposedChart data={sorted} margin={{ top: 5, right: 12, left: -14, bottom: 8 }}>
              <CartesianGrid stroke={C.grid} />
              <XAxis dataKey="i" {...axis} label={{ value: 'moteurs triés', position: 'insideBottomRight', offset: -4, fontSize: 11 }} />
              <YAxis {...axis} domain={[0, 250]} allowDataOverflow />
              <Tooltip {...tip} labelFormatter={(l, p) => (p[0] ? `Moteur ${p[0].payload.unit}` : l)}
                formatter={(v, n) => [Array.isArray(v) ? `${fmt(v[0], 0)} – ${fmt(v[1], 0)}` : fmt(v, 0), n]} />
              <Legend verticalAlign="top" height={24} />
              <Bar dataKey={(r) => [r.deg_p10, r.deg_p90]} fill={C.teal} fillOpacity={0.15} name="IC 10–90 %" isAnimationActive={false} />
              <Line dataKey="true" stroke={C.ink} strokeWidth={2} dot={false} name="RUL réel" isAnimationActive={false} />
              <Line dataKey="deg" stroke="none" dot={{ r: 2.5, fill: C.teal }} legendType="circle" name="Dégradation" isAnimationActive={false} />
              <Line dataKey="lstm" stroke="none" dot={{ r: 2.5, fill: C.orange }} legendType="circle" name="LSTM" isAnimationActive={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Section>Analyse par moteur</Section>
      <div className="grid">
        <Card title={`Moteur de test n°${engine}`} span={12}
          sub={`${row.cycles} cycles observés · RUL réel ${row.true} · dégradation ${fmt(row.deg, 0)} [${fmt(row.deg_p10, 0)} ; ${fmt(row.deg_p90, 0)}] · LSTM ${fmt(row.lstm, 0)}`}
          right={<select value={engine} onChange={(e) => setEngine(+e.target.value)}>
            {T.map((u) => <option key={u.unit} value={u.unit}>Moteur {u.unit}</option>)}</select>}>
          <EngineRul unit={engine} row={row} thr={d.deg_info.threshold} />
        </Card>
      </div>

      <div className="grid" style={{ marginTop: 16 }}>
        <Card title="Modèle de dégradation" span={3} sub={<>HI(t) = w₀ + w₁τ + w₂τ², a priori N(m₀, S₀) appris sur la flotte, mise à jour bayésienne par moteur</>}>
          <div className="params" style={{ gridTemplateColumns: '1fr 1fr' }}>
            <Param l="Seuil HI" v={fmt(d.deg_info.threshold, 3)} /><Param l="σ seuil" v={fmt(d.deg_info.threshold_std, 3)} />
            <Param l="σ bruit" v={fmt(d.deg_info.sigma, 3)} /><Param l="Tirages" v="1000" />
          </div>
        </Card>
        <Card title="Apprentissage du LSTM" span={5} sub={`2 couches LSTM (64) + dense, fenêtres de ${d.lstm_info.seq} cycles, cible plafonnée à ${d.lstm_info.cap}, arrêt précoce`}>
          <ResponsiveContainer width="100%" height={190}>
            <LineChart data={d.lstm_info.history} margin={{ top: 5, right: 10, left: -18, bottom: 0 }}>
              <CartesianGrid stroke={C.grid} />
              <XAxis dataKey="epoch" {...axis} />
              <YAxis {...axis} domain={[0, 'auto']} />
              <Tooltip {...tip} formatter={(v) => fmt(v, 2)} labelFormatter={(l) => `Époque ${l}`} />
              <Legend verticalAlign="top" height={22} iconType="plainline" />
              <Line dataKey="train_rmse" stroke={C.orange} dot={false} name="RMSE entraînement" isAnimationActive={false} />
              <Line dataKey="val_rmse" stroke={C.ink} strokeDasharray="4 3" dot={false} name="RMSE validation" isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Tableau de flotte" span={4} sub="Cliquez sur une ligne pour analyser le moteur"
          right={<select value={sortKey} onChange={(e) => setSort(e.target.value)}>
            <option value="lstm">Tri : RUL LSTM</option><option value="deg">Tri : RUL dégr.</option><option value="unit">Tri : n°</option></select>}>
          <div className="scroll" style={{ maxHeight: 220 }}>
            <table>
              <thead><tr><th>#</th><th className="num">Réel</th><th className="num">Dégr.</th><th className="num">LSTM</th><th>État</th></tr></thead>
              <tbody>{tableRows.map((r) => (
                <tr key={r.unit} className="click" onClick={() => { setEngine(r.unit); window.scrollTo({ top: 1300, behavior: 'smooth' }) }}
                  style={r.unit === engine ? { background: '#eff6ff' } : null}>
                  <td>{r.unit}</td><td className="num">{r.true}</td><td className="num">{fmt(r.deg, 0)}</td>
                  <td className="num">{fmt(r.lstm, 0)}</td><td><span className={`pill ${r.state}`}>{r.state}</span></td></tr>))}
              </tbody>
            </table>
          </div>
        </Card>

        <Card title="Calibration du modèle de dégradation" span={12}
          sub="Couverture empirique des intervalles de RUL comparée au niveau nominal, et biais selon le RUL réel (diagnostic a posteriori, modèle inchangé)">
          <div className="grid" style={{ gap: 12 }}>
            <div className="s6">
              <table>
                <thead><tr><th>Intervalle</th><th className="num">Nominal</th><th className="num">Couverture</th><th className="num">Largeur moy.</th></tr></thead>
                <tbody>{d.deg_info.calibration.map((c) => (
                  <tr key={c.nominal}><td>{c.bornes.join('–')}</td><td className="num">{c.nominal} %</td>
                    <td className={`num ${c.couverture < c.nominal - 10 ? 'ko' : ''}`}>{fmt(c.couverture, 0)} %</td>
                    <td className="num">{fmt(c.largeur_moyenne, 1)} cycles</td></tr>))}
                </tbody>
              </table>
            </div>
            <div className="s6">
              <table>
                <thead><tr><th>RUL réel</th><th className="num">Moteurs</th><th className="num">Biais</th><th className="num">MAE</th><th className="num">Couv. 80 %</th></tr></thead>
                <tbody>{d.deg_info.biais.par_tranche.map((t) => (
                  <tr key={t.rul_min}><td>{t.rul_max ? `${t.rul_min}–${t.rul_max}` : `> ${t.rul_min}`} cycles</td>
                    <td className="num">{t.n}</td><td className="num">{fmt(t.biais, 1)}</td>
                    <td className="num">{fmt(t.mae, 1)}</td><td className="num">{fmt(t.couverture_80, 0)} %</td></tr>))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="note warn">Les intervalles sont <b>trop étroits</b> : à chaque niveau, la couverture observée est
            inférieure au niveau nominal. Le biais moyen est de {fmt(d.deg_info.biais.moyen, 1)} cycles
            ({fmt(d.deg_info.biais.pct_tardif, 0)} % de prédictions tardives). Sans ce biais, l'écart-type des erreurs serait de
            {' '}{fmt(d.deg_info.biais.rmse_hors_biais, 1)} cycles : c'est un diagnostic, pas une performance atteignable, car le biais
            est mesuré sur le jeu de test lui-même.</div>
        </Card>
      </div>
    </>)
  }}</Guard>
}
