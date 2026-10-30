import { useState } from 'react'
import { useDesignStore, type DesignParam } from '../stores/designStore'
import { useSessionStore } from '../stores/sessionStore'
import { useCanEditParameter, useHasActiveSession } from '../hooks/useActiveParameters'
import { SVGWaterfall } from '../charts/SVGWaterfall'
import { SVGBarChart } from '../charts/SVGBarChart'
import { BudgetGauge } from '../charts/BudgetGauge'
import { MarginEnforcement } from './MarginEnforcement'
import { SpectrumSelector } from './SpectrumSelector'
import { LaunchSelector } from './LaunchSelector'
import { PointingBudget } from './PointingBudget'
import { DataBudget } from './DataBudget'
import { TimingBudget } from './TimingBudget'

// Extended domain order including all 20 agent domains
const DOMAIN_ORDER = [
  'orbit', 'payload', 'power', 'aocs', 'thermal', 'link', 'data',
  'propulsion', 'structure', 'mass', 'cost', 'systems', 'risk', 'trl',
  'debris', 'sustainability', 'radiation', 'volume', 'reliability', 'community',
]

function formatValue(value: number | string | boolean): string {
  if (typeof value === 'number') {
    if (Math.abs(value) >= 1e6) return value.toExponential(2)
    if (Math.abs(value) >= 100) return value.toFixed(0)
    if (Math.abs(value) >= 1) return value.toFixed(2)
    if (Math.abs(value) >= 0.01) return value.toFixed(3)
    return value.toExponential(2)
  }
  return String(value)
}

// --- KPI Card ---
function KpiCard({ label, value, unit, status }: {
  label: string; value: string; unit?: string
  status?: 'green' | 'amber' | 'red' | 'blue'
}) {
  const colors = { green: '#10b981', amber: '#f59e0b', red: '#ef4444', blue: '#3b82f6' }
  const c = colors[status || 'blue']
  return (
    <div style={{
      background: 'var(--bg-secondary, #1f2937)', borderRadius: '6px', padding: '0.6rem 0.75rem',
      borderTop: `3px solid ${c}`, border: '1px solid var(--border, #374151)',
      minWidth: 0,
    }}>
      <div style={{ fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.05em', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{label}</div>
      <div style={{ fontSize: '1.3rem', fontWeight: 700, fontFamily: 'monospace', color: c, lineHeight: 1.2 }}>{value}</div>
      {unit && <div style={{ fontSize: '0.65rem', color: '#6b7280' }}>{unit}</div>}
    </div>
  )
}

// --- Mini radiation card ---
function RadiationCard({ parameters: p }: { parameters: Record<string, DesignParam> }) {
  const get = (id: string) => { const v = p[id]; return v && typeof v.value === 'number' ? v.value : 0 }
  const getStr = (id: string) => { const v = p[id]; return v ? String(v.value) : '' }

  const tid = get('radiation.tid_mission_krad')
  const elClass = getStr('radiation.electronics_class')
  const env = getStr('radiation.environment')
  if (!p['radiation.tid_mission_krad']) return null

  const classColors: Record<string, string> = {
    commercial: '#10b981', rad_tolerant: '#f59e0b', rad_hard: '#ef4444', rad_hard_plus: '#dc2626',
  }

  return (
    <div style={{
      background: 'var(--bg-secondary, #1f2937)', borderRadius: '8px', padding: '0.75rem',
      border: '1px solid var(--border, #374151)',
    }}>
      <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem' }}>Radiation</h3>
      <div style={{ fontSize: '1.8rem', fontWeight: 700, fontFamily: 'monospace', color: tid > 30 ? '#ef4444' : tid > 10 ? '#f59e0b' : '#10b981' }}>
        {tid.toFixed(1)} <span style={{ fontSize: '0.8rem', fontWeight: 400 }}>krad</span>
      </div>
      <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginBottom: '0.3rem' }}>Total mission dose</div>
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{
          fontSize: '0.7rem', padding: '0.15rem 0.5rem', borderRadius: '3px',
          background: `${classColors[elClass] || '#6b7280'}22`,
          color: classColors[elClass] || '#6b7280', fontWeight: 600,
        }}>
          {elClass.replace(/_/g, ' ')}
        </span>
        <span style={{ fontSize: '0.7rem', color: '#6b7280' }}>{env.replace(/_/g, ' ')}</span>
      </div>
    </div>
  )
}

