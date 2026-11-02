/**
 * InterfacesPanel — Define connections between sibling elements.
 *
 * Shows interfaces involving elements at the current level.
 * Create/delete via API. Type, direction, endpoints.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { useUIStore } from '../stores/uiStore'
import { ArmButton, Button, Chevron, Field, Input, Panel, Select, Tag } from '../components/ui'

const API = '/api'

// English text is the i18n key
const INTERFACE_TYPE_LABELS: Record<string, string> = {
  electrical: 'Electrical', data: 'Data', rf: 'RF', mechanical: 'Mechanical', thermal: 'Thermal',
}

const INTERFACE_TYPES = [
  { value: 'electrical', label: INTERFACE_TYPE_LABELS.electrical, color: 'var(--cat-4)' },
  { value: 'data', label: INTERFACE_TYPE_LABELS.data, color: 'var(--cat-2)' },
  { value: 'rf', label: INTERFACE_TYPE_LABELS.rf, color: 'var(--cat-6)' },
  { value: 'mechanical', label: INTERFACE_TYPE_LABELS.mechanical, color: 'var(--cat-8)' },
  { value: 'thermal', label: INTERFACE_TYPE_LABELS.thermal, color: 'var(--cat-5)' },
]

export function InterfacesPanel() {
  const { t } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const focusElementId = useUIStore(s => s.focusElementId)
  const qc = useQueryClient()

  // Get sibling elements at current level
  const { data: allElements = [] } = useQuery({
    queryKey: ['elements', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/elements`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false, refetchInterval: 3000,
  })

  const siblings = allElements.filter((el: any) =>
    focusElementId ? el.parent_id === focusElementId : !el.parent_id
  )

  // Get interfaces for study
  const { data: allInterfaces = [] } = useQuery({
    queryKey: ['interfaces', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/interfaces`).then(r => r.json()),
    enabled: !!studyId, structuralSharing: false, refetchInterval: 3000,
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
      <div className="p-4 c-2 t-13">
        {t('Need at least 2 elements at this level to define interfaces.')}
      </div>
    )
  }

  return (
    <div className="c2o-pane">
      <Panel title={t('Interfaces ({{n}})', { n: interfaces.length })}
        actions={<Button variant="primary" size="sm" onClick={() => setShowAdd(true)}
          disabledReason={showAdd ? t('The add form is already open below') : undefined}>{t('+ Add Interface')}</Button>}>
        {interfaces.length === 0 && !showAdd && (
          <p className="t-13 c-2 m-0 py-2">{t('No interfaces defined. Click "Add Interface" to connect elements.')}</p>
        )}
        <div className="c2o-ifaces">
          {interfaces.map((iface: any) => (
            <InterfaceRow key={iface.id} iface={iface} nameOf={nameOf} studyId={studyId}
              onDelete={() => deleteMutation.mutate(iface.id)} />
          ))}
        </div>
      </Panel>

      {showAdd && (
        <form className="c2o-blocks__add" aria-label={t('Add interface')}
          onSubmit={e => { e.preventDefault(); if (fromId && toId) addMutation.mutate() }}>
          <Field label={t('From')}>
            <Select dense value={fromId} onChange={e => setFromId(e.target.value)}>
              <option value="">{t('From...')}</option>
              {siblings.map((el: any) => <option key={el.id} value={el.id}>{el.name}</option>)}
            </Select>
          </Field>
          <span className="c-3 pb-1" aria-hidden="true">→</span>
          <Field label={t('To')}>
            <Select dense value={toId} onChange={e => setToId(e.target.value)}>
              <option value="">{t('To...')}</option>
              {siblings.filter((el: any) => el.id !== fromId).map((el: any) => <option key={el.id} value={el.id}>{el.name}</option>)}
            </Select>
          </Field>
          <Field label={t('Type')}>
            <Select dense value={ifaceType} onChange={e => setIfaceType(e.target.value)}>
              {INTERFACE_TYPES.map(it => <option key={it.value} value={it.value}>{t(it.label)}</option>)}
            </Select>
          </Field>
          <Field label={t('Label (optional)')}>
            <Input dense value={ifaceName} onChange={e => setIfaceName(e.target.value)} />
          </Field>
          <span className="row gap-2">
            <Button type="submit" variant="primary" size="sm"
              disabledReason={!fromId || !toId ? t('Choose both ends of the interface first') : undefined}>{t('Add')}</Button>
            <Button size="sm" onClick={() => setShowAdd(false)}>{t('Cancel')}</Button>
          </span>
        </form>
      )}
    </div>
  )
}

// ─── Interface Row with expandable properties ───

// Labels and placeholders are display-only (the property keys are stored), so the table is built
// per render with the active t(); technical example values (part names, numbers) are not translated.
function ifacePropertyFields(t: TFunction): Record<string, Array<{ key: string; label: string; placeholder: string }>> {
  return {
    electrical: [
      { key: 'voltage_v', label: t('Voltage (V)'), placeholder: '3.3 / 5 / 28' },
      { key: 'current_a', label: t('Current (A)'), placeholder: '0.5' },
      { key: 'connector', label: t('Connector'), placeholder: t('Micro-D 9pin') },
      { key: 'wire_gauge', label: t('Wire gauge'), placeholder: 'AWG 26' },
      { key: 'power_w', label: t('Power (W)'), placeholder: '2.5' },
    ],
    data: [
      { key: 'protocol', label: t('Protocol'), placeholder: 'SPI / I2C / UART / CAN / SpaceWire' },
      { key: 'baud_rate', label: t('Baud rate'), placeholder: '115200 / 1 Mbps' },
      { key: 'data_format', label: t('Data format'), placeholder: t('CCSDS / raw bytes') },
      { key: 'bus_width', label: t('Bus width'), placeholder: t('8 / 16 / 32 bit') },
      { key: 'connector', label: t('Connector'), placeholder: 'Micro-D / Harwin' },
    ],
    rf: [
      { key: 'frequency_ghz', label: t('Frequency (GHz)'), placeholder: '0.435 / 2.2 / 8.2' },
      { key: 'bandwidth_mhz', label: t('Bandwidth (MHz)'), placeholder: '20' },
      { key: 'polarization', label: t('Polarization'), placeholder: t('RHCP / linear / dual') },
      { key: 'power_dbm', label: t('TX power (dBm)'), placeholder: '30' },
      { key: 'connector', label: t('RF connector'), placeholder: t('SMA / N-type') },
    ],
    mechanical: [
      { key: 'mount_type', label: t('Mount type'), placeholder: t('bolted / bonded / rail') },
      { key: 'fastener', label: t('Fasteners'), placeholder: 'M3×8 SS / M2.5' },
      { key: 'torque_nm', label: t('Torque (Nm)'), placeholder: '0.5' },
      { key: 'material', label: t('Material'), placeholder: 'Al 6061-T6' },
    ],
    thermal: [
      { key: 'heat_flow_w', label: t('Heat flow (W)'), placeholder: '2.0' },
      { key: 'conductance_w_k', label: t('Conductance (W/K)'), placeholder: '0.5' },
      { key: 'strap_type', label: t('Thermal strap'), placeholder: t('Cu braid / Al plate') },
      { key: 'interface_temp_c', label: t('Interface temp (°C)'), placeholder: '20' },
    ],
  }
}

function InterfaceRow({ iface, nameOf, studyId, onDelete }: {
  iface: any; nameOf: (id: string) => string; studyId: string | null; onDelete: () => void
}) {
  const { t } = useTranslation()
  const [expanded, setExpanded] = useState(false)
  const qc = useQueryClient()
  const props = iface.properties || {}
  const fields = ifacePropertyFields(t)[iface.interface_type] || []

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

  const typeLabel = INTERFACE_TYPE_LABELS[iface.interface_type] ? t(INTERFACE_TYPE_LABELS[iface.interface_type]) : iface.interface_type
  const nProps = Object.keys(props).length
  return (
    <div className="c2o-ifaces__item">
      <div className="c2o-ifaces__row">
        <button type="button" className="c2o-ifaces__toggle" aria-expanded={expanded} onClick={() => setExpanded(!expanded)}
          disabled={fields.length === 0}>
          <Chevron />
          <Tag>{typeLabel}</Tag>
          <span className="w-500">{nameOf(iface.from_element_id)}</span>
          <span className="c-3" aria-hidden="true">→</span>
          <span className="sr-only">{t('to')}</span>
          <span className="w-500">{nameOf(iface.to_element_id)}</span>
          {iface.name && <span className="c-2">{iface.name}</span>}
        </button>
        <span className="t-12 c-3">{nProps > 0 ? t('{{n}} props', { n: nProps }) : t('no properties')}</span>
        <ArmButton variant="icon" label="×" armedLabel={t('Delete')} aria-label={t('Delete interface {{from}} → {{to}}', { from: nameOf(iface.from_element_id), to: nameOf(iface.to_element_id) })}
          onConfirm={onDelete} />
      </div>
      {expanded && fields.length > 0 && (
        <div className="c2o-form-grid c2o-ifaces__props">
          {fields.map(f => (
            <Field key={f.key} label={f.label}>
              <Input dense value={props[f.key] || ''} onChange={e => updateProp(f.key, e.target.value)} placeholder={f.placeholder} />
            </Field>
          ))}
        </div>
      )}
    </div>
  )
}
