import { useState } from 'react'
import {
  useSnapshots,
  useCreateSnapshot,
  useDiffSnapshots,
  type ParamDelta,
} from '../hooks/useSnapshots'
import { fs } from '../theme/tokens'
import { showAlert } from './ui/Dialog'

interface Props {
  sessionId: string | null
}

export function SnapshotsPanel({ sessionId }: Props) {
  const { data: snapshots, isLoading } = useSnapshots(sessionId)
  const create = useCreateSnapshot()
  const [name, setName] = useState('')
  const [tags, setTags] = useState('')
  const [selA, setSelA] = useState<number | null>(null)
  const [selB, setSelB] = useState<number | null>(null)

  if (!sessionId) {
    return (
      <div style={{ padding: '1rem' }}>
        <p style={{ color: 'var(--text-secondary, var(--text-2))' }}>
          Join a session to create and compare named design snapshots.
        </p>
      </div>
    )
  }

  const handleCreate = async () => {
    const n = name.trim()
    if (!n) return
    try {
      await create.mutateAsync({
        sessionId,
        name: n,
        tags: tags.split(',').map(t => t.trim()).filter(Boolean),
      })
      setName('')
      setTags('')
    } catch (e) {
      void showAlert(`Snapshot failed: ${e}`)
    }
  }

  const handleToggleSelection = (id: number) => {
    if (selA === id) { setSelA(null); return }
    if (selB === id) { setSelB(null); return }
    if (selA === null) { setSelA(id); return }
    if (selB === null) { setSelB(id); return }
    // Rotate: oldest selection out, new in B
    setSelA(selB)
    setSelB(id)
  }

  return (
    <div style={{ padding: '1rem', overflowY: 'auto', height: '100%' }}>
      <h2 style={{ margin: '0 0 0.75rem 0' }}>Snapshots</h2>

      <div style={{
        background: 'var(--bg-secondary, var(--surface-2))',
        padding: '0.75rem',
        borderRadius: '6px',
        marginBottom: '1rem',
        border: '1px solid var(--border, var(--line))',
      }}>
        <label style={{ fontSize: fs.body, color: 'var(--text-secondary, var(--text-2))' }}>Name</label>
        <input
          className="input"
          placeholder="e.g. baseline, heavy-payload"
          value={name}
          onChange={e => setName(e.target.value)}
          style={{ width: '100%', marginBottom: '0.5rem' }}
        />
        <label style={{ fontSize: fs.body, color: 'var(--text-secondary, var(--text-2))' }}>
          Tags (comma-separated)
        </label>
        <input
          className="input"
          placeholder="e.g. pre-pdr, margin-check"
          value={tags}
          onChange={e => setTags(e.target.value)}
          style={{ width: '100%', marginBottom: '0.5rem' }}
        />
        <button
          className="btn btn-sm"
          onClick={handleCreate}
          disabled={create.isPending || !name.trim()}
        >
          {create.isPending ? 'Saving…' : 'Save snapshot'}
        </button>
      </div>

      {selA !== null && selB !== null && selA !== selB && (
        <DiffView a={selA} b={selB} onClear={() => { setSelA(null); setSelB(null) }} />
      )}

      {selA !== null && selB === null && (
        <div style={{
          fontSize: fs.body,
          color: 'var(--text-secondary, var(--text-2))',
          marginBottom: '0.5rem',
          padding: '0.5rem',
          background: 'rgba(59,130,246,0.08)',
          borderRadius: '4px',
        }}>
          Selected snapshot A (#{selA}). Click another snapshot to diff.
          <button className="btn btn-sm" onClick={() => setSelA(null)} style={{ marginLeft: '0.5rem' }}>
            Clear
          </button>
        </div>
      )}

      <h3 style={{ fontSize: fs.value, margin: '1rem 0 0.5rem 0' }}>
        History {snapshots && `(${snapshots.length})`}
      </h3>

      {isLoading && <div>Loading…</div>}
      {snapshots && snapshots.length === 0 && (
        <div style={{ color: 'var(--text-secondary, var(--text-2))', fontSize: fs.body }}>
          No snapshots yet. Save a baseline before making trade-space changes.
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
        {snapshots?.map(s => {
          const isA = selA === s.id
          const isB = selB === s.id
          const selected = isA || isB
          return (
            <div
              key={s.id}
              onClick={() => handleToggleSelection(s.id)}
              style={{
                cursor: 'pointer',
                padding: '0.5rem 0.7rem',
                borderRadius: '4px',
                border: `1px solid ${selected ? 'var(--accent, var(--interactive))' : 'var(--border, var(--line))'}`,
                background: selected ? 'rgba(59,130,246,0.08)' : 'var(--bg-secondary, var(--surface-2))',
                display: 'flex',
                gap: '0.5rem',
                alignItems: 'center',
              }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'baseline' }}>
                  <strong style={{ fontSize: fs.value }}>{s.name || `Snapshot #${s.id}`}</strong>
                  <span style={{
                    fontSize: fs.label,
                    padding: '0.1rem 0.3rem',
                    background: 'var(--bg-primary, var(--surface-1))',
                    borderRadius: '3px',
                    color: 'var(--text-secondary, var(--text-2))',
                  }}>
                    {s.label}
                  </span>
                </div>
                <div style={{ fontSize: fs.label, color: 'var(--text-secondary, var(--text-2))' }}>
                  v{s.version} · {new Date(s.created_at).toLocaleString()}
                  {s.tags.length > 0 && ' · ' + s.tags.join(', ')}
                </div>
              </div>
              {isA && <span style={{ fontSize: fs.label, color: 'var(--accent, var(--interactive))' }}>A</span>}
              {isB && <span style={{ fontSize: fs.label, color: 'var(--accent, var(--interactive))' }}>B</span>}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function DiffView({ a, b, onClear }: { a: number; b: number; onClear: () => void }) {
  const { data, isLoading, error } = useDiffSnapshots(a, b)

  if (isLoading) return <div style={{ padding: '0.5rem' }}>Computing diff…</div>
  if (error) return <div style={{ color: 'var(--danger, var(--status-alarm))' }}>Diff failed: {String(error)}</div>
  if (!data) return null

  return (
    <div style={{
      background: 'var(--bg-secondary, var(--surface-2))',
      border: '1px solid var(--border, var(--line))',
      borderRadius: '6px',
      padding: '0.75rem',
      marginBottom: '1rem',
    }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <h3 style={{ margin: 0, fontSize: fs.value }}>Diff</h3>
        <span style={{ fontSize: fs.label, color: 'var(--text-secondary, var(--text-2))' }}>
          A: <strong>{data.a.name || `#${data.a.id}`}</strong> → B: <strong>{data.b.name || `#${data.b.id}`}</strong>
        </span>
        <button className="btn btn-sm" onClick={onClear} style={{ marginLeft: 'auto' }}>Close</button>
      </div>
      <div style={{ display: 'flex', gap: '0.5rem', fontSize: fs.label, color: 'var(--text-secondary, var(--text-2))', marginBottom: '0.5rem' }}>
        <span>Changed: <strong style={{ color: 'var(--status-caution)' }}>{data.summary.changed}</strong></span>
        <span>Added: <strong style={{ color: 'var(--status-ok)' }}>{data.summary.added}</strong></span>
        <span>Removed: <strong style={{ color: 'var(--status-alarm)' }}>{data.summary.removed}</strong></span>
        <span>Total: {data.summary.total_diffs}</span>
      </div>
      <div style={{ maxHeight: '320px', overflowY: 'auto' }}>
        <table style={{ width: '100%', fontSize: fs.label, borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ color: 'var(--text-secondary, var(--text-2))', textAlign: 'left' }}>
              <th style={{ padding: '0.25rem 0.4rem' }}>Parameter</th>
              <th style={{ padding: '0.25rem 0.4rem' }}>A</th>
              <th style={{ padding: '0.25rem 0.4rem' }}>B</th>
              <th style={{ padding: '0.25rem 0.4rem' }}>Δ</th>
            </tr>
          </thead>
          <tbody>
            {data.deltas.slice(0, 200).map(d => (
              <DeltaRow key={d.param_id} d={d} />
            ))}
          </tbody>
        </table>
        {data.deltas.length > 200 && (
          <div style={{ fontSize: fs.label, color: 'var(--text-secondary, var(--text-2))', marginTop: '0.3rem' }}>
            … {data.deltas.length - 200} more diffs truncated.
          </div>
        )}
      </div>
    </div>
  )
}

function DeltaRow({ d }: { d: ParamDelta }) {
  const color =
    d.change_type === 'added'   ? 'var(--status-ok)' :
    d.change_type === 'removed' ? 'var(--status-alarm)' :
    d.change_type === 'changed' ? 'var(--status-caution)' : 'transparent'
  return (
    <tr style={{ borderTop: '1px solid rgba(55,65,81,0.5)' }}>
      <td style={{ padding: '0.2rem 0.4rem', fontFamily: 'monospace', fontSize: fs.value, borderLeft: `3px solid ${color}` }}>
        {d.param_id}
      </td>
      <td style={{ padding: '0.2rem 0.4rem' }}>{fmt(d.value_a)} {d.unit}</td>
      <td style={{ padding: '0.2rem 0.4rem' }}>{fmt(d.value_b)} {d.unit}</td>
      <td style={{ padding: '0.2rem 0.4rem' }}>
        {d.delta !== null && (
          <>
            <span style={{ color: (d.delta ?? 0) > 0 ? 'var(--status-ok)' : 'var(--status-alarm)' }}>
              {(d.delta ?? 0) > 0 ? '+' : ''}{(d.delta ?? 0).toFixed(3)}
            </span>
            {d.delta_percent !== null && (
              <span style={{ color: 'var(--text-secondary, var(--text-2))', marginLeft: '0.25rem' }}>
                ({(d.delta_percent ?? 0).toFixed(1)}%)
              </span>
            )}
          </>
        )}
      </td>
    </tr>
  )
}

function fmt(v: any): string {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'number') return v.toFixed(3).replace(/\.?0+$/, '')
  return String(v)
}
