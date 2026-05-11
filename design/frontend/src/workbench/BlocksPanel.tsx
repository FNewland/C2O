/**
 * BlocksPanel — Add, remove, rename, scope, and freeze elements.
 *
 * All mutations go through the server API. React Query invalidation
 * causes BlockDiagram to re-render with fresh data.
 */
import { useState, useCallback, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useUIStore, type Level } from '../stores/uiStore'
import { EquipmentBrowser } from './EquipmentBrowser'
import { DesignTools } from './DesignTools'

const API = '/api'

const ELEMENT_TYPES_BY_LEVEL: Record<Level, Array<{ value: string; label: string }>> = {
  0: [
    { value: 'segment', label: 'Segment' },
  ],
  1: [
    { value: 'system', label: 'System' },
  ],
  2: [
    { value: 'subsystem', label: 'Subsystem' },
  ],
  3: [
    { value: 'component', label: 'Component' },
  ],
  4: [],
}

const DOMAIN_OPTIONS = [
  { value: '', label: '(none)' },
  { value: 'payload', label: 'Payload' },
  { value: 'power', label: 'Power (EPS)' },
  { value: 'aocs', label: 'AOCS' },
  { value: 'ttc', label: 'Comms (TTC)' },
  { value: 'thermal', label: 'Thermal' },
  { value: 'structure', label: 'Structure' },
  { value: 'propulsion', label: 'Propulsion' },
  { value: 'obc', label: 'OBC / C&DH' },
  { value: 'ground', label: 'Ground' },
]

const SEGMENT_OPTIONS = [
  { value: 'space', label: 'Space' },
  { value: 'ground', label: 'Ground' },
  { value: 'launch', label: 'Launch' },
  { value: 'operations', label: 'Operations' },
  { value: 'user', label: 'User' },
]

// ─── Inline Edit Component ───

function InlineEdit({ value, onCommit, style, inputStyle }: {
  value: string
  onCommit: (newValue: string) => void
  style?: React.CSSProperties
  inputStyle?: React.CSSProperties
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [editing])

  if (!editing) {
    return (
      <span
        onClick={() => { setDraft(value); setEditing(true) }}
        style={{ cursor: 'pointer', ...style }}
        title="Click to edit"
      >
        {value}
      </span>
    )
  }

  return (
    <input
      ref={inputRef}
      value={draft}
      onChange={e => setDraft(e.target.value)}
      onKeyDown={e => {
        if (e.key === 'Enter') {
          if (draft && draft !== value) onCommit(draft)
          setEditing(false)
        } else if (e.key === 'Escape') {
          setEditing(false)
        }
      }}
      onBlur={() => {
        if (draft && draft !== value) onCommit(draft)
        setEditing(false)
      }}
      style={{
        padding: '0.1rem 0.3rem', fontSize: 'inherit', borderRadius: '3px',
        background: 'var(--bg-primary)', border: '1px solid var(--accent)',
        color: 'var(--text-primary)', outline: 'none',
        ...inputStyle,
      }}
    />
  )
}

