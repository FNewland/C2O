/**
 * InterfacesPanel — Define connections between sibling elements.
 *
 * Shows interfaces involving elements at the current level.
 * Create/delete via API. Type, direction, endpoints.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useUIStore } from '../stores/uiStore'

const API = '/api'

const INTERFACE_TYPES = [
  { value: 'electrical', label: 'Electrical', color: '#f59e0b' },
  { value: 'data', label: 'Data', color: '#8b5cf6' },
  { value: 'rf', label: 'RF', color: '#ec4899' },
  { value: 'mechanical', label: 'Mechanical', color: '#84cc16' },
  { value: 'thermal', label: 'Thermal', color: '#ef4444' },
]

export function InterfacesPanel() {
  const studyId = useUIStore(s => s.studyId)
  const focusElementId = useUIStore(s => s.focusElementId)
  const qc = useQueryClient()

  // Get sibling elements at current level
  const { data: allElements = [] } = useQuery({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId,
  })

  const siblings = allElements.filter((el: any) =>
    focusElementId ? el.parent_id === focusElementId : !el.parent_id
  )

  // Get interfaces for study
  const { data: allInterfaces = [] } = useQuery({
    queryKey: ['interfaces', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/interfaces`).then(r => r.json()),
    enabled: !!studyId,
  })

  // Filter to interfaces between visible siblings
  const siblingIds = new Set(siblings.map((s: any) => s.id))
  const interfaces = allInterfaces.filter((iface: any) =>
    siblingIds.has(iface.from_element_id) && siblingIds.has(iface.to_element_id)
  )

  // Name lookup
  const nameOf = (id: string) => allElements.find((e: any) => e.id === id)?.name || id.slice(0, 8)

  // Add form state
  const [showAdd, setShowAdd] = useState(false)
  const [fromId, setFromId] = useState('')
  const [toId, setToId] = useState('')
  const [ifaceType, setIfaceType] = useState('data')
  const [ifaceName, setIfaceName] = useState('')

  const addMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API}/interfaces/?study_id=${studyId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: ifaceName || `${nameOf(fromId)} → ${nameOf(toId)}`,
          interface_type: ifaceType,
          direction: 'bidirectional',
          from_element_id: fromId,
          to_element_id: toId,
          diagram_label: ifaceName || ifaceType,
        }),
      })
      if (!res.ok) throw new Error(await res.text())
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['interfaces', studyId] })
      setIfaceName('')
      setShowAdd(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (ifaceId: string) => {
      await fetch(`${API}/interfaces/${ifaceId}`, { method: 'DELETE' })
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['interfaces', studyId] }),
  })

  if (siblings.length < 2) {
    return (
      <div style={{ padding: '1rem', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
        Need at least 2 elements at this level to define interfaces.
      </div>
    )
  }

  return (
    <div style={{ padding: '0.5rem 1rem', fontSize: '0.75rem' }}>
      <div style={{ fontWeight: 600, fontSize: '0.78rem', marginBottom: '0.5rem' }}>
        Interfaces ({interfaces.length})
      </div>

      {/* Interface list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', marginBottom: '0.5rem' }}>
        {interfaces.length === 0 && !showAdd && (
          <div style={{ color: 'var(--text-secondary)', padding: '0.5rem 0' }}>
            No interfaces defined. Click "Add Interface" to connect elements.
          </div>
        )}
        {interfaces.map((iface: any) => {
          const typeInfo = INTERFACE_TYPES.find(t => t.value === iface.interface_type)
          return (
            <div key={iface.id} style={{
              display: 'flex', alignItems: 'center', gap: '0.4rem',
              padding: '0.3rem 0.5rem', borderRadius: '4px',
              background: 'var(--bg-card)', border: '1px solid var(--border)',
            }}>
              {/* Type badge */}
              <span style={{
                fontSize: '0.55rem', padding: '0.1rem 0.3rem', borderRadius: '2px',
                background: `${typeInfo?.color || '#6b7280'}20`,
                color: typeInfo?.color || '#6b7280',
                fontWeight: 600, textTransform: 'uppercase', flexShrink: 0,
              }}>
                {iface.interface_type}
              </span>

              {/* From → To */}
              <span style={{ fontWeight: 500 }}>{nameOf(iface.from_element_id)}</span>
              <span style={{ color: 'var(--text-secondary)' }}>→</span>
              <span style={{ fontWeight: 500 }}>{nameOf(iface.to_element_id)}</span>

              {/* Name/label */}
              {iface.name && (
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.68rem', flex: 1 }}>
                  ({iface.name})
                </span>
              )}

              <span style={{ flex: 1 }} />

              {/* Delete */}
              <button
                onClick={() => deleteMutation.mutate(iface.id)}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'var(--danger)', fontSize: '0.75rem',
                }}
              >
                ×
              </button>
            </div>
          )
        })}
      </div>

      {/* Add form */}
      {showAdd ? (
        <div style={{
          display: 'flex', gap: '0.4rem', alignItems: 'center', flexWrap: 'wrap',
          padding: '0.4rem', background: 'var(--bg-card)', borderRadius: '4px', border: '1px solid var(--success)',
        }}>
          <select
            value={fromId}
            onChange={e => setFromId(e.target.value)}
            style={{
              padding: '0.3rem', fontSize: '0.72rem', borderRadius: '3px',
              background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)',
            }}
          >
            <option value="">From...</option>
            {siblings.map((el: any) => <option key={el.id} value={el.id}>{el.name}</option>)}
          </select>

          <span style={{ color: 'var(--text-secondary)' }}>→</span>

          <select
            value={toId}
            onChange={e => setToId(e.target.value)}
            style={{
              padding: '0.3rem', fontSize: '0.72rem', borderRadius: '3px',
              background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)',
            }}
          >
            <option value="">To...</option>
            {siblings.filter((el: any) => el.id !== fromId).map((el: any) => (
              <option key={el.id} value={el.id}>{el.name}</option>
            ))}
          </select>

          <select
            value={ifaceType}
            onChange={e => setIfaceType(e.target.value)}
            style={{
              padding: '0.3rem', fontSize: '0.72rem', borderRadius: '3px',
              background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)',
            }}
          >
            {INTERFACE_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>

          <input
            value={ifaceName}
            onChange={e => setIfaceName(e.target.value)}
            placeholder="Label (optional)"
            style={{
              width: 120, padding: '0.3rem 0.4rem', fontSize: '0.72rem', borderRadius: '3px',
              background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)',
            }}
          />

          <button
            onClick={() => fromId && toId && addMutation.mutate()}
            disabled={!fromId || !toId}
            style={{
              padding: '0.3rem 0.6rem', fontSize: '0.72rem', fontWeight: 600, borderRadius: '3px',
              background: 'var(--success)', color: 'white', border: 'none', cursor: 'pointer',
            }}
          >
            Add
          </button>
          <button
            onClick={() => setShowAdd(false)}
            style={{
              padding: '0.3rem 0.6rem', fontSize: '0.72rem', borderRadius: '3px',
              background: 'var(--bg-secondary)', color: 'var(--text-secondary)', border: 'none', cursor: 'pointer',
            }}
          >
            Cancel
          </button>
        </div>
      ) : (
        <button
          onClick={() => setShowAdd(true)}
          style={{
            padding: '0.35rem 0.75rem', fontSize: '0.72rem', fontWeight: 600, borderRadius: '4px',
            background: 'var(--success)', color: 'white', border: 'none', cursor: 'pointer',
          }}
        >
          + Add Interface
        </button>
      )}
    </div>
  )
}