// --- Volume + Reliability card ---
function VolumeReliabilityCard({ parameters: p }: { parameters: Record<string, DesignParam> }) {
  const get = (id: string) => { const v = p[id]; return v && typeof v.value === 'number' ? v.value : 0 }
  const getStr = (id: string) => { const v = p[id]; return v ? String(v.value) : '' }

  const volUtil = get('volume.utilisation_percent')
  const volMargin = get('volume.margin_litres')
  const reliability = get('reliability.mission_reliability')
  const spf = get('reliability.single_point_failures')
  const weakest = getStr('reliability.weakest_subsystem')

  if (!p['volume.utilisation_percent'] && !p['reliability.mission_reliability']) return null

  const volColor = volUtil > 95 ? '#ef4444' : volUtil > 80 ? '#f59e0b' : '#10b981'
  const relColor = reliability >= 0.9 ? '#10b981' : reliability >= 0.7 ? '#f59e0b' : '#ef4444'

  return (
    <div style={{
      background: 'var(--bg-secondary, #1f2937)', borderRadius: '8px', padding: '0.75rem',
      border: '1px solid var(--border, #374151)',
    }}>
      {/* Volume */}
      {p['volume.utilisation_percent'] && (
        <>
          <h3 style={{ margin: '0 0 0.4rem 0', fontSize: '0.9rem' }}>Volume</h3>
          <div style={{ height: 8, borderRadius: 4, background: '#111827', overflow: 'hidden', marginBottom: '0.3rem' }}>
            <div style={{ height: '100%', width: `${Math.min(100, volUtil)}%`, background: volColor, borderRadius: 4, transition: 'width 0.3s' }} />
          </div>
          <div style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.6rem' }}>
            {volUtil.toFixed(0)}% used — {volMargin.toFixed(1)} L margin
          </div>
        </>
      )}

      {/* Reliability */}
      {p['reliability.mission_reliability'] && (
        <>
          <h3 style={{ margin: '0 0 0.4rem 0', fontSize: '0.9rem' }}>Reliability</h3>
          <div style={{ fontSize: '1.6rem', fontWeight: 700, fontFamily: 'monospace', color: relColor }}>
            {(reliability * 100).toFixed(1)}%
          </div>
          <div style={{ fontSize: '0.72rem', color: '#9ca3af' }}>
            {spf > 0 ? <span style={{ color: '#f59e0b' }}>{spf} single-point failure{spf !== 1 ? 's' : ''}</span> : 'No single-point failures'}
            {weakest ? <span> — weakest: {weakest}</span> : ''}
          </div>
        </>
      )}
    </div>
  )
}

// --- Editable parameter row ---
function EditableParamRow({ pid, param }: { pid: string; param: DesignParam }) {
  const canEdit = useCanEditParameter(pid)
  const sendEdit = useSessionStore(s => s.sendEdit)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')

  const startEdit = () => {
    if (!canEdit || !sendEdit) return
    setDraft(param.value === null || param.value === undefined ? '' : String(param.value))
    setEditing(true)
  }

  const commit = () => {
    setEditing(false)
    if (!sendEdit || draft === String(param.value)) return
    const n = Number(draft)
    sendEdit(pid, isNaN(n) ? draft : n, {
      rationale: 'Inline edit from dashboard',
      editType: 'override',
    })
  }

  const label = pid.split('.').slice(1).join(' ').replace(/_/g, ' ')

  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', padding: '0.1rem 0.3rem', fontSize: '0.75rem',
      cursor: canEdit ? 'pointer' : 'default',
      background: editing ? 'rgba(59,130,246,0.1)' : 'transparent',
      borderRadius: '3px',
    }}
      onDoubleClick={startEdit}
    >
      <span style={{ color: '#9ca3af', flex: 1 }}>{label}</span>
      {editing ? (
        <input
          autoFocus
          value={draft}
          onChange={e => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={e => { if (e.key === 'Enter') commit(); if (e.key === 'Escape') setEditing(false) }}
          style={{
            width: '100px', fontFamily: 'monospace', fontSize: '0.75rem', fontWeight: 600,
            background: 'var(--bg-primary, #111827)', color: '#f3f4f6',
            border: '1px solid var(--accent, #3b82f6)', borderRadius: '3px',
            padding: '0 0.25rem', textAlign: 'right',
          }}
        />
      ) : (
        <span>
          <span style={{ fontFamily: 'monospace', fontWeight: 600, color: canEdit ? '#f3f4f6' : undefined }}>{formatValue(param.value)}</span>
          {param.unit && <span style={{ color: '#6b7280', marginLeft: '0.25rem', fontSize: '0.65rem' }}>{param.unit}</span>}
          {canEdit && <span style={{ color: '#3b82f6', fontSize: '0.6rem', marginLeft: '0.3rem', opacity: 0.5 }}>edit</span>}
        </span>
      )}
    </div>
  )
}

