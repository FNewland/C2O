/**
 * ParametricEditor — Interactive editor for all parametric model data.
 *
 * Shows mass fractions, cost fractions, power duty cycles as editable tables.
 * Changes mark the design as stale.
 */
import { useState, useEffect } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useApplyToDesign } from '../hooks/useApplyToDesign'
import { fs } from '../theme/tokens'

interface ParametricData {
  mass_fractions: Record<string, Record<string, number>>
  cost_fractions: Record<string, Record<string, number>>
  power_duty_cycles: Record<string, any>
  sa_power_generation: Record<string, Record<string, number>>
  sources: string[]
}

export function ParametricEditor() {
  const [data, setData] = useState<ParametricData | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'mass' | 'cost' | 'power' | 'sa'>('mass')
  const markStale = useDesignStore(s => s.markStale)
  const scClass = useDesignStore(s => s.requirements.spacecraft_class)

  useEffect(() => {
    fetch('/api/lifecycle/parametric-data')
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setData(d) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const [applied, setApplied] = useState(false)

  const parametricEvents = data ? [
    ...Object.entries(data.mass_fractions).map(([subsys, values]) => ({
      kind: 'parameter_override' as const,
      target_id: `parametric.mass_fraction.${subsys}`,
      new_value: values[scClass] ?? 0,
    })),
    ...Object.entries(data.cost_fractions).map(([subsys, values]) => ({
      kind: 'parameter_override' as const,
      target_id: `parametric.cost_fraction.${subsys}`,
      new_value: values[scClass] ?? 0,
    })),
  ] : []

  const apply = useApplyToDesign({
    events: parametricEvents,
    correlation_id: 'parametric-editor',
    rationale: `Apply parametric model fractions for ${scClass} class`,
  })

  if (loading) return <div style={{ padding: '1rem', color: 'var(--text-3)' }}>Loading parametric data...</div>
  if (!data) return <div style={{ padding: '1rem', color: 'var(--status-alarm)' }}>Failed to load parametric data.</div>

  const tabs = [
    { id: 'mass' as const, label: 'Mass Fractions' },
    { id: 'cost' as const, label: 'Cost Fractions' },
    { id: 'power' as const, label: 'Power Duty Cycles' },
    { id: 'sa' as const, label: 'SA Power' },
  ]

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ marginBottom: '0.25rem' }}>Parametric Model Data</h2>
      <p style={{ fontSize: fs.label, color: 'var(--text-2)', marginBottom: '0.5rem' }}>
        These values drive the sizing agents. Edit to override defaults. Changes mark the design as stale.
        <br />Sources: {data.sources?.join(', ')}
      </p>

      {/* Tab selector */}
      <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.75rem' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            padding: '0.25rem 0.6rem', fontSize: fs.label, borderRadius: '4px', cursor: 'pointer',
            background: activeTab === t.id ? 'var(--interactive)' : 'var(--bg-secondary, var(--surface-2))',
            color: activeTab === t.id ? 'white' : 'var(--text-2)',
            border: `1px solid ${activeTab === t.id ? 'var(--interactive)' : 'var(--line)'}`,
          }}>{t.label}</button>
        ))}
      </div>

      {/* Mass fractions table */}
      {activeTab === 'mass' && (
        <FractionTable title="Subsystem Mass Fractions (% of dry mass)" data={data.mass_fractions}
          highlight={scClass} onEdit={() => markStale('parametric')} />
      )}

      {/* Cost fractions table */}
      {activeTab === 'cost' && (
        <FractionTable title="Mission Cost Fractions (% of total)" data={data.cost_fractions}
          highlight={scClass} onEdit={() => markStale('parametric')} />
      )}

      {/* Power duty cycles */}
      {activeTab === 'power' && (
        <div className="card">
          <h3 style={{ fontSize: fs.body, marginBottom: '0.4rem' }}>Power Duty Cycles by Mode</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label }}>
            <thead>
              <tr style={{ background: 'var(--bg-primary, var(--surface-0))' }}>
                <th style={th}>Mode</th>
                <th style={thR}>Power (W) — {scClass}</th>
                <th style={thR}>Duty (%)</th>
                <th style={th}>Description</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.power_duty_cycles).map(([mode, info]: [string, any]) => (
                <tr key={mode} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 5%, transparent)' }}>
                  <td style={{ ...td, fontWeight: 600 }}>{mode.replace(/_/g, ' ')}</td>
                  <td style={tdR}>{info.power_w?.[scClass] || info.power_w?.nano || '—'}</td>
                  <td style={tdR}>{info.duty_pct}%</td>
                  <td style={{ ...td, fontSize: fs.label, color: 'var(--text-3)' }}>{info.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* SA power generation */}
      {activeTab === 'sa' && (
        <div className="card">
          <h3 style={{ fontSize: fs.body, marginBottom: '0.4rem' }}>Solar Array Power Generation (W)</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label }}>
            <thead>
              <tr style={{ background: 'var(--bg-primary, var(--surface-0))' }}>
                <th style={th}>Configuration</th>
                {['1U', '2U', '3U', '6U', '12U'].map(ff => (
                  <th key={ff} style={thR}>{ff}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.sa_power_generation).map(([config, values]) => (
                <tr key={config} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 5%, transparent)' }}>
                  <td style={{ ...td, fontWeight: 500 }}>{config.replace(/_/g, ' ')}</td>
                  {['1U', '2U', '3U', '6U', '12U'].map(ff => (
                    <td key={ff} style={tdR}>{(values as any)[ff] ?? '—'}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <button className="btn" onClick={async () => { await apply(); setApplied(true); setTimeout(() => setApplied(false), 2000) }}
        style={{ marginTop: '0.5rem', width: '100%', background: applied ? 'var(--status-ok)' : 'var(--interactive)', fontSize: fs.label }}>
        {applied ? 'Applied — reconverging...' : 'Apply to Design'}
      </button>
    </div>
  )
}

function FractionTable({ title, data, highlight, onEdit }: {
  title: string; data: Record<string, Record<string, number>>; highlight: string; onEdit: () => void
}) {
  const classes = ['nano', 'micro', 'small', 'medium', 'large']
  return (
    <div className="card">
      <h3 style={{ fontSize: fs.body, marginBottom: '0.4rem' }}>{title}</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: fs.label }}>
        <thead>
          <tr style={{ background: 'var(--bg-primary, var(--surface-0))' }}>
            <th style={th}>Subsystem</th>
            {classes.map(c => (
              <th key={c} style={{ ...thR, color: c === highlight ? 'var(--interactive)' : 'var(--text-2)', fontWeight: c === highlight ? 700 : 400 }}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Object.entries(data).map(([subsystem, values]) => (
            <tr key={subsystem} style={{ borderBottom: '1px solid color-mix(in srgb, var(--text) 5%, transparent)' }}>
              <td style={{ ...td, fontWeight: 500 }}>{subsystem.replace(/_/g, ' ')}</td>
              {classes.map(c => (
                <td key={c} style={{
                  ...tdR,
                  color: c === highlight ? 'var(--text)' : 'var(--text-3)',
                  fontWeight: c === highlight ? 600 : 400,
                }}>
                  {c === highlight && values[c] !== undefined ? (
                    <input className="input" type="number" step={0.1} min={0} max={100}
                      value={(values[c] * 100).toFixed(1)}
                      onChange={() => onEdit()}
                      style={{ width: '55px', fontSize: fs.label, textAlign: 'right', background: 'rgba(59,130,246,0.1)', border: '1px solid color-mix(in srgb, var(--interactive) 25%, transparent)' }}
                      title="Edit this value to override the parametric model"
                    />
                  ) : (
                    values[c] !== undefined ? `${(values[c] * 100).toFixed(1)}%` : '—'
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.3rem 0.5rem', textAlign: 'left', fontSize: fs.label, color: 'var(--text-2)', textTransform: 'uppercase' }
const thR: React.CSSProperties = { ...th, textAlign: 'right' }
const td: React.CSSProperties = { padding: '0.25rem 0.5rem' }
const tdR: React.CSSProperties = { ...td, textAlign: 'right', fontFamily: 'monospace' }
