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
import { subsystemStyle } from '../theme/tokens'
import { askText } from '../components/ui/Dialog'
import { ArmButton, Button, Disclosure, Field, Input, Panel, Select, StatusBadge } from '../components/ui'

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

function InlineEdit({ value, onCommit, className, inputClassName, label }: {
  value: string; onCommit: (newValue: string) => void; className?: string; inputClassName?: string; label: string
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
      <button
        type="button"
        onClick={() => { setDraft(value); setEditing(true) }}
        className={`c2o-inline-edit ${className ?? ''}`}
        aria-label={t('{{label}}: {{value}}. Click to edit', { label, value })}
        title={t('Click to edit')}
      >
        {value}
      </button>
    )
  }

  return (
    <input
      ref={inputRef}
      aria-label={label}
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
      className={`c2o-input c2o-input--sm ${inputClassName ?? ''}`}
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
        element_type: newType || (({ 0: 'segment', 1: 'system', 2: 'subsystem', 3: 'component' } as Record<number, string>)[currentLevel] || 'system'),
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

  const setQuantity = async (el: any) => {
    const q = await askText(t('Quantity for "{{name}}":', { name: displayElementName(el.name, t) }), String(el.quantity || 1))
    if (q && !isNaN(Number(q)) && Number(q) >= 1) {
      fetch(`${API}/elements/${el.id}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quantity: Number(q), version: getVersion(el.id) }),
      }).then(() => qc.invalidateQueries({ queryKey: ['elements', studyId] }))
    }
  }

  return (
    <div className="c2o-pane">
      {/* Element list */}
      <div className="c2o-blocks" role="list" aria-label={t('Elements at this level')}>
        {children.length === 0 && !showAdd && (
          <p className="c2o-blocks__empty">{t('No elements at this level. Click "Add Element" to start.')}</p>
        )}
        {children.map((el: any) => {
          const ss = el.subsystem_domain ? subsystemStyle(el.subsystem_domain) : null
          const name = displayElementName(el.name, t)
          const locked = isLockedByOther(el.id)
          const outOfScope = el.in_scope === false
          return (
            <div key={el.id} role="listitem" className={outOfScope ? 'c2o-blocks__row is-external' : 'c2o-blocks__row'}>
              <span className="c2o-blocks__kind">
                <span className="c2o-ss-badge" aria-hidden="true" style={{ background: ss ? ss.color : 'transparent' }}>{ss?.badge ?? ''}</span>
                <span className="ellipsis">{el.subsystem_domain || el.element_type}</span>
              </span>
              <span className="c2o-blocks__name">
                {locked ? (
                  <>
                    <span className="w-500 c-2">{name}</span>
                    <StatusBadge status="caution">{t('Locked by {{name}}', { name: lockHolder(el.id) })}</StatusBadge>
                  </>
                ) : (
                  <InlineEdit value={name} label={t('Name')} className="w-500"
                    onCommit={(v) => { requestLock(el.id); patchElement(el.id, { name: v }); releaseLock(el.id) }} />
                )}
              </span>
              <span className="c2o-blocks__val">
                {el.mass_kg != null ? (
                  <><InlineEdit value={el.mass_kg.toFixed(1)} label={t('Mass (kg)')} className="mono c2o-blocks__num" inputClassName="c2o-input--num c2o-blocks__numinput"
                    onCommit={(v) => { const n = parseFloat(v); if (!isNaN(n)) patchElement(el.id, { mass_kg: n }) }} /><span className="c2o-blocks__unit">kg</span></>
                ) : <span className="c2o-nodata">{t('no mass')}</span>}
              </span>
              <span className="c2o-blocks__val">
                {el.power_avg_w != null ? (
                  <><InlineEdit value={el.power_avg_w.toFixed(1)} label={t('Average power (W)')} className="mono c2o-blocks__num" inputClassName="c2o-input--num c2o-blocks__numinput"
                    onCommit={(v) => { const n = parseFloat(v); if (!isNaN(n)) patchElement(el.id, { power_avg_w: n }) }} /><span className="c2o-blocks__unit">W</span></>
                ) : <span className="c2o-nodata">{t('no power')}</span>}
              </span>
              <span className="c2o-blocks__ctl">
                <Button size="sm" variant="quiet" onClick={() => setQuantity(el)}
                  title={t('Set quantity (for duplicates/constellation)')} aria-label={t('Quantity: {{n}}', { n: el.quantity || 1 })}>
                  <span className="mono">×{el.quantity || 1}</span>
                </Button>
                <label className="c2o-check t-12" title={outOfScope ? t('Mark in-scope') : t('Mark out-of-scope')}>
                  <input type="checkbox" checked={!outOfScope} onChange={() => toggleScope(el.id, !outOfScope)} />
                  {t('In scope')}
                </label>
                <label className="c2o-check t-12" title={el.frozen ? t('Unfreeze') : t('Freeze')}>
                  <input type="checkbox" checked={!!el.frozen} onChange={() => toggleFreeze(el.id, !!el.frozen)} />
                  {t('Frozen')}
                </label>
                <ArmButton variant="icon" label="×" armedLabel={t('Delete with children')}
                  aria-label={t('Delete "{{name}}"', { name })}
                  disabledReason={el.frozen ? t('Unfreeze the element before deleting it') : undefined}
                  onConfirm={() => deleteMutation.mutate(el.id)} />
              </span>
            </div>
          )
        })}
      </div>

      {/* Add element form */}
      {showAdd ? (
        <form className="c2o-blocks__add" aria-label={t('Add element')}
          onSubmit={e => { e.preventDefault(); if (newName) addMutation.mutate() }}>
          <Field label={t('Element name')}>
            <Input value={newName} onChange={e => setNewName(e.target.value)} autoFocus dense />
          </Field>
          {typeOptions.length > 0 && (
            <Field label={t('Type')}>
              <Select value={newType} onChange={e => setNewType(e.target.value)} dense>
                {typeOptions.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </Select>
            </Field>
          )}
          {currentLevel === 0 && (
            <Field label={t('Segment')}>
              <Select value={newSegment} onChange={e => setNewSegment(e.target.value)} dense>
                {segmentOptions(t).map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
              </Select>
            </Field>
          )}
          {currentLevel >= 1 && (
            <Field label={t('Subsystem domain')}>
              <Select value={newDomain} onChange={e => setNewDomain(e.target.value)} dense>
                {domainOptions(t).map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
              </Select>
            </Field>
          )}
          <span className="row gap-2">
            <Button type="submit" variant="primary" size="sm" busy={addMutation.isPending}
              disabledReason={!newName ? t('Enter a name first') : undefined}>{t('Add')}</Button>
            <Button size="sm" onClick={() => setShowAdd(false)}>{t('Cancel')}</Button>
          </span>
        </form>
      ) : (
        <Button variant="primary" size="sm" className="mt-2"
          onClick={() => { setNewType(typeOptions[0]?.value || 'segment'); setShowAdd(true) }}>
          {t('+ Add Element')}
        </Button>
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
        <div className="mt-2 bt pt-2">
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
    <Disclosure ruled open={expanded} onToggle={setExpanded}
      summary={t('Properties: {{name}}', { name: displayElementName(focusElement.name, t) })}>
      <div className="c2o-form-grid">
        {fields.map(f => (
          <Field key={f.key} label={f.label}>
            {f.type === 'select' ? (
              <Select dense value={perf[f.key] || ''} onChange={e => updateProp(f.key, e.target.value)}>
                <option value="">{t('not set')}</option>
                {f.options?.map(o => <option key={o} value={o}>{OPTION_WORDS.includes(o) ? t(o) : o}</option>)}
              </Select>
            ) : (
              <Input dense numeric={f.type === 'number'} type={f.type} value={perf[f.key] ?? ''}
                onChange={e => updateProp(f.key, f.type === 'number' ? parseFloat(e.target.value) || null : e.target.value)} />
            )}
          </Field>
        ))}
      </div>
    </Disclosure>
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
    <Disclosure ruled open={expanded} onToggle={setExpanded} summary={t('Architecture Presets')}
      meta={t('{{count}} presets', { count: presets.length, defaultValue_one: '{{count}} preset' })}>
      <ul className="c2o-preset-list list-reset">
        {presets.map(p => (
          <li key={p.id}>
            <button type="button" className="c2o-example-card" onClick={() => applyPreset(p)} disabled={applying} aria-busy={applying || undefined}>
              <span className="row gap-2 jc-sb">
                <span className="w-600 t-13">{p.name}</span>
                <span className="t-12 c-3">{t('({{count}} blocks)', { count: p.children.length })}</span>
              </span>
              <span className="c2o-example-card__desc">{p.description}</span>
            </button>
          </li>
        ))}
      </ul>
    </Disclosure>
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
      // Send the study's spacecraft class so the rules pick the right bus (audit §4.2: '{}' always meant nano).
      let spacecraftClass: string | undefined
      try {
        const st = await fetch(`${API}/studies/${studyId}`).then(r => (r.ok ? r.json() : null))
        spacecraftClass = st?.requirements?.spacecraft_class ?? st?.spacecraft_class ?? undefined
      } catch { /* keep the server default */ }
      const res = await fetch(
        `${API}/studies/${studyId}/populate-subsystems?parent_element_id=${focusElementId}`,
        { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(spacecraftClass ? { spacecraft_class: spacecraftClass } : {}) }
      )
      qc.invalidateQueries({ queryKey: ['interfaces', studyId] })
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
    <Panel boxed className="mt-3" title={t('Quick Start')}>
      <p className="t-13 c-2 m-0 mb-2 measure">
        {t('Auto-create standard subsystems (EPS, AOCS, Comms, OBC, Thermal, Structure, Propulsion) with recommended CubeSat equipment from the component catalogue.')}
      </p>
      <Button variant="primary" size="sm" onClick={populate} busy={loading} active={loading}>
        {loading ? t('Populating...') : t('Populate Subsystems + Equipment')}
      </Button>
      {result && (
        <div className="mt-2">
          {result.startsWith('Error')
            ? <StatusBadge status="alarm">{t('Error: {{message}}', { message: result.slice('Error: '.length) })}</StatusBadge>
            : <StatusBadge status="ok">{result}</StatusBadge>}
        </div>
      )}
    </Panel>
  )
}
