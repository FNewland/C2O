/**
 * linkParts — pieces shared by the Interfaces panel and the block diagram:
 * the status chip (suggested / accepted / rejected), the type label
 * (glyph + word), a one-line property summary and the link editor.
 */
import { useId, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Button, Field, Input, Select } from '../components/ui'
import { cx } from '../components/ui/util'
import {
  INTERFACE_TYPES, SUBTYPE_LABELS, TYPE_META, ruleId,
  type DesignInterface, type InterfaceStatus, type InterfaceType,
} from '../types/interfaces'
import { InterfaceGlyph } from './InterfaceGlyph'
import { useInterfaceTypes, type InterfacePatch } from './interfaceApi'
import { useUIStore } from '../stores/uiStore'
import { pickLang } from '../types/interfaces'
import './links.css'

/** Status chip: suggested = dashed outline + dash glyph + word; accepted = solid + check; rejected = struck ring. */
export function LinkStatusChip({ status, className }: { status: InterfaceStatus; className?: string }) {
  const { t } = useTranslation()
  const word = status === 'suggested' ? t('Suggested') : status === 'rejected' ? t('Rejected') : t('Accepted')
  return (
    <span className={cx('c2o-lstat', `c2o-lstat--${status}`, className)}>
      <svg viewBox="0 0 12 12" width="11" height="11" aria-hidden="true">
        {status === 'suggested' && <path d="M1 6h2.6M5 6h2M8.4 6H11" stroke="currentColor" strokeWidth="1.6" />}
        {status === 'accepted' && <path d="M1.8 6.2 4.8 9 10.2 3" fill="none" stroke="currentColor" strokeWidth="1.7" />}
        {status === 'rejected' && <><circle cx="6" cy="6" r="4.4" fill="none" stroke="currentColor" strokeWidth="1.3" /><path d="M3 9 9 3" stroke="currentColor" strokeWidth="1.3" /></>}
      </svg>
      {word}
    </span>
  )
}

export function TypeLabel({ type, short, className }: { type: InterfaceType; short?: boolean; className?: string }) {
  const { t } = useTranslation()
  const m = TYPE_META[type]
  return (
    <span className={cx('c2o-ltype', className)}>
      <InterfaceGlyph type={type} />
      <span>{t(short ? m.short : m.label)}</span>
    </span>
  )
}

/** "5 V · I2C · TM/TC": the two or three values that identify a link. */
export function propsSummary(iface: DesignInterface, t: (k: string, o?: any) => string): string {
  const p = iface.properties as Record<string, any>
  const bits: string[] = []
  if (iface.subtype && SUBTYPE_LABELS[iface.subtype]) bits.push(t(SUBTYPE_LABELS[iface.subtype]))
  const v = p.rail_voltage ?? p.voltage_v
  if (v != null && v !== '') bits.push(`${v} V`)
  if (p.protocol) bits.push(String(p.protocol))
  if (p.band) bits.push(`${p.band}`)
  if (p.frequency_mhz) bits.push(`${p.frequency_mhz} MHz`)
  if (p.conductance_w_k ?? p.conductance_w_per_k) bits.push(`${p.conductance_w_k ?? p.conductance_w_per_k} W/K`)
  if (p.mount_type) bits.push(String(p.mount_type))
  if (p.medium) bits.push(String(p.medium))
  if (p.signal) bits.push(String(p.signal))
  return bits.slice(0, 3).join(' · ')
}

/** Who made the link, in words: "Rule PWR-RAIL-01" / "You" / "Imported". */
export function originText(iface: DesignInterface, t: (k: string, o?: any) => string): string {
  const r = ruleId(iface.origin)
  if (r) return t('Rule {{id}}', { id: r })
  if (iface.origin === 'import') return t('Imported')
  return t('Added by a designer')
}

// ─── Editor ───

export interface EndpointOption { id: string; name: string }

export function LinkEditor({ iface, endpoints, onSave, onCancel, saving, compact }: {
  iface: DesignInterface
  endpoints: EndpointOption[]
  onSave: (patch: InterfacePatch) => void
  onCancel: () => void
  saving?: boolean
  compact?: boolean
}) {
  const { t, i18n } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const { types: typeInfo, served } = useInterfaceTypes(studyId)
  const [type, setType] = useState<InterfaceType>(iface.type)
  const [subtype, setSubtype] = useState<string>(iface.subtype ?? '')
  const [from, setFrom] = useState(iface.from_element_id)
  const [to, setTo] = useState(iface.to_element_id)
  const [props, setProps] = useState<Record<string, any>>(() => {
    const p: Record<string, any> = { ...iface.properties }
    if (p.rail_voltage == null && p.voltage_v != null) p.rail_voltage = p.voltage_v
    return p
  })
  const meta = TYPE_META[type]
  // The server's Annex E field list wins when served; labels then come bilingual from it.
  const info = typeInfo.find(x => x.id === type)
  const fields = served && info?.served.length
    ? info.served.map(f => ({ key: f.key, label: pickLang(f.label, i18n.language), placeholder: meta.fields.find(m => m.key === f.key)?.placeholder }))
    : meta.fields.map(f => ({ ...f, label: t(f.label) }))
  const subtypes = served && info?.subtypes.length
    ? info.subtypes.map(x => ({ id: x.id, label: pickLang(x.label, i18n.language) }))
    : meta.subtypes.map(x => ({ id: x, label: t(SUBTYPE_LABELS[x] ?? x) }))
  const headId = useId()
  const sameEnds = from === to
  const knownEnd = (id: string) => endpoints.some(e => e.id === id)

  const save = () => {
    const cleaned: Record<string, any> = {}
    for (const [k, v] of Object.entries(props)) if (v !== '' && v != null) cleaned[k] = v
    onSave({
      status: 'accepted', type, subtype: subtype || null, properties: cleaned,
      ...(from !== iface.from_element_id ? { from_element_id: from } : {}),
      ...(to !== iface.to_element_id ? { to_element_id: to } : {}),
      version: iface.version,
    })
  }

  return (
    <form className={cx('c2o-ledit', compact && 'c2o-ledit--compact')} aria-labelledby={headId}
      onSubmit={e => { e.preventDefault(); if (!sameEnds) save() }}
      onKeyDown={e => { if (e.key === 'Escape') { e.stopPropagation(); onCancel() } }}>
      <span id={headId} className="sr-only">{t('Edit link')}</span>
      <div className="c2o-ledit__grid">
        <Field label={t('Type')}>
          <Select dense value={type} onChange={e => { setType(e.target.value as InterfaceType); setSubtype('') }}>
            {INTERFACE_TYPES.map(id => <option key={id} value={id}>{t(TYPE_META[id].label)}</option>)}
          </Select>
        </Field>
        <Field label={t('Subtype')}>
          <Select dense value={subtype} onChange={e => setSubtype(e.target.value)}>
            <option value="">{t('(none)')}</option>
            {subtypes.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
          </Select>
        </Field>
        <Field label={t('From')}>
          <Select dense value={from} onChange={e => setFrom(e.target.value)}>
            {!knownEnd(from) && <option value={from}>{t('(outside this level)')}</option>}
            {endpoints.map(el => <option key={el.id} value={el.id}>{el.name}</option>)}
          </Select>
        </Field>
        <Field label={t('To')} error={sameEnds ? t('A link needs two different ends') : undefined}>
          <Select dense value={to} onChange={e => setTo(e.target.value)}>
            {!knownEnd(to) && <option value={to}>{t('(outside this level)')}</option>}
            {endpoints.map(el => <option key={el.id} value={el.id}>{el.name}</option>)}
          </Select>
        </Field>
        {fields.map(f => (
          <Field key={f.key} label={f.label}>
            <Input dense value={props[f.key] ?? ''} placeholder={f.placeholder}
              onChange={e => setProps(p => ({ ...p, [f.key]: e.target.value }))} />
          </Field>
        ))}
      </div>
      <div className="c2o-ledit__foot">
        <span className="t-12 c-3">{iface.status === 'accepted' && iface.origin === 'user'
          ? t('Saved as your link.')
          : t('Saving makes this your link: accepted, and kept if the rules change.')}</span>
        <span className="row gap-2">
          <Button size="sm" onClick={onCancel}>{t('Cancel')}</Button>
          <Button size="sm" variant="primary" type="submit" busy={saving}
            disabledReason={sameEnds ? t('A link needs two different ends') : undefined}>{t('Save and accept')}</Button>
        </span>
      </div>
    </form>
  )
}
