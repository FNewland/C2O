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
import { ArmButton, Button, Disclosure, Field, Input, Panel, Select, StatusBadge, Tag } from '../components/ui'

import { canAddSpacecraft, placement, segmentOf, showQuickStart, structuralLevel } from './blockLevels'

const API = '/api'

// Option values are stored enums; only the labels are translated (display time).
// One type per level: the next level of the ECSS product tree (blockLevels.ts). Under a
// space segment a system is a spacecraft; under a ground segment a station or centre.
const elementTypesByLevel = (t: TFunction, segment?: string | null): Record<Level, Array<{ value: string; label: string }>> => ({
  0: [
    { value: 'segment', label: t('Segment') },
  ],
  1: [
    { value: 'system', label: segment === 'space' ? t('Spacecraft (system)')
      : segment === 'ground' ? t('Ground station / facility (system)') : t('System / element') },
  ],
  // Under a ground station or facility the parts are equipment (RF chain, computers), not subsystems.
  2: segment && segment !== 'space'
    ? [{ value: 'component', label: t('Component') }, { value: 'subsystem', label: t('Subsystem') }]
    : [{ value: 'subsystem', label: t('Subsystem') }],
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
  'Spacecraft', 'DSN Ground Station', 'Ground Segment (DSN)', 'Communications', 'On-Board Computer', 'Primary GS', 'Backup GS', 'Arctic GS', 'Mid-Lat GS', 'Equatorial GS',
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
  const place = placement(allElements, focusElementId)
  const blockLevel = structuralLevel(place.childType)
  const focusEl = allElements.find((e: any) => e.id === focusElementId)

  // Add element form state
  const [showAdd, setShowAdd] = useState(false)
  const [newName, setNewName] = useState('')
  const [newType, setNewType] = useState('')
  const [newSegment, setNewSegment] = useState('space')
  const [newDomain, setNewDomain] = useState('')

  const addMutation = useMutation({
    mutationFn: async () => {
      // Type and parent follow the element in focus, not the breadcrumb depth (blockLevels.ts)
      const body: any = {
        name: newName,
        element_type: newType || place.childType || 'component',
        parent_id: place.parentId || undefined,
        segment: newSegment,
      }
      // Inside a segment, children belong to that segment
      if (focusEl?.segment && place.childType !== 'segment') body.segment = focusEl.segment
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

  const focusSegment = segmentOf(allElements, focusElementId)
  const typeOptions = elementTypesByLevel(t, focusSegment)[blockLevel] || []
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
          {blockLevel === 0 && (
            <Field label={t('Segment')}>
              <Select value={newSegment} onChange={e => setNewSegment(e.target.value)} dense>
                {segmentOptions(t).map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
              </Select>
            </Field>
          )}
          {blockLevel >= 1 && (
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
        <span className="row gap-2 wrap mt-2">
          {canAddSpacecraft(allElements, focusElementId) && (
            <AddSpacecraftButton studyId={studyId} segmentId={focusElementId!}
              count={children.filter((c: any) => c.element_type === 'system' && !c.deleted_at).length} />
          )}
          <Button variant={canAddSpacecraft(allElements, focusElementId) ? 'default' : 'primary'} size="sm"
            onClick={() => { setNewType(typeOptions[0]?.value || 'segment'); setShowAdd(true) }}>
            {t('+ Add Element')}
          </Button>
        </span>
      )}

      {/* Auto-populate subsystem tree from KB */}
      <PopulateButton studyId={studyId} focusElementId={focusElementId} show={showQuickStart(allElements, focusElementId)} />

      {/* Element properties editor (Tier C data capture for exports) */}
      <ElementProperties studyId={studyId} focusElementId={focusElementId} allElements={allElements} />

      {/* Parameters & equations (SCDF-160) for the focused element */}
      <div data-where="params">
        <ParameterSection studyId={studyId} elementId={focusElementId}
          elementName={focusName && displayElementName(focusName, t)} />
      </div>

      {/* Design Tools (constellation orbit, ground station config) */}
      <DesignTools />

      {/* Equipment Browser at Level 3 */}
      {blockLevel === 3 && (
        <div className="mt-2 bt pt-2" data-where="equipment-catalog">
          <EquipmentBrowser />
        </div>
      )}

      {/* Design Assist */}
      <DesignAssist studyId={studyId} parentId={place.parentId} blockLevel={blockLevel} segment={focusSegment} />
    </div>
  )
}

// ─── Design Assist: presets + suggested requirements ───

interface PresetChild { name: string; type: string; domain?: string; segment?: string; quantity?: number; performance?: Record<string, any> }
/** Level-1 presets name the segment kind they fill (spacecraft under a space segment, stations
 *  under a ground segment): the right child types at each level (blockLevels.ts). */
interface Preset { id: string; name: string; description: string; children: PresetChild[]; segments?: string[] }
// Preset name/description are display-only (translated); children names are stored as element names (English).
const presetsByLevel = (t: TFunction): Record<number, Preset[]> => ({
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
      id: 'single-spacecraft', name: t('Single Spacecraft'), segments: ['space'],
      description: t('1 spacecraft for the space segment'),
      children: [
        { name: 'Spacecraft', type: 'system', quantity: 1 },
      ],
    },
    {
      id: 'constellation-4', name: t('Constellation (4 spacecraft)'), segments: ['space'],
      description: t('4 identical spacecraft in one orbital plane'),
      children: [
        { name: 'Spacecraft', type: 'system', quantity: 4, performance: { constellation: true, orbital_planes: 1, sats_per_plane: 4 } },
      ],
    },
    {
      id: 'constellation-12', name: t('Constellation (3×4 = 12 spacecraft)'), segments: ['space'],
      description: t('12 spacecraft across 3 orbital planes'),
      children: [
        { name: 'Spacecraft', type: 'system', quantity: 12, performance: { constellation: true, orbital_planes: 3, sats_per_plane: 4 } },
      ],
    },
    {
      id: 'ground-network-2', name: t('2 Ground Stations'), segments: ['ground', 'operations', 'user'],
      description: t('Primary + backup ground stations'),
      children: [
        { name: 'Primary GS', type: 'system', domain: 'ground', quantity: 1, performance: { latitude: 78.2, longitude: 15.4, location: 'Svalbard' } },
        { name: 'Backup GS', type: 'system', domain: 'ground', quantity: 1, performance: { latitude: 67.9, longitude: 20.2, location: 'Kiruna' } },
      ],
    },
    {
      id: 'ground-network-3', name: t('3 Ground Stations'), segments: ['ground', 'operations', 'user'],
      description: t('Arctic + mid-lat + equatorial coverage'),
      children: [
        { name: 'Arctic GS', type: 'system', domain: 'ground', quantity: 1, performance: { latitude: 78.2, longitude: 15.4, location: 'Svalbard' } },
        { name: 'Mid-Lat GS', type: 'system', domain: 'ground', quantity: 1, performance: { latitude: 47.9, longitude: 11.1, location: 'Weilheim' } },
        { name: 'Equatorial GS', type: 'system', domain: 'ground', quantity: 1, performance: { latitude: -2.2, longitude: -54.9, location: 'Kourou' } },
      ],
    },
    {
      id: 'ops-centre', name: t('Operations Centre'), segments: ['ground', 'operations', 'user'],
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
      id: 'standard-spacecraft-bus', name: t('Standard Spacecraft Bus'), segments: ['space'],
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
      id: 'eps-subsystems', name: t('EPS Subsystems'), segments: ['space'],
      description: t('Solar Array, Battery, Power Distribution, Regulation'),
      children: [
        { name: 'Solar Array', type: 'subsystem', domain: 'power' },
        { name: 'Battery Pack', type: 'subsystem', domain: 'power' },
        { name: 'Power Distribution', type: 'subsystem', domain: 'power' },
        { name: 'Power Regulation', type: 'subsystem', domain: 'power' },
      ],
    },
    {
      id: 'aocs-subsystems', name: t('AOCS Subsystems'), segments: ['space'],
      description: t('Sensors, Actuators, ADCS Computer'),
      children: [
        { name: 'Attitude Sensors', type: 'subsystem', domain: 'aocs' },
        { name: 'Reaction Wheels', type: 'subsystem', domain: 'aocs' },
        { name: 'Magnetorquers', type: 'subsystem', domain: 'aocs' },
        { name: 'ADCS Computer', type: 'subsystem', domain: 'aocs' },
      ],
    },
    {
      id: 'ttc-subsystems', name: t('TTC Subsystems'), segments: ['space'],
      description: t('Transponder, Antenna, Diplexer'),
      children: [
        { name: 'Transponder', type: 'subsystem', domain: 'ttc' },
        { name: 'Antenna', type: 'subsystem', domain: 'ttc' },
        { name: 'Diplexer/Filter', type: 'subsystem', domain: 'ttc' },
      ],
    },
    {
      id: 'ground-station-subsystems', name: t('Ground Station Subsystems'), segments: ['ground', 'operations', 'user'],
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
    { key: 'swath_km', label: t('Swath (km)'), type: 'number' },
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

/** Debounce of Properties edits (W1.07): one PATCH per pause in typing, never two in flight. */
export const PROPERTY_SAVE_DELAY_MS = 500

function ElementProperties({ studyId, focusElementId, allElements }: { studyId: string | null; focusElementId: string | null; allElements: any[] }) {
  const { t } = useTranslation()
  const [expanded, setExpanded] = useState(false)
  const qc = useQueryClient()

  const focusElement = allElements.find((e: any) => e.id === focusElementId)
  // Local draft of the edited fields: typing updates it at once; the server sees one debounced
  // PATCH with the latest version (W1.07: no 409 while typing, the final value is stored).
  const [draft, setDraft] = useState<Record<string, any>>({})
  const [shown, setShown] = useState<Record<string, string>>({})   // raw text of number fields while typing
  const [trlDraft, setTrlDraft] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const versionRef = useRef<number>(focusElement?.version || 1)
  const pendingRef = useRef<{ perf: Record<string, any>; trl?: number | null } | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const chainRef = useRef<Promise<void>>(Promise.resolve())
  const elIdRef = useRef<string | null>(null)

  useEffect(() => {
    // another element in focus: flush nothing, start a fresh draft
    if (elIdRef.current !== (focusElement?.id ?? null)) {
      elIdRef.current = focusElement?.id ?? null
      setDraft({}); setShown({}); setTrlDraft(null); setSaveError(null)
      versionRef.current = focusElement?.version || 1
    } else if ((focusElement?.version || 0) > versionRef.current) {
      versionRef.current = focusElement.version
    }
  }, [focusElement?.id, focusElement?.version])

  useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current) }, [])

  const send = useCallback((elementId: string) => {
    chainRef.current = chainRef.current.then(async () => {
      const body = pendingRef.current
      pendingRef.current = null
      if (!body) return
      const payload: Record<string, any> = { performance: body.perf }
      if (body.trl !== undefined) payload.trl = body.trl
      for (let attempt = 0; attempt < 2; attempt++) {
        const res = await fetch(`${API}/elements/${elementId}`, {
          method: 'PATCH', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...payload, version: versionRef.current }),
        })
        if (res.ok) {
          const el = await res.json().catch(() => null)
          if (el?.version) versionRef.current = el.version
          setSaveError(null)
          break
        }
        if (res.status === 409 && attempt === 0) {
          // someone else saved in between: take the server version, keep our edit on top
          const cur = await fetch(`${API}/elements/${elementId}`).then(r => r.ok ? r.json() : null).catch(() => null)
          if (cur?.version) versionRef.current = cur.version
          if (cur?.performance) payload.performance = { ...cur.performance, ...body.perf }
          continue
        }
        setSaveError(t('Not saved ({{status}})', { status: res.status }))
        break
      }
      qc.invalidateQueries({ queryKey: ['elements', studyId] })
    })
  }, [qc, studyId, t])

  if (!focusElement) return null
  return <ElementPropertiesBody {...{ studyId, focusElement, expanded, setExpanded, draft, setDraft, shown, setShown,
    trlDraft, setTrlDraft, saveError, pendingRef, timerRef, send }} />
}

/** 3.L5: Properties the optics propose for a payload camera (GSD, FOV, swath, CSI-2 rate). */
const PROPOSED_KEYS = ['gsd_m', 'fov_deg', 'swath_km', 'data_rate_mbps']

function ProposedChip({ value, proposed }: { value: unknown; proposed: unknown }) {
  const { t } = useTranslation()
  // shown only once the student has typed a value: the hand calculation comes first (A5)
  if (proposed === null || proposed === undefined || value === null || value === undefined || value === '') return null
  const v = Number(value), p = Number(proposed)
  const agrees = Number.isFinite(v) && Math.abs(v - p) <= Math.max(0.02 * Math.abs(p), 0.05)
  return (
    <Tag accent={!agrees} title={agrees ? t('Your value agrees with the optics') : t('The optics give {{p}}: check your calculation', { p })}>
      {agrees ? t('✓ proposed {{p}}', { p }) : t('proposed {{p}}', { p })}
    </Tag>
  )
}

function ElementPropertiesBody({ studyId, focusElement, expanded, setExpanded, draft, setDraft, shown, setShown,
  trlDraft, setTrlDraft, saveError, pendingRef, timerRef, send }: any) {
  const { t } = useTranslation()
  const domain = focusElement.subsystem_domain || focusElement.element_type
  const isCamera = domain === 'payload' && focusElement.element_type === 'component'
  const { data: geometry } = useQuery({
    queryKey: ['payload-geometry', studyId],
    queryFn: async () => {
      const r = await fetch(`${API}/lifecycle/payload-geometry/${studyId}`)
      return r.ok ? r.json() : null
    },
    enabled: !!studyId && isCamera,
    staleTime: 10_000,
  })
  const proposal: Record<string, number> | undefined = geometry?.proposals?.[focusElement.id]
  const fields = propertyFields(t)[domain] || []
  const isCustom = !focusElement.kb_component_id
  const showTrl = focusElement.element_type === 'component' || isCustom
  if (fields.length === 0 && !showTrl) return null

  const perf = { ...(focusElement.performance || {}), ...draft }

  const schedule = (nextDraft: Record<string, any>, trl?: number | null) => {
    pendingRef.current = {
      perf: { ...(focusElement.performance || {}), ...nextDraft },
      trl: trl !== undefined ? trl : pendingRef.current?.trl,
    }
    if (timerRef.current) clearTimeout(timerRef.current)
    const id = focusElement.id
    timerRef.current = setTimeout(() => send(id), PROPERTY_SAVE_DELAY_MS)
  }

  const updateProp = (key: string, value: any, raw?: string) => {
    if (raw !== undefined) setShown((prev: Record<string, string>) => ({ ...prev, [key]: raw }))
    const next = { ...draft, [key]: value }
    setDraft(next)
    schedule(next)
  }

  const updateTrl = (raw: string) => {
    setTrlDraft(raw)
    const n = parseInt(raw, 10)
    if (raw === '' || (n >= 1 && n <= 9)) schedule(draft, raw === '' ? null : n)
  }

  return (
    <Disclosure ruled open={expanded} onToggle={setExpanded}
      summary={t('Properties: {{name}}', { name: displayElementName(focusElement.name, t) })}>
      <div className="c2o-form-grid">
        {showTrl && (
          <Field label={t('TRL (1-9)')} help={isCustom ? undefined : t('From the knowledge base')}
            disabledReason={isCustom ? undefined : t('TRL of a catalogue part comes from the knowledge base')}>
            <Input dense numeric type="number" min={1} max={9} aria-label={t('TRL (1-9)')}
              value={trlDraft ?? (focusElement.trl ?? '')} onChange={e => updateTrl(e.target.value)} />
          </Field>
        )}
        {showTrl && (<>
          <Field label={t('TRL target at PDR')}>
            <Input dense numeric type="number" min={1} max={9} aria-label={t('TRL target at PDR')}
              value={shown.trl_target_pdr ?? perf.trl_target_pdr ?? ''}
              onChange={e => updateProp('trl_target_pdr', e.target.value === '' ? null : parseInt(e.target.value, 10), e.target.value)} />
          </Field>
          <Field label={t('TRL target at CDR')}>
            <Input dense numeric type="number" min={1} max={9} aria-label={t('TRL target at CDR')}
              value={shown.trl_target_cdr ?? perf.trl_target_cdr ?? ''}
              onChange={e => updateProp('trl_target_cdr', e.target.value === '' ? null : parseInt(e.target.value, 10), e.target.value)} />
          </Field>
          <Field label={t('Maturation plan')} help={perf.readiness_item ? t('Readiness plan row: {{item}}', { item: perf.readiness_item }) : undefined}>
            <Input dense value={perf.trl_maturation ?? ''} onChange={e => updateProp('trl_maturation', e.target.value)} />
          </Field>
        </>)}
        {fields.map(f => (
          <Field key={f.key} label={<>{f.label} {isCamera && PROPOSED_KEYS.includes(f.key) && <ProposedChip value={perf[f.key]} proposed={proposal?.[f.key]} />}</>}>
            {f.type === 'select' ? (
              <Select dense value={perf[f.key] || ''} onChange={e => updateProp(f.key, e.target.value)}>
                <option value="">{t('not set')}</option>
                {f.options?.map(o => <option key={o} value={o}>{OPTION_WORDS.includes(o) ? t(o) : o}</option>)}
              </Select>
            ) : (
              <Input dense numeric={f.type === 'number'} type={f.type} value={shown[f.key] ?? perf[f.key] ?? ''}
                onChange={e => f.type === 'number'
                  ? updateProp(f.key, e.target.value === '' || isNaN(parseFloat(e.target.value)) ? null : parseFloat(e.target.value), e.target.value)
                  : updateProp(f.key, e.target.value)} />
            )}
          </Field>
        ))}
      </div>
      {saveError && <p role="alert" className="t-12 c-alarm m-0">{saveError}</p>}
    </Disclosure>
  )
}

// Suggested requirements moved to RequirementsPanel (suggestedReqs.ts)

function DesignAssist({ studyId, parentId: placeParent, blockLevel, segment }: {
  studyId: string | null; parentId: string | null; blockLevel: Level; segment?: string | null
}) {
  const { t } = useTranslation()
  const [expanded, setExpanded] = useState(false)
  const [applying, setApplying] = useState(false)
  const qc = useQueryClient()

  const presets = (presetsByLevel(t)[blockLevel] || []).filter(p => !p.segments || !segment || p.segments.includes(segment))

  if (presets.length === 0) return null

  const applyPreset = async (preset: typeof presets[0]) => {
    if (!studyId) return
    setApplying(true)
    try {
      // Parent: the element in focus, or the study's mission root at the top level;
      // a mission root is created only for a study that has none.
      let parentId = placeParent
      if (!parentId) {
        // At root level 0 with no mission root, create the mission element first
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
            segment: child.segment || segment || 'space',
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


// ─── Add Spacecraft: another level-2 element under the space segment ───

function AddSpacecraftButton({ studyId, segmentId, count }: { studyId: string | null; segmentId: string; count: number }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const add = async () => {
    if (!studyId) return
    setBusy(true)
    setError(null)
    try {
      let spacecraftClass: string | undefined
      try {
        const st = await fetch(`${API}/studies/${studyId}`).then(r => (r.ok ? r.json() : null))
        spacecraftClass = st?.requirements?.spacecraft_class ?? undefined
      } catch { /* server default */ }
      const res = await fetch(`${API}/studies/${studyId}/spacecraft`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ segment_id: segmentId, populate: true, ...(spacecraftClass ? { spacecraft_class: spacecraftClass } : {}) }),
      })
      if (!res.ok) throw new Error(await res.text())
      qc.invalidateQueries({ queryKey: ['elements', studyId] })
      qc.invalidateQueries({ queryKey: ['interfaces', studyId] })
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <>
      <Button variant="primary" size="sm" onClick={add} busy={busy}
        title={t('A spacecraft is a system (level 2) of the space segment; it gets the standard subsystems')}>
        {count === 0 ? t('+ Add Spacecraft') : t('+ Add another Spacecraft')}
      </Button>
      {error && <StatusBadge status="alarm">{t('Error: {{message}}', { message: error })}</StatusBadge>}
    </>
  )
}

// ─── Populate Button: auto-create subsystems + equipment from KB ───

function PopulateButton({ studyId, focusElementId, show }: {
  studyId: string | null; focusElementId: string | null; show: boolean
}) {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const qc = useQueryClient()

  // Shown on a segment with no system yet (creates its spacecraft or station) and on a
  // system with no subsystem yet (gives it the standard subsystems) — blockLevels.ts
  const all: any[] = qc.getQueryData(['elements', studyId]) || []
  const focus = all.find((e: any) => e.id === focusElementId)
  const onSystem = focus?.element_type === 'system'
  const seg = segmentOf(all, focusElementId)
  if (!show) return null

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
        {onSystem
          ? t('Give this spacecraft the standard subsystems (Payload, EPS, AOCS, Comms, OBC, Thermal, Structure, Propulsion) with recommended CubeSat equipment from the component catalogue.')
          : seg === 'space'
            ? t('Create a Spacecraft in this segment with the standard subsystems (Payload, EPS, AOCS, Comms, OBC, Thermal, Structure, Propulsion) and recommended CubeSat equipment from the component catalogue.')
            : t('Create a Ground Station in this segment with its standard subsystems and recommended equipment from the component catalogue.')}
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
