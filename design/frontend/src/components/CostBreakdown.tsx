import { useCostEstimate } from '../hooks/useSession'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'

const PHASE_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']

export function CostBreakdown({ studyId }: { studyId: string | null }) {
  const { data, isLoading, error } = useCostEstimate(studyId)

  if (!studyId) return <div style={{ padding: '1rem', color: 'var(--text-secondary, #9ca3af)' }}>Run a design first to see cost breakdown.</div>
  if (isLoading) return <div className="loading"><div className="spinner" /> Estimating cost...</div>
  if (error) return <div className="warning-item">Cost estimation failed: {String(error)}</div>

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

      {/* Cost distribution histogram */}
      {histData.length > 0 && (
        <div className="card">
          <h3>Cost Distribution</h3>
          <div style={{ width: '100%', height: '200px' }}>
            <ResponsiveContainer>
              <BarChart data={histData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="bin" tick={{ fontSize: 10, fill: '#9ca3af' }} />
                <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} />
                <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #374151', fontSize: '0.75rem' }} />
                <Bar dataKey="count" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Phase distribution */}
      {phaseData.length > 0 && (
        <div className="card">
          <h3>Phase Distribution</h3>
          <div style={{ width: '100%', height: '220px' }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={phaseData} dataKey="value" nameKey="name" outerRadius={80} label={(e: any) => `${e.name}: ${(e.value / 1000).toFixed(1)}M`}>
                  {phaseData.map((_, i) => <Cell key={i} fill={PHASE_COLORS[i]} />)}
                </Pie>
                <Legend wrapperStyle={{ fontSize: '0.75rem' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
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