// --- Collapsible parameters section ---
function AllParameters({ parameters }: { parameters: Record<string, DesignParam> }) {
  const [open, setOpen] = useState(false)
  const hasSession = useHasActiveSession()

  return (
    <div style={{ marginTop: '1rem' }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer',
          fontSize: '0.8rem', padding: '0.3rem 0', display: 'flex', alignItems: 'center', gap: '0.3rem',
        }}
      >
        <span style={{ transform: open ? 'rotate(90deg)' : 'rotate(0)', display: 'inline-block', transition: 'transform 0.15s' }}>&#9654;</span>
        All Parameters ({Object.keys(parameters).length})
        {hasSession && <span style={{ fontSize: '0.65rem', color: '#3b82f6', marginLeft: '0.5rem' }}>double-click to edit</span>}
      </button>
      {open && (
        <div style={{ maxHeight: '50vh', overflowY: 'auto', marginTop: '0.5rem', background: 'var(--bg-secondary, #1f2937)', borderRadius: '6px', padding: '0.5rem', border: '1px solid var(--border, #374151)' }}>
          {DOMAIN_ORDER.map(domain => {
            const domainParams = Object.entries(parameters).filter(([k]) => k.startsWith(domain + '.'))
            if (domainParams.length === 0) return null
            return (
              <div key={domain} style={{ marginBottom: '0.5rem' }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', color: '#6b7280', borderBottom: '1px solid #374151', padding: '0.2rem 0', marginBottom: '0.2rem', letterSpacing: '0.05em' }}>
                  {domain}
                </div>
                {domainParams.map(([pid, p]) => (
                  <EditableParamRow key={pid} pid={pid} param={p} />
                ))}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// --- Community summary ---
function CommunityCard({ parameters: p }: { parameters: Record<string, DesignParam> }) {
  const get = (id: string) => { const v = p[id]; return v && typeof v.value === 'number' ? v.value : 0 }
  if (!p['community.societal_impact_score']) return null

  const impact = get('community.societal_impact_score')
  const openData = get('community.open_data_score')
  const educational = get('community.educational_value')
  const stakeholders = get('community.stakeholder_count')

  return (
    <div style={{
      background: 'var(--bg-secondary, #1f2937)', borderRadius: '8px', padding: '0.75rem',
      border: '1px solid var(--border, #374151)', gridColumn: '1 / -1',
    }}>
      <h3 style={{ margin: '0 0 0.4rem 0', fontSize: '0.9rem' }}>Community & Societal Impact</h3>
      <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', fontSize: '0.8rem' }}>
        <div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'monospace', color: '#3b82f6' }}>{impact.toFixed(0)}</div>
          <div style={{ fontSize: '0.65rem', color: '#9ca3af' }}>Impact Score</div>
        </div>
        <div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'monospace', color: '#10b981' }}>{openData.toFixed(0)}</div>
          <div style={{ fontSize: '0.65rem', color: '#9ca3af' }}>Open Data</div>
        </div>
        <div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'monospace', color: '#f59e0b' }}>{educational.toFixed(0)}</div>
          <div style={{ fontSize: '0.65rem', color: '#9ca3af' }}>Educational</div>
        </div>
        <div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'monospace' }}>{stakeholders.toFixed(0)}</div>
          <div style={{ fontSize: '0.65rem', color: '#9ca3af' }}>Stakeholder Groups</div>
        </div>
      </div>
    </div>
  )
}

