/**
 * BlocksPanel — Add, remove, rename, scope, and freeze elements.
 *
 * All mutations go through the server API. React Query invalidation
 * causes BlockDiagram to re-render with fresh data.
 */
import { useState, useCallback, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { useUIStore, type Level } from '../stores/uiStore'
import { EquipmentBrowser } from './EquipmentBrowser'
import { DesignTools } from './DesignTools'
import { useCollaboration } from './useCollaboration'

import { ParameterSection } from '../components/ParameterPanel'

const API = '/api'

// Option values are stored enums; only the labels are translated (display time).
const elementTypesByLevel = (t: TFunction): Record<Level, Array<{ value: string; label: string }>> => ({
  0: [
    { value: 'segment', label: t('Segment') },
  ],
  1: [
    { value: 'system', label: t('System') },
  ],
  2: [
    { value: 'subsystem', label: t('Subsystem') },
  ],
  3: [
    { value: 'component', label: t('Component') },
  ],
  4: [],
})

const domainOptions = (t: TFunction) => [
  { value: '', label: t('(none)') },
  { value: 'payload', label: t('Payload') },
  { value: 'power', label: t('Power (EPS)') },
  { value: 'aocs', label: t('AOCS') },
  { value: 'ttc', label: t('Comms (TTC)') },
  { value: 'thermal', label: t('Thermal') },
  { value: 'structure', label: t('Structure') },
  { value: 'propulsion', label: t('Propulsion') },
  { value: 'obc', label: t('OBC / C&DH') },
  { value: 'ground', label: t('Ground') },
]

const segmentOptions = (t: TFunction) => [
  { value: 'space', label: t('Space') },
  { value: 'ground', label: t('Ground') },
  { value: 'launch', label: t('Launch') },
  { value: 'operations', label: t('Operations') },
  { value: 'user', label: t('User') },
]

/**
 * Element names created by the presets (PRESETS_BY_LEVEL children, the root 'Mission').
 * They are stored in English; while an element still carries one of these exact names it is
 * shown translated. A renamed element is user data and is shown as typed.
 */
// English text is the i18n key
export const SEED_ELEMENT_NAMES = [
  'Mission', 'Space Segment', 'Ground Segment', 'Launch Segment', 'User Segment', 'Operations',
  'Air Segment', 'Ground Control', 'Communications', 'Balloon Platform', 'Ground Station', 'Launch & Recovery',
  'Sensor Network', 'Data Centre', 'Ground Sensors', 'Data Fusion Centre',
  'Spacecraft', 'Primary GS', 'Backup GS', 'Arctic GS', 'Mid-Lat GS', 'Equatorial GS',
  'Mission Control Centre', 'Payload Data Centre', 'Flight Dynamics',
  'Payload', 'Thermal', 'Structure', 'Propulsion',
  'Solar Array', 'Battery Pack', 'Power Distribution', 'Power Regulation',
  'Attitude Sensors', 'Reaction Wheels', 'Magnetorquers', 'ADCS Computer',
  'Transponder', 'Antenna', 'Diplexer/Filter',
  'GS Antenna', 'RF Front End', 'Baseband Modem', 'Network Interface',
]

/** Display name of an element: seed names translated, anything else unchanged. */
export function displayElementName(name: string, t: TFunction): string {
  return SEED_ELEMENT_NAMES.includes(name) ? t(name) : name
}

// ─── Inline Edit Component ───

function InlineEdit({ value, onCommit, style, inputStyle }: {
  value: string
  onCommit: (newValue: string) => void
  style?: React.CSSProperties
  inputStyle?: React.CSSProperties
}) {
  const { t } = useTranslation()
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
        title={t('Click to edit')}
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
  const { t } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const focusElementId = useUIStore(s => s.focusElementId)
  const currentLevel = useUIStore(s => s.currentLevel)
  const qc = useQueryClient()
  const { isLockedByOther, lockHolder, requestLock, releaseLock } = useCollaboration()

  // Elements at current focus
  const { data: allElements = [] } = useQuery({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId,
    structuralSharing: false, refetchInterval: 3000,
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

  const typeOptions = elementTypesByLevel(t)[currentLevel] || []
  const focusName = allElements.find((e: any) => e.id === focusElementId)?.name

  return (
    <div style={{ padding: '0.5rem 1rem', fontSize: '0.75rem' }}>
      {/* Element list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', marginBottom: '0.5rem' }}>
        {children.length === 0 && !showAdd && (
          <div style={{ color: 'var(--text-secondary)', padding: '0.5rem 0' }}>
            {t('No elements at this level. Click "Add Element" to start.')}
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
            {/* Lock indicator */}
            {isLockedByOther(el.id) && (
              <span style={{ fontSize: '0.5rem', padding: '0.05rem 0.2rem', borderRadius: '2px', background: 'rgba(239,68,68,0.15)', color: 'var(--danger)', fontWeight: 600, flexShrink: 0 }}
                title={t('Locked by {{name}}', { name: lockHolder(el.id) })}>
                🔒 {lockHolder(el.id)}
              </span>
            )}
            {isLockedByOther(el.id) ? (
              <span style={{ fontWeight: 500, flex: 1, color: 'var(--text-secondary)' }}>{displayElementName(el.name, t)}</span>
            ) : (
              <InlineEdit
                value={displayElementName(el.name, t)}
                onCommit={(v) => { requestLock(el.id); patchElement(el.id, { name: v }); releaseLock(el.id) }}
                style={{ fontWeight: 500, flex: 1 }}
                inputStyle={{ width: 120, fontWeight: 500 }}
              />
            )}

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
                const q = prompt(t('Quantity for "{{name}}":', { name: displayElementName(el.name, t) }), String(el.quantity || 1))
                if (q && !isNaN(Number(q))) {
                  fetch(`${API}/elements/${el.id}`, {
                    method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ quantity: Number(q), version: getVersion(el.id) }),
                  }).then(() => qc.invalidateQueries({ queryKey: ['elements', studyId] }))
                }
              }}
              title={t('Click to change quantity')}>
                ×{el.quantity}
              </span>
            ) : (
              <button
                onClick={() => {
                  const q = prompt(t('Quantity for "{{name}}":', { name: displayElementName(el.name, t) }), '1')
                  if (q && Number(q) > 1) {
                    fetch(`${API}/elements/${el.id}`, {
                      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ quantity: Number(q), version: getVersion(el.id) }),
                    }).then(() => qc.invalidateQueries({ queryKey: ['elements', studyId] }))
                  }
                }}
                style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.55rem', color: 'var(--text-secondary)' }}
                title={t('Set quantity (for duplicates/constellation)')}
              >
                {t('qty')}
              </button>
            )}

            {/* Scope toggle */}
            <button
              onClick={() => toggleScope(el.id, el.in_scope !== false)}
              title={el.in_scope === false ? t('Mark in-scope') : t('Mark out-of-scope')}
              style={{
                background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.65rem',
                color: el.in_scope === false ? '#6b7280' : 'var(--success)',
              }}
            >
              {el.in_scope === false ? t('EXT') : t('IN')}
            </button>

            {/* Freeze toggle */}
            <button
              onClick={() => toggleFreeze(el.id, !!el.frozen)}
              title={el.frozen ? t('Unfreeze') : t('Freeze')}
              style={{
                background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.65rem',
                color: el.frozen ? 'var(--warning)' : 'var(--text-secondary)',
              }}
            >
              {el.frozen ? t('FROZEN') : t('freeze')}
            </button>

            {/* Delete */}
            {!el.frozen && (
              <button
                onClick={() => {
                  if (confirm(t('Delete "{{name}}" and all its children?', { name: displayElementName(el.name, t) }))) {
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
            placeholder={t('Element name')}
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
              {typeOptions.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
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
              {segmentOptions(t).map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
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
              {domainOptions(t).map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
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
            {t('Add')}
          </button>
          <button
            onClick={() => setShowAdd(false)}
            style={{
              padding: '0.3rem 0.6rem', fontSize: '0.72rem',
              borderRadius: '3px', background: 'var(--bg-secondary)', color: 'var(--text-secondary)',
              border: 'none', cursor: 'pointer',
            }}
          >
            {t('Cancel')}
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
          {t('+ Add Element')}
        </button>
      )}

      {/* Auto-populate subsystem tree from KB */}
      <PopulateButton studyId={studyId} focusElementId={focusElementId} currentLevel={currentLevel} childElements={children} />

      {/* Element properties editor (Tier C data capture for exports) */}
      <ElementProperties studyId={studyId} focusElementId={focusElementId} allElements={allElements} />

      {/* Parameters & equations (SCDF-160) for the focused element */}
      <ParameterSection studyId={studyId} elementId={focusElementId}
        elementName={focusName && displayElementName(focusName, t)} />

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
// Preset name/description are display-only (translated); children names are stored as element names (English).
const presetsByLevel = (t: TFunction): Record<number, Array<{ id: string; name: string; description: string; children: PresetChild[] }>> => ({
  0: [
    {
      id: 'cubesat-mission', name: t('CubeSat LEO Mission'),
      description: t('Space, Ground, Launch, and Operations segments for a CubeSat'),
      children: [
        { name: 'Space Segment', type: 'segment', segment: 'space' },
        { name: 'Ground Segment', type: 'segment', segment: 'ground' },
        { name: 'Launch Segment', type: 'segment', segment: 'launch' },
        { name: 'Operations', type: 'segment', segment: 'operations' },
      ],
    },
    {
      id: 'constellation-mission', name: t('CubeSat Constellation'),
      description: t('Space (multi-sat), Ground, Launch, User, and Operations segments'),
      children: [
        { name: 'Space Segment', type: 'segment', segment: 'space' },
        { name: 'Ground Segment', type: 'segment', segment: 'ground' },
        { name: 'Launch Segment', type: 'segment', segment: 'launch' },
        { name: 'User Segment', type: 'segment', segment: 'user' },
        { name: 'Operations', type: 'segment', segment: 'operations' },
      ],
    },
    {
      id: 'drone-mission', name: t('Drone / UAV Network'),
      description: t('Non-space alternative: drone fleet, ground control, operations'),
      children: [
        { name: 'Air Segment', type: 'segment', segment: 'space' },
        { name: 'Ground Control', type: 'segment', segment: 'ground' },
        { name: 'Communications', type: 'segment', segment: 'ground' },
        { name: 'Operations', type: 'segment', segment: 'operations' },
      ],
    },
    {
      id: 'balloon-mission', name: t('Stratospheric Balloon'),
      description: t('Non-space alternative: balloon platform with ground station'),
      children: [
        { name: 'Balloon Platform', type: 'segment', segment: 'space' },
        { name: 'Ground Station', type: 'segment', segment: 'ground' },
        { name: 'Launch & Recovery', type: 'segment', segment: 'launch' },
        { name: 'Operations', type: 'segment', segment: 'operations' },
      ],
    },
    {
      id: 'ground-sensor-network', name: t('Ground Sensor Network'),
      description: t('Non-space alternative: distributed ground sensors with data center'),
      children: [
        { name: 'Sensor Network', type: 'segment', segment: 'ground' },
        { name: 'Communications', type: 'segment', segment: 'ground' },
        { name: 'Data Centre', type: 'segment', segment: 'ground' },
        { name: 'Operations', type: 'segment', segment: 'operations' },
      ],
    },
    {
      id: 'hybrid-mission', name: t('Hybrid Space + Ground'),
      description: t('CubeSat with ground sensor network for gap-filling'),
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
      id: 'single-spacecraft', name: t('Single Spacecraft'),
      description: t('1 spacecraft for the space segment'),
      children: [
        { name: 'Spacecraft', type: 'system', domain: 'payload', quantity: 1 },
      ],
    },
    {
      id: 'constellation-4', name: t('Constellation (4 spacecraft)'),
      description: t('4 identical spacecraft in one orbital plane'),
      children: [
        { name: 'Spacecraft', type: 'system', domain: 'payload', quantity: 4, performance: { constellation: true, orbital_planes: 1, sats_per_plane: 4 } },
      ],
    },
    {
      id: 'constellation-12', name: t('Constellation (3×4 = 12 spacecraft)'),
      description: t('12 spacecraft across 3 orbital planes'),
      children: [
        { name: 'Spacecraft', type: 'system', domain: 'payload', quantity: 12, performance: { constellation: true, orbital_planes: 3, sats_per_plane: 4 } },
      ],
    },
    {
      id: 'ground-network-2', name: t('2 Ground Stations'),
      description: t('Primary + backup ground stations'),
      children: [
        { name: 'Primary GS', type: 'system', domain: 'ground', quantity: 1, performance: { latitude: 78.2, longitude: 15.4, location: 'Svalbard' } },
        { name: 'Backup GS', type: 'system', domain: 'ground', quantity: 1, performance: { latitude: 67.9, longitude: 20.2, location: 'Kiruna' } },
      ],
    },
    {
      id: 'ground-network-3', name: t('3 Ground Stations'),
      description: t('Arctic + mid-lat + equatorial coverage'),
      children: [
        { name: 'Arctic GS', type: 'system', domain: 'ground', quantity: 1, performance: { latitude: 78.2, longitude: 15.4, location: 'Svalbard' } },
        { name: 'Mid-Lat GS', type: 'system', domain: 'ground', quantity: 1, performance: { latitude: 47.9, longitude: 11.1, location: 'Weilheim' } },
        { name: 'Equatorial GS', type: 'system', domain: 'ground', quantity: 1, performance: { latitude: -2.2, longitude: -54.9, location: 'Kourou' } },
      ],
    },
    {
      id: 'ops-centre', name: t('Operations Centre'),
      description: t('Mission control + payload processing'),
      children: [
        { name: 'Mission Control Centre', type: 'system', domain: 'ground', quantity: 1 },
        { name: 'Payload Data Centre', type: 'system', domain: 'ground', quantity: 1 },
        { name: 'Flight Dynamics', type: 'system', domain: 'ground', quantity: 1 },
      ],
    },
  ],
  2: [
    {
      id: 'standard-spacecraft-bus', name: t('Standard Spacecraft Bus'),
      description: t('All subsystems for a spacecraft: Payload, EPS, AOCS, TTC, OBC, Thermal, Structure, Propulsion'),
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
      id: 'eps-subsystems', name: t('EPS Subsystems'),
      description: t('Solar Array, Battery, Power Distribution, Regulation'),
      children: [
        { name: 'Solar Array', type: 'subsystem', domain: 'power' },
        { name: 'Battery Pack', type: 'subsystem', domain: 'power' },
        { name: 'Power Distribution', type: 'subsystem', domain: 'power' },
        { name: 'Power Regulation', type: 'subsystem', domain: 'power' },
      ],
    },
    {
      id: 'aocs-subsystems', name: t('AOCS Subsystems'),
      description: t('Sensors, Actuators, ADCS Computer'),
      children: [
        { name: 'Attitude Sensors', type: 'subsystem', domain: 'aocs' },
        { name: 'Reaction Wheels', type: 'subsystem', domain: 'aocs' },
        { name: 'Magnetorquers', type: 'subsystem', domain: 'aocs' },
        { name: 'ADCS Computer', type: 'subsystem', domain: 'aocs' },
      ],
    },
    {
      id: 'ttc-subsystems', name: t('TTC Subsystems'),
      description: t('Transponder, Antenna, Diplexer'),
      children: [
        { name: 'Transponder', type: 'subsystem', domain: 'ttc' },
        { name: 'Antenna', type: 'subsystem', domain: 'ttc' },
        { name: 'Diplexer/Filter', type: 'subsystem', domain: 'ttc' },
      ],
    },
    {
      id: 'ground-station-subsystems', name: t('Ground Station Subsystems'),
      description: t('Antenna, RF chain, Modem, Network'),
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
})

// ─── Element Properties Editor (Tier C data capture) ───

// Labels are display-only; keys and option values are stored in element.performance.
const propertyFields = (t: TFunction): Record<string, Array<{ key: string; label: string; type: 'text' | 'number' | 'select'; options?: string[] }>> => ({
  payload: [
    { key: 'gsd_m', label: t('GSD (m)'), type: 'number' },
    { key: 'fov_deg', label: t('FOV (deg)'), type: 'number' },
    { key: 'spectral_bands', label: t('Spectral bands'), type: 'text' },
    { key: 'shutter_control', label: t('Shutter control'), type: 'select', options: ['yes', 'no', 'N/A'] },
    { key: 'data_format', label: t('Data format'), type: 'text' },
    { key: 'data_rate_mbps', label: t('Data rate (Mbps)'), type: 'number' },
    { key: 'data_volume_gb_per_day', label: t('Data vol (GB/day)'), type: 'number' },
    { key: 'duty_cycle', label: t('Duty cycle (0-1)'), type: 'number' },
  ],
  ttc: [
    { key: 'rf_band', label: t('RF band'), type: 'select', options: ['UHF', 'S-band', 'X-band', 'Ka-band', 'L-band'] },
    { key: 'tx_power_w', label: t('TX power (W)'), type: 'number' },
    { key: 'data_rate_kbps', label: t('Data rate (kbps)'), type: 'number' },
    { key: 'data_rate_mbps', label: t('Downlink rate (Mbps)'), type: 'number' },
    { key: 'encryption', label: t('Encryption'), type: 'select', options: ['none', 'AES-128', 'AES-256', 'custom'] },
    { key: 'modulation', label: t('Modulation'), type: 'text' },
    { key: 'duty_cycle', label: t('Duty cycle (0-1)'), type: 'number' },
  ],
  power: [
    { key: 'bus_voltage_v', label: t('Bus voltage (V)'), type: 'number' },
    { key: 'sa_type', label: t('Solar array type'), type: 'select', options: ['body-mounted', 'single-deploy', 'dual-deploy', 'tracking'] },
    { key: 'battery_chemistry', label: t('Battery chemistry'), type: 'select', options: ['Li-ion', 'LiPo', 'LiFePO4', 'NiMH'] },
    { key: 'duty_cycle', label: t('Duty cycle (0-1)'), type: 'number' },
  ],
  thermal: [
    { key: 'temp_min_c', label: t('Min temp (°C)'), type: 'number' },
    { key: 'temp_max_c', label: t('Max temp (°C)'), type: 'number' },
    { key: 'coating', label: t('Surface coating'), type: 'select', options: ['white paint', 'black anodize', 'gold', 'MLI', 'OSR'] },
    { key: 'duty_cycle', label: t('Duty cycle (0-1)'), type: 'number' },
  ],
  aocs: [
    { key: 'pointing_accuracy_deg', label: t('Pointing accuracy (deg)'), type: 'number' },
    { key: 'pointing_knowledge_deg', label: t('Pointing knowledge (deg)'), type: 'number' },
    { key: 'slew_rate_deg_s', label: t('Slew rate (deg/s)'), type: 'number' },
    { key: 'duty_cycle', label: t('Duty cycle (0-1)'), type: 'number' },
  ],
  propulsion: [
    { key: 'isp_s', label: t('Isp (s)'), type: 'number' },
    { key: 'thrust_n', label: t('Thrust (N)'), type: 'number' },
    { key: 'propellant_type', label: t('Propellant'), type: 'select', options: ['cold gas (N2)', 'cold gas (R236fa)', 'green monoprop', 'hydrazine', 'electric (Xe)', 'none'] },
    { key: 'total_impulse_ns', label: t('Total impulse (Ns)'), type: 'number' },
    { key: 'duty_cycle', label: t('Duty cycle (0-1)'), type: 'number' },
  ],
  structure: [
    { key: 'form_factor', label: t('Form factor'), type: 'select', options: ['1U', '1.5U', '2U', '3U', '6U', '12U', '16U', '27U', 'custom'] },
    { key: 'material', label: t('Primary material'), type: 'select', options: ['Al 6061-T6', 'Al 7075', 'CFRP', 'Ti-6Al-4V'] },
    { key: 'deployables', label: t('Deployables'), type: 'text' },
    { key: 'duty_cycle', label: t('Duty cycle (0-1)'), type: 'number' },
  ],
  ground: [
    { key: 'latitude', label: t('Latitude (deg)'), type: 'number' },
    { key: 'longitude', label: t('Longitude (deg)'), type: 'number' },
    { key: 'antenna_diameter_m', label: t('Antenna diameter (m)'), type: 'number' },
    { key: 'min_elevation_deg', label: t('Min elevation (deg)'), type: 'number' },
    { key: 'bands', label: t('Bands'), type: 'text' },
  ],
})

/** Option values that are words (not part numbers, standards or materials): shown translated. */
// English text is the i18n key
const OPTION_WORDS = [
  'yes', 'no', 'none', 'custom', 'body-mounted', 'single-deploy', 'dual-deploy', 'tracking',
  'white paint', 'black anodize', 'gold', 'cold gas (N2)', 'cold gas (R236fa)', 'green monoprop',
  'hydrazine', 'electric (Xe)',
]

function ElementProperties({ studyId, focusElementId, allElements }: { studyId: string | null; focusElementId: string | null; allElements: any[] }) {
  const { t } = useTranslation()
  const [expanded, setExpanded] = useState(false)
  const qc = useQueryClient()

  const focusElement = allElements.find((e: any) => e.id === focusElementId)
  if (!focusElement) return null

  const domain = focusElement.subsystem_domain || focusElement.element_type
  const fields = propertyFields(t)[domain]
  if (!fields || fields.length === 0) return null

  const perf = focusElement.performance || {}

  const updateProp = async (key: string, value: any) => {
    const newPerf = { ...perf, [key]: value }
    await fetch(`${API}/elements/${focusElement.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ performance: newPerf, version: focusElement.version }),
    })
    qc.invalidateQueries({ queryKey: ['elements', studyId] })
  }

  return (
    <div style={{ marginTop: '0.5rem', borderTop: '1px solid var(--border)', paddingTop: '0.4rem' }}>
      <button onClick={() => setExpanded(!expanded)} style={{
        background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.68rem',
        color: '#06b6d4', fontWeight: 600, padding: 0,
      }}>
        {expanded ? '▾' : '▸'} {t('Properties: {{name}}', { name: displayElementName(focusElement.name, t) })}
      </button>
      {expanded && (
        <div style={{ marginTop: '0.3rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.25rem' }}>
          {fields.map(f => (
            <div key={f.key} style={{ fontSize: '0.63rem' }}>
              <label style={{ color: 'var(--text-secondary)', display: 'block', marginBottom: '0.1rem' }}>{t('{{label}}:', { label: f.label })}</label>
              {f.type === 'select' ? (
                <select value={perf[f.key] || ''} onChange={e => updateProp(f.key, e.target.value)}
                  style={{ width: '100%', padding: '0.15rem 0.3rem', fontSize: '0.63rem', borderRadius: '3px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
                  <option value="">—</option>
                  {f.options?.map(o => <option key={o} value={o}>{OPTION_WORDS.includes(o) ? t(o) : o}</option>)}
                </select>
              ) : (
                <input type={f.type} value={perf[f.key] ?? ''} onChange={e => updateProp(f.key, f.type === 'number' ? parseFloat(e.target.value) || null : e.target.value)}
                  placeholder={f.label}
                  style={{ width: '100%', padding: '0.15rem 0.3rem', fontSize: '0.63rem', borderRadius: '3px', background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)' }} />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Suggested requirements moved to RequirementsPanel (suggestedReqs.ts)

function DesignAssist({ studyId, focusElementId, currentLevel }: { studyId: string | null; focusElementId: string | null; currentLevel: Level }) {
  const { t } = useTranslation()
  const [expanded, setExpanded] = useState(false)
  const [applying, setApplying] = useState(false)
  const qc = useQueryClient()

  const presets = presetsByLevel(t)[currentLevel] || []

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
        {expanded ? '▾' : '▸'} {t('Architecture Presets')}
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
                {t('({{count}} blocks)', { count: p.children.length })}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}


// ─── Populate Button: auto-create subsystems + equipment from KB ───

function PopulateButton({ studyId, focusElementId, currentLevel, childElements }: {
  studyId: string | null; focusElementId: string | null; currentLevel: number; childElements: any[]
}) {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const qc = useQueryClient()

  // Show at Level 1 (segment focused) when no system children exist yet
  const focusEl = (qc.getQueryData(['elements', studyId]) as any[] || [])
    .find((e: any) => e.id === focusElementId)
  const isSegment = focusEl?.element_type === 'segment'
  const hasSystem = childElements.some((c: any) => c.element_type === 'system')

  if (currentLevel !== 1 || !isSegment || hasSystem) return null

  const populate = async () => {
    if (!studyId || !focusElementId) return
    setLoading(true)
    setResult(null)
    try {
      const res = await fetch(
        `${API}/studies/${studyId}/populate-subsystems?parent_element_id=${focusElementId}`,
        { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }
      )
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setResult(data.message)
      qc.invalidateQueries({ queryKey: ['elements', studyId] })
    } catch (e) {
      setResult(t('Error: {{msg}}', { msg: String(e) }))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      marginTop: '0.5rem', padding: '0.5rem', borderRadius: '6px',
      background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)',
    }}>
      <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--accent)', marginBottom: '0.3rem' }}>
        {t('Quick Start')}
      </div>
      <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
        {t('Auto-create standard subsystems (EPS, AOCS, Comms, OBC, Thermal, Structure, Propulsion) with recommended CubeSat equipment from the component catalogue.')}
      </div>
      <button
        onClick={populate}
        disabled={loading}
        style={{
          padding: '0.3rem 0.8rem', fontSize: '0.72rem', fontWeight: 600,
          borderRadius: '4px', background: loading ? 'var(--border)' : 'var(--accent)',
          color: 'white', border: 'none', cursor: loading ? 'wait' : 'pointer',
        }}
      >
        {loading ? t('Populating...') : t('Populate Subsystems + Equipment')}
      </button>
      {result && (
        <div style={{ marginTop: '0.3rem', fontSize: '0.65rem', color: result.startsWith('Error') ? 'var(--danger)' : 'var(--success)' }}>
          {result.startsWith('Error: ') ? t('Error: {{message}}', { message: result.slice('Error: '.length) }) : result}
        </div>
      )}
    </div>
  )
}