export function BlocksPanel() {
  const studyId = useUIStore(s => s.studyId)
  const focusElementId = useUIStore(s => s.focusElementId)
  const currentLevel = useUIStore(s => s.currentLevel)
  const qc = useQueryClient()

  // Elements at current focus
  const { data: allElements = [] } = useQuery({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId,
  })

  const children = allElements.filter((el: any) =>
    focusElementId ? el.parent_id === focusElementId : !el.parent_id
  )

  // Add element form state
  const [showAdd, setShowAdd] = useState(false)
  const [newName, setNewName] = useState('')
  const [newType, setNewType] = useState('')
  const [newSegment, setNewSegment] = useState('space')
  const [newDomain, setNewDomain] = useState('')

  const addMutation = useMutation({
    mutationFn: async () => {
      const body: any = {
        name: newName,
        element_type: newType || ({ 0: 'segment', 1: 'system', 2: 'subsystem', 3: 'component' }[currentLevel] || 'system'),
        parent_id: focusElementId || undefined,
        segment: newSegment,
      }
      // For mission root (level 0, no focus), create mission element
      if (currentLevel === 0 && !focusElementId) {
        body.element_type = 'mission'
      }
      if (newDomain) body.subsystem_domain = newDomain
      const res = await fetch(`${API}/elements/?study_id=${studyId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(await res.text())
      return res.json()
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['elements', studyId] })
      setNewName('')
      setShowAdd(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (elementId: string) => {
      const res = await fetch(`${API}/elements/${elementId}`, { method: 'DELETE' })
      if (!res.ok) throw new Error(await res.text())
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['elements', studyId] }),
  })

  const getVersion = (elementId: string) => {
    const el = allElements.find((e: any) => e.id === elementId)
    return el?.version || 1
  }

  const patchElement = useCallback(async (elementId: string, patch: Record<string, any>) => {
    const res = await fetch(`${API}/elements/${elementId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...patch, version: getVersion(elementId) }),
    })
    if (res.ok) {
      qc.invalidateQueries({ queryKey: ['elements', studyId] })
    }
  }, [studyId, qc, allElements])

  const toggleScope = useCallback(async (elementId: string, currentScope: boolean) => {
    await fetch(`${API}/elements/${elementId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ in_scope: !currentScope, version: getVersion(elementId) }),
    })
    qc.invalidateQueries({ queryKey: ['elements', studyId] })
  }, [studyId, qc, allElements])

  const toggleFreeze = useCallback(async (elementId: string, currentFrozen: boolean) => {
    await fetch(`${API}/elements/${elementId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ frozen: !currentFrozen, version: getVersion(elementId) }),
    })
    qc.invalidateQueries({ queryKey: ['elements', studyId] })
  }, [studyId, qc, allElements])

  const typeOptions = ELEMENT_TYPES_BY_LEVEL[currentLevel] || []

  return (
    <div style={{ padding: '0.5rem 1rem', fontSize: '0.75rem' }}>
      {/* Element list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', marginBottom: '0.5rem' }}>
        {children.length === 0 && !showAdd && (
          <div style={{ color: 'var(--text-secondary)', padding: '0.5rem 0' }}>
            No elements at this level. Click "Add Element" to start.
          </div>
        )}
        {children.map((el: any) => (
          <div key={el.id} style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            padding: '0.3rem 0.5rem', borderRadius: '4px',
            background: 'var(--bg-card)', border: '1px solid var(--border)',
          }}>
            <span style={{
              fontSize: '0.55rem', padding: '0.1rem 0.3rem', borderRadius: '3px',
              background: 'rgba(59,130,246,0.15)', color: 'var(--accent)',
              fontWeight: 600, textTransform: 'uppercase',
            }}>
              {el.subsystem_domain || el.element_type}
            </span>
            <InlineEdit
              value={el.name}
              onCommit={(v) => patchElement(el.id, { name: v })}
              style={{ fontWeight: 500, flex: 1 }}
              inputStyle={{ width: 120, fontWeight: 500 }}
            />

            {el.mass_kg != null && (
              <InlineEdit
                value={el.mass_kg.toFixed(1)}
                onCommit={(v) => { const n = parseFloat(v); if (!isNaN(n)) patchElement(el.id, { mass_kg: n }) }}
                style={{ color: 'var(--text-secondary)', fontSize: '0.65rem' }}
                inputStyle={{ width: 50, fontSize: '0.65rem', textAlign: 'right' }}
              />
            )}
            {el.mass_kg != null && (
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.65rem' }}>kg</span>
            )}

            {el.power_avg_w != null && (
              <InlineEdit
                value={el.power_avg_w.toFixed(1)}
                onCommit={(v) => { const n = parseFloat(v); if (!isNaN(n)) patchElement(el.id, { power_avg_w: n }) }}
                style={{ color: 'var(--text-secondary)', fontSize: '0.65rem' }}
                inputStyle={{ width: 50, fontSize: '0.65rem', textAlign: 'right' }}
              />
            )}
            {el.power_avg_w != null && (
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.65rem' }}>W</span>
            )}

            {/* Quantity */}
            {(el.quantity || 1) > 1 ? (
              <span style={{
                fontSize: '0.6rem', padding: '0.05rem 0.25rem', borderRadius: '3px',
                background: 'rgba(59,130,246,0.15)', color: 'var(--accent)', fontWeight: 600,
                cursor: 'pointer',
              }}
              onClick={() => {
                const q = prompt(`Quantity for "${el.name}":`, String(el.quantity || 1))
                if (q && !isNaN(Number(q))) {
                  fetch(`${API}/elements/${el.id}`, {
                    method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ quantity: Number(q), version: getVersion(el.id) }),
                  }).then(() => qc.invalidateQueries({ queryKey: ['elements', studyId] }))
                }
              }}
              title="Click to change quantity">
                ×{el.quantity}
              </span>
            ) : (
              <button
                onClick={() => {
                  const q = prompt(`Quantity for "${el.name}":`, '1')
                  if (q && Number(q) > 1) {
                    fetch(`${API}/elements/${el.id}`, {
                      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ quantity: Number(q), version: getVersion(el.id) }),
                    }).then(() => qc.invalidateQueries({ queryKey: ['elements', studyId] }))
                  }
                }}
                style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.55rem', color: 'var(--text-secondary)' }}
                title="Set quantity (for duplicates/constellation)"
              >
                qty
              </button>
            )}

            {/* Scope toggle */}
            <button
              onClick={() => toggleScope(el.id, el.in_scope !== false)}
              title={el.in_scope === false ? 'Mark in-scope' : 'Mark out-of-scope'}
              style={{
                background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.65rem',
                color: el.in_scope === false ? '#6b7280' : 'var(--success)',
              }}
            >
              {el.in_scope === false ? 'EXT' : 'IN'}
            </button>

            {/* Freeze toggle */}
            <button
              onClick={() => toggleFreeze(el.id, !!el.frozen)}
              title={el.frozen ? 'Unfreeze' : 'Freeze'}
              style={{
                background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.65rem',
                color: el.frozen ? 'var(--warning)' : 'var(--text-secondary)',
              }}
            >
              {el.frozen ? 'FROZEN' : 'freeze'}
            </button>

            {/* Delete */}
            {!el.frozen && (
              <button
                onClick={() => {
                  if (confirm(`Delete "${el.name}" and all its children?`)) {
                    deleteMutation.mutate(el.id)
                  }
                }}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'var(--danger)', fontSize: '0.75rem',
                }}
              >
                ×
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Add element form */}
      {showAdd ? (
        <div style={{
          display: 'flex', gap: '0.4rem', alignItems: 'center', flexWrap: 'wrap',
          padding: '0.4rem', background: 'var(--bg-card)', borderRadius: '4px', border: '1px solid var(--accent)',
        }}>
          <input
            value={newName}
            onChange={e => setNewName(e.target.value)}
            placeholder="Element name"
            autoFocus
            style={{
              padding: '0.3rem 0.5rem', fontSize: '0.72rem', borderRadius: '3px',
              background: 'var(--bg-primary)', border: '1px solid var(--border)',
              color: 'var(--text-primary)', width: 140,
            }}
            onKeyDown={e => e.key === 'Enter' && newName && addMutation.mutate()}
          />

          {typeOptions.length > 0 && (
            <select
              value={newType}
              onChange={e => setNewType(e.target.value)}
              style={{
                padding: '0.3rem', fontSize: '0.72rem', borderRadius: '3px',
                background: 'var(--bg-primary)', border: '1px solid var(--border)',
                color: 'var(--text-primary)',
              }}
            >
              {typeOptions.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          )}

          {currentLevel === 0 && (
            <select
              value={newSegment}
              onChange={e => setNewSegment(e.target.value)}
              style={{
                padding: '0.3rem', fontSize: '0.72rem', borderRadius: '3px',
                background: 'var(--bg-primary)', border: '1px solid var(--border)',
                color: 'var(--text-primary)',
              }}
            >
              {SEGMENT_OPTIONS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          )}

          {(currentLevel >= 1) && (
            <select
              value={newDomain}
              onChange={e => setNewDomain(e.target.value)}
              style={{
                padding: '0.3rem', fontSize: '0.72rem', borderRadius: '3px',
                background: 'var(--bg-primary)', border: '1px solid var(--border)',
                color: 'var(--text-primary)',
              }}
            >
              {DOMAIN_OPTIONS.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
            </select>
          )}

          <button
            onClick={() => newName && addMutation.mutate()}
            disabled={!newName || addMutation.isPending}
            style={{
              padding: '0.3rem 0.6rem', fontSize: '0.72rem', fontWeight: 600,
              borderRadius: '3px', background: 'var(--accent)', color: 'white',
              border: 'none', cursor: 'pointer',
            }}
          >
            Add
          </button>
          <button
            onClick={() => setShowAdd(false)}
            style={{
              padding: '0.3rem 0.6rem', fontSize: '0.72rem',
              borderRadius: '3px', background: 'var(--bg-secondary)', color: 'var(--text-secondary)',
              border: 'none', cursor: 'pointer',
            }}
          >
            Cancel
          </button>
        </div>
      ) : (
        <button
          onClick={() => {
            setNewType(typeOptions[0]?.value || 'segment')
            setShowAdd(true)
          }}
          style={{
            padding: '0.35rem 0.75rem', fontSize: '0.72rem', fontWeight: 600,
            borderRadius: '4px', background: 'var(--accent)', color: 'white',
            border: 'none', cursor: 'pointer',
          }}
        >
          + Add Element
        </button>
      )}

      {/* Design Tools (constellation orbit, ground station config) */}
      <DesignTools />

      {/* Equipment Browser at Level 3 */}
      {currentLevel === 3 && (
        <div style={{ marginTop: '0.5rem', borderTop: '1px solid var(--border)', paddingTop: '0.5rem' }}>
          <EquipmentBrowser />
        </div>
      )}

      {/* Design Assist */}
      <DesignAssist studyId={studyId} focusElementId={focusElementId} currentLevel={currentLevel} />
    </div>
  )
}

// ─── Design Assist: presets + suggested requirements ───

interface PresetChild { name: string; type: string; domain?: string; segment?: string; quantity?: number; performance?: Record<string, any> }
const PRESETS_BY_LEVEL: Record<number, Array<{ id: string; name: string; description: string; children: PresetChild[] }>> = {
  0: [
    {
      id: 'cubesat-mission', name: 'CubeSat LEO Mission',
      description: 'Space, Ground, Launch, and Operations segments for a CubeSat',
      children: [
        { name: 'Space Segment', type: 'segment', segment: 'space' },
        { name: 'Ground Segment', type: 'segment', segment: 'ground' },
        { name: 'Launch Segment', type: 'segment', segment: 'launch' },
        { name: 'Operations', type: 'segment', segment: 'operations' },
      ],
    },
    {
      id: 'constellation-mission', name: 'CubeSat Constellation',
      description: 'Space (multi-sat), Ground, Launch, User, and Operations segments',
      children: [
        { name: 'Space Segment', type: 'segment', segment: 'space' },
        { name: 'Ground Segment', type: 'segment', segment: 'ground' },
        { name: 'Launch Segment', type: 'segment', segment: 'launch' },
        { name: 'User Segment', type: 'segment', segment: 'user' },
        { name: 'Operations', type: 'segment', segment: 'operations' },
      ],
    },
    {
      id: 'drone-mission', name: 'Drone / UAV Network',
      description: 'Non-space alternative: drone fleet, ground control, operations',
      children: [
        { name: 'Air Segment', type: 'segment', segment: 'space' },
        { name: 'Ground Control', type: 'segment', segment: 'ground' },
        { name: 'Communications', type: 'segment', segment: 'ground' },
        { name: 'Operations', type: 'segment', segment: 'operations' },
      ],
    },
    {
      id: 'balloon-mission', name: 'Stratospheric Balloon',
      description: 'Non-space alternative: balloon platform with ground station',
      children: [
        { name: 'Balloon Platform', type: 'segment', segment: 'space' },
        { name: 'Ground Station', type: 'segment', segment: 'ground' },
        { name: 'Launch & Recovery', type: 'segment', segment: 'launch' },
        { name: 'Operations', type: 'segment', segment: 'operations' },
      ],
    },
    {
      id: 'ground-sensor-network', name: 'Ground Sensor Network',
      description: 'Non-space alternative: distributed ground sensors with data center',
      children: [
        { name: 'Sensor Network', type: 'segment', segment: 'ground' },
        { name: 'Communications', type: 'segment', segment: 'ground' },
        { name: 'Data Centre', type: 'segment', segment: 'ground' },
        { name: 'Operations', type: 'segment', segment: 'operations' },
      ],
    },
    {
      id: 'hybrid-mission', name: 'Hybrid Space + Ground',
      description: 'CubeSat with ground sensor network for gap-filling',
      children: [
        { name: 'Space Segment', type: 'segment', segment: 'space' },
        { name: 'Ground Sensors', type: 'segment', segment: 'ground' },
        { name: 'Ground Station', type: 'segment', segment: 'ground' },
        { name: 'Data Fusion Centre', type: 'segment', segment: 'ground' },
        { name: 'Operations', type: 'segment', segment: 'operations' },
      ],
    },
  ],
  1: [
    {
      id: 'single-spacecraft', name: 'Single Spacecraft',
      description: '1 spacecraft for the space segment',
      children: [
        { name: 'Spacecraft', type: 'system', domain: 'payload', quantity: 1 },
      ],
    },
    {
      id: 'constellation-4', name: 'Constellation (4 spacecraft)',
      description: '4 identical spacecraft in one orbital plane',
      children: [
        { name: 'Spacecraft', type: 'system', domain: 'payload', quantity: 4, performance: { constellation: true, orbital_planes: 1, sats_per_plane: 4 } },
      ],
    },
    {
      id: 'constellation-12', name: 'Constellation (3×4 = 12 spacecraft)',
      description: '12 spacecraft across 3 orbital planes',
      children: [
        { name: 'Spacecraft', type: 'system', domain: 'payload', quantity: 12, performance: { constellation: true, orbital_planes: 3, sats_per_plane: 4 } },
      ],
    },
    {
      id: 'ground-network-2', name: '2 Ground Stations',
      description: 'Primary + backup ground stations',
      children: [
        { name: 'Primary GS', type: 'system', domain: 'ground', quantity: 1, performance: { latitude: 78.2, longitude: 15.4, location: 'Svalbard' } },
        { name: 'Backup GS', type: 'system', domain: 'ground', quantity: 1, performance: { latitude: 67.9, longitude: 20.2, location: 'Kiruna' } },
      ],
    },
    {
      id: 'ground-network-3', name: '3 Ground Stations',
      description: 'Arctic + mid-lat + equatorial coverage',
      children: [
        { name: 'Arctic GS', type: 'system', domain: 'ground', quantity: 1, performance: { latitude: 78.2, longitude: 15.4, location: 'Svalbard' } },
        { name: 'Mid-Lat GS', type: 'system', domain: 'ground', quantity: 1, performance: { latitude: 47.9, longitude: 11.1, location: 'Weilheim' } },
        { name: 'Equatorial GS', type: 'system', domain: 'ground', quantity: 1, performance: { latitude: -2.2, longitude: -54.9, location: 'Kourou' } },
      ],
    },
    {
      id: 'ops-centre', name: 'Operations Centre',
      description: 'Mission control + payload processing',
      children: [
        { name: 'Mission Control Centre', type: 'system', domain: 'ground', quantity: 1 },
        { name: 'Payload Data Centre', type: 'system', domain: 'ground', quantity: 1 },
        { name: 'Flight Dynamics', type: 'system', domain: 'ground', quantity: 1 },
      ],
    },
  ],
  2: [
    {
      id: 'standard-spacecraft-bus', name: 'Standard Spacecraft Bus',
      description: 'All subsystems for a spacecraft: Payload, EPS, AOCS, TTC, OBC, Thermal, Structure, Propulsion',
      children: [
        { name: 'Payload', type: 'subsystem', domain: 'payload' },
        { name: 'EPS', type: 'subsystem', domain: 'power' },
        { name: 'AOCS', type: 'subsystem', domain: 'aocs' },
        { name: 'TTC', type: 'subsystem', domain: 'ttc' },
        { name: 'OBC', type: 'subsystem', domain: 'obc' },
        { name: 'Thermal', type: 'subsystem', domain: 'thermal' },
        { name: 'Structure', type: 'subsystem', domain: 'structure' },
        { name: 'Propulsion', type: 'subsystem', domain: 'propulsion' },
      ],
    },
    {
      id: 'eps-subsystems', name: 'EPS Subsystems',
      description: 'Solar Array, Battery, Power Distribution, Regulation',
      children: [
        { name: 'Solar Array', type: 'subsystem', domain: 'power' },
        { name: 'Battery Pack', type: 'subsystem', domain: 'power' },
        { name: 'Power Distribution', type: 'subsystem', domain: 'power' },
        { name: 'Power Regulation', type: 'subsystem', domain: 'power' },
      ],
    },
    {
      id: 'aocs-subsystems', name: 'AOCS Subsystems',
      description: 'Sensors, Actuators, ADCS Computer',
      children: [
        { name: 'Attitude Sensors', type: 'subsystem', domain: 'aocs' },
        { name: 'Reaction Wheels', type: 'subsystem', domain: 'aocs' },
        { name: 'Magnetorquers', type: 'subsystem', domain: 'aocs' },
        { name: 'ADCS Computer', type: 'subsystem', domain: 'aocs' },
      ],
    },
    {
      id: 'ttc-subsystems', name: 'TTC Subsystems',
      description: 'Transponder, Antenna, Diplexer',
      children: [
        { name: 'Transponder', type: 'subsystem', domain: 'ttc' },
        { name: 'Antenna', type: 'subsystem', domain: 'ttc' },
        { name: 'Diplexer/Filter', type: 'subsystem', domain: 'ttc' },
      ],
    },
    {
      id: 'ground-station-subsystems', name: 'Ground Station Subsystems',
      description: 'Antenna, RF chain, Modem, Network',
      children: [
        { name: 'GS Antenna', type: 'subsystem', domain: 'ground' },
        { name: 'RF Front End', type: 'subsystem', domain: 'ground' },
        { name: 'Baseband Modem', type: 'subsystem', domain: 'ground' },
        { name: 'Network Interface', type: 'subsystem', domain: 'ground' },
      ],
    },
  ],
  3: [],
  4: [],
}

// Suggested requirements moved to RequirementsPanel (suggestedReqs.ts)

function DesignAssist({ studyId, focusElementId, currentLevel }: { studyId: string | null; focusElementId: string | null; currentLevel: Level }) {
  const [expanded, setExpanded] = useState(false)
  const [applying, setApplying] = useState(false)
  const qc = useQueryClient()

  const presets = PRESETS_BY_LEVEL[currentLevel] || []

  if (presets.length === 0) return null

  const applyPreset = async (preset: typeof presets[0]) => {
    if (!studyId) return
    setApplying(true)
    try {
      // Find or create parent element
      let parentId = focusElementId
      if (!parentId) {
        // At root level 0, create mission element first
        const res = await fetch(`${API}/elements/?study_id=${studyId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: 'Mission', element_type: 'mission', segment: 'space' }),
        })
        if (res.ok) {
          const data = await res.json()
          parentId = data.id
        }
      }
      if (!parentId) return

      // Create children
      for (let i = 0; i < preset.children.length; i++) {
        const child = preset.children[i]
        await fetch(`${API}/elements/?study_id=${studyId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: child.name,
            element_type: child.type,
            parent_id: parentId,
            segment: child.segment || 'space',
            subsystem_domain: child.domain || undefined,
            quantity: child.quantity || 1,
            performance: child.performance || undefined,
            diagram_x: 80 + (i % 4) * 200,
            diagram_y: 40 + Math.floor(i / 4) * 140,
          }),
        })
      }
      qc.invalidateQueries({ queryKey: ['elements', studyId] })
    } finally {
      setApplying(false)
    }
  }

  return (
    <div style={{ marginTop: '0.75rem', borderTop: '1px solid var(--border)', paddingTop: '0.5rem' }}>
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.72rem',
          color: 'var(--info)', fontWeight: 600, padding: 0,
        }}
      >
        {expanded ? '▾' : '▸'} Architecture Presets
      </button>

      {expanded && (
        <div style={{ marginTop: '0.4rem', display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
          {presets.map(p => (
            <button
              key={p.id}
              onClick={() => applyPreset(p)}
              disabled={applying}
              title={p.description}
              style={{
                padding: '0.3rem 0.6rem', fontSize: '0.7rem', borderRadius: '4px',
                background: 'var(--bg-card)', border: '1px solid var(--info)',
                color: 'var(--info)', cursor: 'pointer',
              }}
            >
              {p.name}
              <span style={{ fontSize: '0.55rem', color: 'var(--text-secondary)', marginLeft: '0.3rem' }}>
                ({p.children.length} blocks)
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