// === MAIN DASHBOARD ===
export function MissionDashboard() {
  const { result, studyId } = useDesignStore()

  // Use result.parameters directly (stable reference) to avoid recharts infinite loop
  if (!result?.parameters) return null

  const p = result.parameters as Record<string, DesignParam>
  const get = (id: string) => { const v = p[id]; return v && typeof v.value === 'number' ? v.value : 0 }
  const getStr = (id: string) => { const v = p[id]; return v ? String(v.value) : '—' }

  const massMargin = get('systems.mass_margin_percent')
  const powerMargin = get('systems.power_margin_percent')
  const linkMargin = get('link.downlink_margin_db')
  const cost = get('cost.total_meur')
  const sustainGrade = getStr('sustainability.grade')
  const reliability = get('reliability.mission_reliability')

  const conflicts = result?.conflicts || []
  const conflictCount = conflicts.length
  const criticalCount = conflicts.filter(c => c.severity === 'critical').length

  const marginStatus = (v: number): 'green' | 'amber' | 'red' => v > 20 ? 'green' : v > 0 ? 'amber' : 'red'

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      {/* Row 1: KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '0.5rem', marginBottom: '1rem' }}>
        <KpiCard label="Mass Margin" value={`${massMargin.toFixed(0)}%`} status={marginStatus(massMargin)} />
        <KpiCard label="Power Margin" value={`${powerMargin.toFixed(0)}%`} status={marginStatus(powerMargin)} />
        <KpiCard label="Link Margin" value={`${linkMargin.toFixed(1)}`} unit="dB" status={linkMargin >= 6 ? 'green' : linkMargin >= 3 ? 'amber' : 'red'} />
        <KpiCard label="Cost" value={cost.toFixed(1)} unit="MEUR" status="blue" />
        <KpiCard label="Sustainability" value={sustainGrade} status={sustainGrade === 'A' || sustainGrade === 'B' ? 'green' : sustainGrade === 'C' ? 'amber' : 'red'} />
        <KpiCard label="Reliability" value={`${(reliability * 100).toFixed(1)}%`} status={reliability >= 0.9 ? 'green' : reliability >= 0.7 ? 'amber' : 'red'} />
        <KpiCard label="Conflicts" value={`${conflictCount}`} status={conflictCount === 0 ? 'green' : criticalCount > 0 ? 'red' : 'amber'} />
      </div>

      {/* Row 2: Charts (pure SVG — no recharts) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '0.75rem', marginBottom: '1rem' }}>
        <div className="card">
          <SVGWaterfall
            title="Mass Breakdown"
            items={[
              { label: 'Payload', value: get('payload.mass_kg') || (result?.parameters as any)?.['payload.mass_kg']?.value || 0, color: '#10b981' },
              { label: 'EPS', value: get('power.eps_mass_kg'), color: '#f59e0b' },
              { label: 'AOCS', value: get('aocs.mass_kg'), color: '#06b6d4' },
              { label: 'Comms', value: get('link.ttc_mass_kg'), color: '#ec4899' },
              { label: 'Thermal', value: get('thermal.tcs_mass_kg'), color: '#ef4444' },
              { label: 'Structure', value: get('structure.mass_kg'), color: '#84cc16' },
            ].filter(i => i.value > 0)}
            allocation={requirements.target_mass_kg || 6}
            unit="kg"
            width={380}
            height={200}
          />
        </div>
        <div className="card">
          <SVGBarChart
            title="Power Profile"
            data={[
              { label: 'Sun Demand', value: get('power.total_sunlight_w'), color: '#f59e0b' },
              { label: 'Eclipse', value: get('power.total_eclipse_w'), color: '#6b7280' },
              { label: 'SA BOL', value: get('power.sa_power_bol_w'), color: '#10b981' },
              { label: 'SA EOL', value: get('power.sa_power_eol_w'), color: '#3b82f6' },
            ].filter(d => d.value > 0)}
            unit=" W"
            width={380}
            height={200}
          />
        </div>
      </div>

      {/* Row 3: Budget Gauges */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.5rem', marginBottom: '1rem' }}>
        <BudgetGauge label="Mass" value={get('mass.dry_mass_kg')} allocation={requirements.target_mass_kg || 6} unit="kg" />
        <BudgetGauge label="Power" value={get('power.total_sunlight_w')} allocation={get('power.sa_power_eol_w') || 15} unit="W" />
        <BudgetGauge label="TTC Link" value={3} allocation={get('link.ttc_margin_db') || 3} unit="dB" />
        <BudgetGauge label="Cost" value={get('cost.total_meur') * 1000} allocation={(requirements.target_cost_meur || 2) * 1000} unit="kEUR" />
      </div>

      {/* Row 4: Analysis Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '0.75rem', marginBottom: '0.75rem' }}>
        <RadiationCard parameters={p} />
        <VolumeReliabilityCard parameters={p} />
      </div>

      {/* Row 5: Margins */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '0.75rem', marginBottom: '0.75rem' }}>
        <MarginEnforcement studyId={studyId} />
        <SpectrumSelector />
        <LaunchSelector />
      </div>

      {/* Row 5: Engineering Budgets */}
      <PointingBudget />
      <DataBudget />
      <TimingBudget />

      {/* Row 6: Community */}
      <CommunityCard parameters={p} />

      {/* Row 5: Collapsible all parameters */}
      <AllParameters parameters={p} />
    </div>
  )
}
