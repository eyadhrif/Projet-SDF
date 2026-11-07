import React from 'react'
import {
  ComposedChart, LineChart, Line, Area, Scatter, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine, ReferenceDot,
} from 'recharts'
import { useData, Guard, Card, Kpi, Section, Param, fmt, tip, axis, tticks, C } from '../ui.jsx'

const X = (label, max = 380) => ({ type: 'number', dataKey: 't', domain: [0, max], ticks: tticks.filter((t) => t <= max), ...axis,
  label: { value: label, position: 'insideBottomRight', offset: -4, fontSize: 11, fill: C.muted } })

export default function Fiabilite() {
  const s = useData('/fmds')
  return <Guard state={s}>{(d) => {
    const fi = d.fiabilite, ma = d.maintenabilite, di = d.disponibilite, pr = d.preventif, as = d.assumptions
    const curves = fi.curves.filter((c) => c.t <= 380)
    const hz = fi.hazard.filter((p) => p.t <= 360)
    return (<>
      <div className="head">
        <div><h1>Fiabilité, maintenabilité, disponibilité</h1>
          <p className="lede">{fi.n_units} moteurs : {fi.n_failures} défaillances observées (jeu d'entraînement) et
            {' '}{fi.n_censored} moteurs encore en service au dernier cycle (jeu de test, censure à droite).
            Démarche du cours : estimation non paramétrique, puis paramétrique, puis validation.</p></div>
        <span className="tag">Unité de temps : cycle de vol</span>
      </div>

      <div className="grid">
        <Kpi label="MTTF" value={fmt(fi.mttf, 1)} unit="cycles" hint="γ + η·Γ(1+1/β)" />
        <Kpi label="Médiane KM" value={fmt(fi.median_km, 0)} unit="cycles" hint="R(t) = 0,5" />
        <Kpi label="Durée B10" value={fmt(fi.b10, 0)} unit="cycles"
          hint={`10 % de défaillances · B1 = ${fmt(fi.b1, 0)} · B50 = ${fmt(fi.b50, 0)}`} />
        <Kpi label="Disponibilité A" value={fmt(di.A * 100, 2)} unit="%" hint="MUT / (MUT + MDT)" />
      </div>

      <Section owner="Eya">FMDS-01 · Fiabilité</Section>
      <div className="grid">
        <Card title="Fonction de fiabilité R(t)" span={8}
          sub="Kaplan-Meier avec IC 95 % (log-log) et marques de censure, comparé aux modèles paramétriques">
          <ResponsiveContainer width="100%" height={320}>
            <ComposedChart margin={{ top: 8, right: 12, left: -10, bottom: 8 }}>
              <CartesianGrid stroke={C.grid} />
              <XAxis {...X('cycles')} />
              <YAxis domain={[0, 1.02]} {...axis} tickFormatter={(v) => v.toFixed(1)} />
              <Tooltip {...tip} formatter={(v, n) => [Array.isArray(v) ? `${fmt(v[0], 3)} – ${fmt(v[1], 3)}` : fmt(v, 3), n]}
                labelFormatter={(l) => `t = ${l} cycles`} />
              <Legend verticalAlign="top" height={28} iconType="plainline" />
              <Area data={fi.km} dataKey={(p) => [p.lo, p.hi]} type="stepAfter" fill={C.blue} fillOpacity={0.12}
                stroke="none" name="IC 95 % KM" isAnimationActive={false} />
              <Line data={fi.km} dataKey="R" type="stepAfter" stroke={C.blue} strokeWidth={2} dot={false} name="Kaplan-Meier" isAnimationActive={false} />
              <Line data={curves} dataKey="R_w3" stroke={C.teal} strokeWidth={2.2} dot={false} name="Weibull 3P (retenu)" isAnimationActive={false} />
              <Line data={curves} dataKey="R_w2" stroke={C.gray} strokeDasharray="5 4" dot={false} name="Weibull 2P (MV)" isAnimationActive={false} />
              <Scatter data={fi.censored} dataKey="R" fill={C.red} fillOpacity={0.55} shape="cross" name="Censures" isAnimationActive={false} legendType="cross" />
            </ComposedChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Paramètres estimés" span={4} sub="Weibull 2P par MCO (rangs de Bernard) et par MV ; Weibull 3P par MV">
          <table>
            <thead><tr><th>Méthode</th><th className="num greek">β</th><th className="num greek">η</th><th className="num greek">γ</th></tr></thead>
            <tbody>
              <tr><td>MCO · W2P</td><td className="num">{fmt(fi.mco.beta)}</td><td className="num">{fmt(fi.mco.eta, 1)}</td><td className="num">0</td></tr>
              <tr><td>MV · W2P</td><td className="num">{fmt(fi.mv.beta)}</td><td className="num">{fmt(fi.mv.eta, 1)}</td><td className="num">0</td></tr>
              <tr><td>MV censuré · W2P</td><td className="num">{fmt(fi.mv_cens.beta)}</td><td className="num">{fmt(fi.mv_cens.eta, 1)}</td><td className="num">0</td></tr>
              <tr className="best"><td>MV · W3P ✓</td><td className="num">{fmt(fi.w3.beta)}</td><td className="num">{fmt(fi.w3.eta, 1)}</td><td className="num">{fmt(fi.w3.gamma, 1)}</td></tr>
            </tbody>
          </table>
          <div className="note">R² du diagramme de Weibull (MCO) : <b>{fmt(fi.mco.r2, 3)}</b>. La courbure visible du
            diagramme signale un seuil γ &gt; 0. IC 95 % MV censuré : β ∈ [{fmt(fi.mv_cens.beta_ci[0])} ; {fmt(fi.mv_cens.beta_ci[1])}].</div>
          <div className="params" style={{ marginTop: 12, gridTemplateColumns: 'repeat(3, 1fr)' }}>
            <Param l="B1 (1 %)" v={`${fmt(fi.b1, 1)} cycles`} />
            <Param l="B10 (10 %)" v={`${fmt(fi.b10, 1)} cycles`} />
            <Param l="B50 (médiane)" v={`${fmt(fi.b50, 1)} cycles`} />
          </div>
          <div className="note">β = {fmt(fi.w3.beta)} &gt; 1 : <b>taux de défaillance croissant</b>, donc usure. La maintenance
            préventive est justifiée.</div>
        </Card>

        <Card title="Diagramme de Weibull (MCO)" span={4} sub="ln(−ln(1−F)) en fonction de ln(t), droite des moindres carrés">
          <ResponsiveContainer width="100%" height={250}>
            <ComposedChart data={fi.weibull_plot} margin={{ top: 5, right: 10, left: -20, bottom: 8 }}>
              <CartesianGrid stroke={C.grid} />
              <XAxis dataKey="x" type="number" domain={[4.8, 6]} {...axis} tickFormatter={(v) => v.toFixed(1)}
                label={{ value: 'ln t', position: 'insideBottomRight', offset: -4, fontSize: 11 }} />
              <YAxis {...axis} domain={[-5, 2]} tickFormatter={(v) => v.toFixed(0)} />
              <Tooltip {...tip} formatter={(v) => fmt(v, 3)} />
              <Scatter dataKey="y" fill={C.blue} name="Données" isAnimationActive={false} />
              <Line dataKey="fit" stroke={C.red} dot={false} strokeWidth={2} name="Droite MCO" isAnimationActive={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Taux de défaillance λ(t)" span={4} sub="Nelson-Aalen lissé par noyau (non paramétrique) et Weibull 3P">
          <ResponsiveContainer width="100%" height={250}>
            <ComposedChart margin={{ top: 5, right: 10, left: -8, bottom: 8 }}>
              <CartesianGrid stroke={C.grid} />
              <XAxis {...X('cycles', 360)} />
              <YAxis {...axis} tickFormatter={(v) => v.toFixed(3)} />
              <Tooltip {...tip} formatter={(v) => fmt(v, 4)} labelFormatter={(l) => `t = ${fmt(l, 0)}`} />
              <Line data={hz} dataKey="h" stroke={C.blue} dot={false} strokeWidth={2} name="NA lissé" isAnimationActive={false} />
              <Line data={curves.filter((c) => c.t <= 360)} dataKey="lam" stroke={C.teal} dot={false} strokeWidth={2} name="Weibull 3P" isAnimationActive={false} />
              <Legend verticalAlign="top" height={24} iconType="plainline" />
            </ComposedChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Adéquation des lois" span={4} sub="MV sur les durées complètes, test de Kolmogorov-Smirnov (α = 5 %) et AIC">
          <table>
            <thead><tr><th>Loi</th><th className="num">AIC</th><th className="num">p (KS)</th><th></th></tr></thead>
            <tbody>{fi.comparison.map((m) => (
              <tr key={m.model} className={m.model === fi.retained ? 'best' : ''}>
                <td>{m.model}</td><td className="num">{fmt(m.aic, 1)}</td><td className="num">{fmt(m.ks_p, 3)}</td>
                <td className={m.accept ? 'ok' : 'ko'}>{m.accept ? 'accepté' : 'rejeté'}</td></tr>))}
            </tbody>
          </table>
          <div className="note">La Weibull 2P est <b>rejetée</b> (p = {fmt(fi.mv.ks_p, 3)}). Les lois Weibull 3P et log-normale
            sont équivalentes (ΔAIC &lt; 1). On retient la <b>Weibull 3P</b> : γ a une interprétation physique (durée sans défaillance garantie).</div>
        </Card>

        <Card title="Fiabilité conditionnelle" span={6} sub="Probabilité qu'un moteur ayant atteint t cycles survive aux 25 cycles suivants">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={fi.conditional} margin={{ top: 5, right: 10, left: -18, bottom: 8 }}>
              <CartesianGrid stroke={C.grid} />
              <XAxis {...X('âge atteint (cycles)', 300)} />
              <YAxis domain={[0, 1]} {...axis} />
              <Tooltip {...tip} formatter={(v) => [fmt(v, 3), 'R(t+25 | t)']} />
              <ReferenceLine y={0.9} stroke={C.amber} strokeDasharray="4 4" label={{ value: '0,9', fontSize: 11, fill: C.amber, position: 'left' }} />
              <Line dataKey="Rc" stroke={C.violet} strokeWidth={2} dot={{ r: 2 }} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Densité et fonction de répartition" span={6} sub="Weibull 3P : f(t) et F(t) = 1 − R(t)">
          <ResponsiveContainer width="100%" height={220}>
            <ComposedChart data={curves} margin={{ top: 5, right: 10, left: -8, bottom: 8 }}>
              <CartesianGrid stroke={C.grid} />
              <XAxis {...X('cycles')} />
              <YAxis yAxisId="f" {...axis} tickFormatter={(v) => v.toFixed(3)} />
              <YAxis yAxisId="F" orientation="right" domain={[0, 1]} {...axis} />
              <Tooltip {...tip} formatter={(v) => fmt(v, 4)} />
              <Area yAxisId="f" dataKey="f" fill={C.teal} fillOpacity={0.15} stroke={C.teal} name="f(t)" isAnimationActive={false} />
              <Line yAxisId="F" dataKey="F" stroke={C.red} dot={false} name="F(t)" isAnimationActive={false} />
              <Legend verticalAlign="top" height={24} iconType="plainline" />
            </ComposedChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Section owner="Salma">FMDS-02 · Maintenabilité & disponibilité</Section>
      <div className="grid">
        <Card title="Maintenabilité M(t)" span={5}
          sub={`${ma.samples.length} temps de réparation, loi log-normale estimée par MV (médiane simulée ${as.ttr_median_h} h)`}>
          <ResponsiveContainer width="100%" height={240}>
            <ComposedChart margin={{ top: 5, right: 10, left: -18, bottom: 8 }}>
              <CartesianGrid stroke={C.grid} />
              <XAxis type="number" dataKey="t" domain={[0, 60]} {...axis}
                label={{ value: 'heures', position: 'insideBottomRight', offset: -4, fontSize: 11 }} />
              <YAxis domain={[0, 1]} {...axis} />
              <Tooltip {...tip} formatter={(v) => fmt(v, 3)} labelFormatter={(l) => `${fmt(l, 1)} h`} />
              <Line data={ma.M} dataKey="M" stroke={C.orange} strokeWidth={2.2} dot={false} name="M(t)" isAnimationActive={false} />
              <ReferenceLine x={ma.mttr_h} stroke={C.ink} strokeDasharray="4 4" label={{ value: 'MTTR', fontSize: 11, position: 'top' }} />
              <ReferenceLine x={ma.t90_h} stroke={C.gray} strokeDasharray="2 3" label={{ value: 't90', fontSize: 11, position: 'top' }} />
            </ComposedChart>
          </ResponsiveContainer>
          <div className="params">
            <Param l="μ (log)" v={fmt(ma.mu, 3)} /><Param l="σ (log)" v={fmt(ma.sigma, 3)} />
            <Param l="MTTR" v={`${fmt(ma.mttr_h, 1)} h`} /><Param l="t90" v={`${fmt(ma.t90_h, 1)} h`} />
            <Param l="Taux μ" v={`${fmt(ma.repair_rate, 4)} /h`} /><Param l="KS p" v={fmt(ma.ks.p, 3)} />
          </div>
        </Card>

        <Card title="Disponibilité instantanée A(t)" span={4} sub="Modèle markovien à 2 états, λ = 1/MTTF, μ = 1/MTTR">
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={di.A_t} margin={{ top: 5, right: 10, left: -4, bottom: 8 }}>
              <CartesianGrid stroke={C.grid} />
              <XAxis {...X('cycles', 60)} />
              <YAxis domain={[0.95, 1]} {...axis} tickFormatter={(v) => v.toFixed(3)} />
              <Tooltip {...tip} formatter={(v) => [fmt(v, 4), 'A(t)']} />
              <ReferenceLine y={di.A} stroke={C.ink} strokeDasharray="4 4" label={{ value: `A∞ = ${fmt(di.A, 4)}`, fontSize: 11, position: 'insideTopRight' }} />
              <Line dataKey="A" stroke={C.blue} strokeWidth={2.2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
          <div className="params">
            <Param l="MTBF" v={fmt(di.mtbf, 1)} /><Param l="MUT" v={fmt(di.mut, 1)} /><Param l="MDT" v={fmt(di.mdt, 2)} />
          </div>
        </Card>

        <Card title="Histogramme des temps de réparation" span={3} sub="Échantillon simulé (h)">
          <ResponsiveContainer width="100%" height={240}>
            <ComposedChart data={ma.hist} margin={{ top: 5, right: 5, left: -24, bottom: 8 }}>
              <CartesianGrid stroke={C.grid} vertical={false} />
              <XAxis dataKey="mid" {...axis} />
              <YAxis {...axis} allowDecimals={false} />
              <Tooltip {...tip} labelFormatter={(l, p) => (p[0] ? `${p[0].payload.bin} h` : l)} />
              <Bar dataKey="n" fill={C.orange} fillOpacity={0.8} radius={[3, 3, 0, 0]} name="réparations" />
            </ComposedChart>
          </ResponsiveContainer>
          <div className="note warn" style={{ fontSize: 11.5 }}>C-MAPSS ne contient pas de temps de réparation : ils sont
            simulés (hypothèse documentée), puis ré-estimés par MV.</div>
        </Card>

        <Card title="Stratégie : remplacement préventif à âge fixe" span={12}
          sub={`Coût moyen par cycle C(T) = [Cp·R(T) + Cc·(1−R(T))] / ∫₀ᵀ R(t)dt, avec Cp = ${pr.Cp} et Cc = ${pr.Cc} (une défaillance en service coûte 5 fois plus cher)`}>
          <div className="grid" style={{ gap: 12 }}>
            <div className="s8">
              <ResponsiveContainer width="100%" height={250}>
                <ComposedChart data={pr.curve} margin={{ top: 10, right: 30, left: 0, bottom: 8 }}>
                  <CartesianGrid stroke={C.grid} />
                  <XAxis dataKey="T" type="number" domain={[100, 360]} {...axis}
                    label={{ value: 'âge de remplacement T (cycles)', position: 'insideBottomRight', offset: -4, fontSize: 11 }} />
                  <YAxis yAxisId="c" {...axis} tickFormatter={(v) => v.toFixed(3)} />
                  <YAxis yAxisId="a" orientation="right" domain={[0.9, 1]} {...axis} tickFormatter={(v) => v.toFixed(2)} />
                  <Tooltip {...tip} formatter={(v, n) => [fmt(v, 4), n]} labelFormatter={(l) => `T = ${l}`} />
                  <Legend verticalAlign="top" height={24} iconType="plainline" />
                  <Line yAxisId="c" dataKey="cost" stroke={C.teal} strokeWidth={2.2} dot={false} name="Coût / cycle" isAnimationActive={false} />
                  <Line yAxisId="a" dataKey="A" stroke={C.blue} strokeDasharray="5 4" dot={false} name="Disponibilité" isAnimationActive={false} />
                  <ReferenceLine yAxisId="c" x={pr.T_opt} stroke={C.red} strokeDasharray="4 4" label={{ value: `T* = ${fmt(pr.T_opt, 0)}`, fontSize: 11, fill: C.red, position: 'top' }} />
                  <ReferenceLine yAxisId="c" y={pr.cost_rtf} stroke={C.gray} strokeDasharray="2 3" label={{ value: 'sans préventif', fontSize: 11, fill: C.muted, position: 'insideTopRight' }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
            <div className="s4">
              <div className="params" style={{ gridTemplateColumns: '1fr 1fr' }}>
                <Param l="Âge optimal T*" v={`${fmt(pr.T_opt, 0)} cycles`} />
                <Param l="R(T*)" v={fmt(pr.R_at_T, 3)} />
                <Param l="Gain vs corrective" v={`−${fmt(pr.saving_pct, 0)} %`} />
                <Param l="Coût à T*" v={fmt(pr.cost_opt, 4)} />
              </div>
              <div className="note">Grâce au seuil γ ≈ {fmt(fi.w3.gamma, 0)} cycles, remplacer les moteurs vers <b>{fmt(pr.T_opt, 0)} cycles</b> évite
                presque toutes les défaillances en service. En pratique, la maintenance <b>prédictive</b> (pages suivantes) permet de
                ne remplacer que les moteurs réellement dégradés, et donc d'exploiter les moteurs les plus robustes au-delà de T*.</div>
            </div>
          </div>
        </Card>
      </div>
    </>)
  }}</Guard>
}
