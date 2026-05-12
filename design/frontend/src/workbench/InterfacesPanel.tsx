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
    enabled: !!studyId, structuralSharing: false,
  })

  const siblings = allElements.filter((el: any) =>
    focusElementId ? el.parent_id === focusElementId : !el.parent_id
  )

  // Get interfaces for study
  const { data: allInterfaces = [] } = useQuery({
    queryKey: ['interfaces', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/interfaces`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false,
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
        {interfaces.map((iface: any) => (
          <InterfaceRow key={iface.id} iface={iface} nameOf={nameOf} studyId={studyId}
            onDelete={() => deleteMutation.mutate(iface.id)} />
        ))}
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

// ─── Interface Row with expandable properties ───

const IFACE_PROPERTY_FIELDS: Record<string, Array<{ key: string; label: string; placeholder: string }>> = {
  electrical: [
    { key: 'voltage_v', label: 'Voltage (V)', placeholder: '3.3 / 5 / 28' },
    { key: 'current_a', label: 'Current (A)', placeholder: '0.5' },
    { key: 'connector', label: 'Connector', placeholder: 'Micro-D 9pin' },
    { key: 'wire_gauge', label: 'Wire gauge', placeholder: 'AWG 26' },
    { key: 'power_w', label: 'Power (W)', placeholder: '2.5' },
  ],
  data: [
    { key: 'protocol', label: 'Protocol', placeholder: 'SPI / I2C / UART / CAN / SpaceWire' },
    { key: 'baud_rate', label: 'Baud rate', placeholder: '115200 / 1 Mbps' },
    { key: 'data_format', label: 'Data format', placeholder: 'CCSDS / raw bytes' },
    { key: 'bus_width', label: 'Bus width', placeholder: '8 / 16 / 32 bit' },
    { key: 'connector', label: 'Connector', placeholder: 'Micro-D / Harwin' },
  ],
  rf: [
    { key: 'frequency_ghz', label: 'Frequency (GHz)', placeholder: '0.435 / 2.2 / 8.2' },
    { key: 'bandwidth_mhz', label: 'Bandwidth (MHz)', placeholder: '20' },
    { key: 'polarization', label: 'Polarization', placeholder: 'RHCP / linear / dual' },
    { key: 'power_dbm', label: 'TX power (dBm)', placeholder: '30' },
    { key: 'connector', label: 'RF connector', placeholder: 'SMA / N-type' },
  ],
  mechanical: [
    { key: 'mount_type', label: 'Mount type', placeholder: 'bolted / bonded / rail' },
    { key: 'fastener', label: 'Fasteners', placeholder: 'M3×8 SS / M2.5' },
    { key: 'torque_nm', label: 'Torque (Nm)', placeholder: '0.5' },
    { key: 'material', label: 'Material', placeholder: 'Al 6061-T6' },
  ],
  thermal: [
    { key: 'heat_flow_w', label: 'Heat flow (W)', placeholder: '2.0' },
    { key: 'conductance_w_k', label: 'Conductance (W/K)', placeholder: '0.5' },
    { key: 'strap_type', label: 'Thermal strap', placeholder: 'Cu braid / Al plate' },
    { key: 'interface_temp_c', label: 'Interface temp (°C)', placeholder: '20' },
  ],
}

function InterfaceRow({ iface, nameOf, studyId, onDelete }: {
  iface: any; nameOf: (id: string) => string; studyId: string | null; onDelete: () => void
}) {
  const [expanded, setExpanded] = useState(false)
  const qc = useQueryClient()
  const typeInfo = INTERFACE_TYPES.find(t => t.value === iface.interface_type)
  const props = iface.properties || {}
  const fields = IFACE_PROPERTY_FIELDS[iface.interface_type] || []

  const updateProp = async (key: string, value: string) => {
    const newProps = { ...props, [key]: value }
    await fetch(`${API}/interfaces/${iface.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ properties: newProps }),
    }).catch(() => {
      // If PATCH not supported on interfaces, store in a different way
    })
    qc.invalidateQueries({ queryKey: ['interfaces', studyId] })
  }

  return (
    <div style={{ borderRadius: '4px', background: 'var(--bg-card)', border: '1px solid var(--border)', marginBottom: '0.15rem' }}>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', padding: '0.3rem 0.5rem', cursor: 'pointer' }}
        onClick={() => setExpanded(!expanded)}>
        <span style={{ fontSize: '0.55rem', padding: '0.1rem 0.25rem', borderRadius: '2px', background: `${typeInfo?.color || '#6b7280'}20`, color: typeInfo?.color || '#6b7280', fontWeight: 600, textTransform: 'uppercase', flexShrink: 0 }}>
          {iface.interface_type}
        </span>
        <span style={{ fontWeight: 500, fontSize: '0.72rem' }}>{nameOf(iface.from_element_id)}</span>
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.65rem' }}>→</span>
        <span style={{ fontWeight: 500, fontSize: '0.72rem' }}>{nameOf(iface.to_element_id)}</span>
        {iface.name && <span style={{ color: 'var(--text-secondary)', fontSize: '0.63rem' }}>({iface.name})</span>}
        <span style={{ flex: 1 }} />
        {Object.keys(props).length > 0 && (
          <span style={{ fontSize: '0.5rem', color: 'var(--success)' }}>{Object.keys(props).length} props</span>
        )}
        <span style={{ fontSize: '0.6rem', color: 'var(--text-secondary)' }}>{expanded ? '▾' : '▸'}</span>
        <button onClick={e => { e.stopPropagation(); onDelete() }}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--danger)', fontSize: '0.72rem' }}>×</button>
      </div>

      {/* Expandable properties */}
      {expanded && fields.length > 0 && (
        <div style={{ padding: '0.3rem 0.5rem', borderTop: '1px solid var(--border)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.2rem' }}>
          {fields.map(f => (
            <div key={f.key} style={{ fontSize: '0.6rem' }}>
              <label style={{ color: 'var(--text-secondary)', display: 'block', marginBottom: '0.05rem' }}>{f.label}:</label>
              <input value={props[f.key] || ''} onChange={e => updateProp(f.key, e.target.value)}
                placeholder={f.placeholder}
                style={{ width: '100%', padding: '0.15rem 0.25rem', fontSize: '0.6rem', borderRadius: '2px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
