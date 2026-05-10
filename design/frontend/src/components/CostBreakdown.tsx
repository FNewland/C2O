import { useState } from 'react'
import { useCostEstimate } from '../hooks/useSession'
import { useDesignStore } from '../stores/designStore'
import { useEquipmentView } from '../hooks/useEquipmentView'
import { SVGBarChart } from '../charts/SVGBarChart'

const PHASE_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']

export function CostBreakdown({ studyId }: { studyId: string | null }) {
  const { data, isLoading, error } = useCostEstimate(studyId)
  const selectedEquipment = useEquipmentView()
  const [costOverrides, setCostOverrides] = useState<Record<string, number>>({})

  const getEquipCost = (id: string, defaultCost: number) => costOverrides[id] ?? defaultCost
  const totalEquipCost = selectedEquipment.reduce((s, eq) => s + getEquipCost(eq.componentId, eq.cost_keur) * eq.quantity, 0)

  const hasDesignResult = !!useDesignStore(s => s.result)

  if (!studyId || !hasDesignResult) return (
    <div style={{ padding: '2rem', color: '#6b7280' }}>
      <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem', color: '#9ca3af' }}>Cost Estimation</h3>
      <p style={{ fontSize: '0.78rem' }}>
        Cost estimation requires a completed design run. Click "Run Design" in the sidebar first,
        then return here for parametric cost breakdown by WBS element.
      </p>
    </div>
  )
  if (isLoading) return <div className="loading"><div className="spinner" /> Estimating cost...</div>
  if (error) return (
    <div style={{ padding: '1rem', color: '#6b7280' }}>
      <p style={{ fontSize: '0.78rem', color: '#f59e0b' }}>
        Cost estimation is unavailable. The design may need to be re-run, or the backend may be restarting.
      </p>
      <p style={{ fontSize: '0.65rem', color: '#6b7280', marginTop: '0.3rem' }}>Error: {String(error)}</p>
    </div>
  )

  const d: any = data
  if (!d) return null

  const wbs: any[] = (d.wbs || []).filter((w: any) => (w.total_keur || 0) > 0)
  const risk = d.risk || {}
  const totals = d.totals || {}
  const phases = d.phases || {}

  // Histogram data for distribution chart
  const hist: number[] = risk.cost_hist || []
  const edges: number[] = risk.cost_hist_bin_edges || []
  const histData = hist.map((count, i) => ({
    bin: edges[i] ? `${(edges[i] / 1000).toFixed(1)}M` : `${i}`,
    count,
  }))

  // Phase pie chart data
  const phaseData = [
    { name: 'Phase A', value: phases.phase_a_keur || 0 },
    { name: 'Phase B', value: phases.phase_b_keur || 0 },
    { name: 'Phase C/D', value: phases.phase_cd_keur || 0 },
    { name: 'Phase E', value: phases.phase_e_keur || 0 },
  ].filter(p => p.value > 0)

  return (
    <div style={{ padding: '1rem' }}>
      <h2>Cost Breakdown (NASA CEH-Aligned)</h2>

      {/* Confidence bars */}
      <div className="card">
        <h3>Cost Confidence Intervals</h3>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary, #9ca3af)', marginBottom: '0.5rem' }}>
          Monte Carlo (n=1000) · Model: {d.model_used}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem' }}>
          {[
            { label: 'P50', value: risk.p50_meur, color: 'var(--success, #10b981)' },
            { label: 'P70', value: risk.p70_meur, color: 'var(--accent, #3b82f6)' },
            { label: 'P80', value: risk.p80_meur, color: 'var(--warning, #f59e0b)' },
            { label: 'P90', value: risk.p90_meur, color: 'var(--danger, #ef4444)' },
          ].map(p => (
            <div key={p.label} style={{
              background: 'var(--bg-primary, #111827)', padding: '0.75rem',
              borderRadius: '6px', textAlign: 'center',
              borderTop: `3px solid ${p.color}`,
            }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary, #9ca3af)' }}>{p.label}</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: p.color, fontFamily: 'monospace' }}>
                {p.value?.toFixed(1) || '—'}
              </div>
              <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary, #9ca3af)' }}>MEUR</div>
            </div>
          ))}
        </div>
      </div>

      {/* Cost distribution histogram (SVG) */}
      {histData.length > 0 && (
        <div className="card">
          <h3>Cost Distribution</h3>
          <SVGBarChart
            data={histData.map((h: any) => ({ label: h.bin, value: h.count, color: '#3b82f6' }))}
            width={500} height={200} unit="" title=""
          />
        </div>
      )}

      {/* Phase distribution (simple bar instead of pie) */}
      {phaseData.length > 0 && (
        <div className="card">
          <h3>Phase Distribution</h3>
          <SVGBarChart
            data={phaseData.map((p: any, i: number) => ({ label: p.name, value: p.value / 1000, color: PHASE_COLORS[i] }))}
            width={400} height={180} unit="M" orientation="horizontal"
          />
        </div>
      )}

      {/* Equipment costs (bottom-up from selections) */}
      {selectedEquipment.length > 0 && (
        <div className="card">
          <h3>Equipment Costs (Bottom-Up)</h3>
          <p style={{ fontSize: '0.72rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
            From selected hardware. Edit costs to override catalogue values.
          </p>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-secondary, #1f2937)' }}>
                <th style={th}>Component</th>
                <th style={th}>Subsystem</th>
                <th style={thNum}>Qty</th>
                <th style={thNum}>Unit Cost (kEUR)</th>
                <th style={thNum}>Line Total (kEUR)</th>
              </tr>
            </thead>
            <tbody>
              {selectedEquipment.map(eq => (
                <tr key={eq.componentId} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={td}>{eq.name}</td>
                  <td style={{ ...td, color: '#6b7280' }}>{eq.category}</td>
                  <td style={tdNum}>{eq.quantity}</td>
                  <td style={tdNum}>
                    <input className="input" type="number" step={1}
                      value={getEquipCost(eq.componentId, eq.cost_keur)}
                      onChange={e => setCostOverrides(prev => ({ ...prev, [eq.componentId]: Number(e.target.value) }))}
                      style={{ width: '70px', fontSize: '0.72rem', textAlign: 'right' }} />
                  </td>
                  <td style={{ ...tdNum, fontWeight: 600 }}>
                    {(getEquipCost(eq.componentId, eq.cost_keur) * eq.quantity).toLocaleString()}
                  </td>
                </tr>
              ))}
              <tr style={{ background: 'var(--bg-secondary, #1f2937)', fontWeight: 700 }}>
                <td style={td} colSpan={3}>Total Equipment (Hardware)</td>
                <td style={tdNum}></td>
                <td style={tdNum}>{totalEquipCost.toLocaleString()} kEUR</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {/* WBS table */}
      <div className="card">
        <h3>Work Breakdown Structure</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
          <thead>
            <tr style={{ background: 'var(--bg-secondary, #1f2937)' }}>
              <th style={th}>WBS</th>
              <th style={th}>Element</th>
              <th style={thNum}>DDT&E (kEUR)</th>
              <th style={thNum}>Recurring (kEUR)</th>
              <th style={thNum}>Total (kEUR)</th>
            </tr>
          </thead>
          <tbody>
            {wbs.map((w: any) => (
              <tr key={w.wbs_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ ...td, fontFamily: 'monospace' }}>{w.wbs_id}</td>
                <td style={td}>{w.name}</td>
                <td style={tdNum}>{(w.ddte_keur || 0).toLocaleString()}</td>
                <td style={tdNum}>{(w.recurring_keur || 0).toLocaleString()}</td>
                <td style={{ ...tdNum, fontWeight: 600 }}>{(w.total_keur || 0).toLocaleString()}</td>
              </tr>
            ))}
            <tr style={{ background: 'var(--bg-secondary, #1f2937)', fontWeight: 700 }}>
              <td style={td}></td>
              <td style={td}>Total Life-Cycle Cost</td>
              <td style={tdNum}>—</td>
              <td style={tdNum}>—</td>
              <td style={tdNum}>{(totals.total_lcc_keur || 0).toLocaleString()} ({(totals.total_lcc_meur || 0).toFixed(1)} MEUR)</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}

const th: React.CSSProperties = { padding: '0.5rem', textAlign: 'left', fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-secondary, #9ca3af)', letterSpacing: '0.03em' }
const thNum: React.CSSProperties = { ...th, textAlign: 'right' }
const td: React.CSSProperties = { padding: '0.4rem 0.5rem', verticalAlign: 'top' }
const tdNum: React.CSSProperties = { ...td, textAlign: 'right', fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }
