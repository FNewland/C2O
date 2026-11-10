/**
 * LicensingPanel (W5.01-W5.04): the licensing inputs the design cannot derive, the filing tracker,
 * what the study derives (frequency assignments, disposal analysis with the drag sail) and the
 * study-linked licence documents (RSSSA, ISED space and earth stations, ITU API, debris plan,
 * UN registration, export-control summary, licensing status).
 *
 * Server: GET/PUT /api/lifecycle/licensing/{study}, POST …/evidence,
 *         POST /api/exports/regulatory/{kind}/{study}?fmt=docx|json.
 * Its own workbench tab ('licensing') and the Export drawer's dialog. Edited by the Team leader and
 * Comms engineer seats; the Propulsion seat (which owns the disposal function) sees and edits the
 * disposal part only. The server refuses other seats.
 *
 * Frequencies: each earth station's power, gain and line loss come from its link case (W4.04);
 * per-assignment overrides (power, gain, EIRP) are kept in the record's assignment_overrides.
 */
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { Button, Dialog, Field, Input, Note, Select, StatusBadge, Tabs, Textarea, tabPanelProps } from '../components/ui'
import { useSeatView } from '../seats/view'

const API = '/api'
const GRID = { gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))' } as const

type Rec = Record<string, any>
type Section = 'applicant' | 'protection' | 'policy' | 'frequencies' | 'disposal' | 'filings' | 'documents'

const STATUSES = ['not_started', 'in_preparation', 'submitted', 'received', 'granted', 'granted_with_conditions', 'refused', 'not_applicable']

// English text is the i18n key: literal t() calls so the i18n check sees every label.
export function regulatoryDocs(t: TFunction): Array<{ kind: string; label: string; description: string; zip?: boolean }> {
  return [
    { kind: 'rsssa', label: t('RSSSA Licence Application'), description: t('Remote Sensing Space Systems Act filing') + ': ' + t('guide sections 1-32 and Annexes A-B, from the study') },
    { kind: 'ised-space', label: t('ISED space station technical brief'), description: t('Frequency assignments, EIRP, PFD at 5°, coordination, debris summary') },
    { kind: 'ised-earth', label: t('ISED earth station applications'), description: t('One document per ground station'), zip: true },
    { kind: 'itu-api', label: t('ITU advance publication (API)'), description: t('Space operation service; RR No. 9.21 for 449.75-450.25 MHz') },
    { kind: 'debris', label: t('Space debris mitigation plan'), description: t('ISED conditions, drag sail, solar-cycle lifetimes, reliability, collision probability') },
    { kind: 'un-registration', label: t('UN registration (Article IV)'), description: t('Registration Convention data items') },
    { kind: 'export-control', label: t('Export-control summary'), description: t('Controlled parts (SWIR camera, encryption, GNSS) and actions') },
    { kind: 'status', label: t('Licensing status and timeline'), description: t('The six filings with their status and dates') },
  ]
}

function statusLabel(t: TFunction, s: string): string {
  switch (s) {
    case 'not_started': return t('Not started')
    case 'in_preparation': return t('In preparation')
    case 'submitted': return t('Submitted')
    case 'received': return t('Received')
    case 'granted': return t('Granted')
    case 'granted_with_conditions': return t('Granted with conditions')
    case 'refused': return t('Refused')
    case 'not_applicable': return t('Not applicable')
    default: return s
  }
}

async function download(url: string, filename: string) {
  const res = await fetch(url, { method: 'POST' })
  if (!res.ok) throw new Error(`${res.status}`)
  const blob = await res.blob()
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = filename; a.click(); URL.revokeObjectURL(a.href)
}

/** The Export drawer's licensing (regulatory) group. */
export function licensingExportCategory(sid: string, t: TFunction, openLicensing: () => void) {
  return {
    name: t('Licensing'), color: 'var(--cat-3)', docs: [
      { id: 'lic-tab', label: t('Licensing inputs and filing tracker'), description: t('Applicant, command and data protection plan, filings, DRAMA/DAS results'), formats: [
        { fmt: 'OPEN', label: t('Open'), action: async () => openLicensing() },
      ]},
      ...regulatoryDocs(t).map(d => ({
        id: `reg-${d.kind}`, label: d.label, description: d.description, formats: [
          { fmt: 'DOCX', label: d.zip ? 'ZIP' : 'DOCX', action: () => download(`${API}/exports/regulatory/${d.kind}/${sid}?fmt=docx`, `${d.kind}_${sid}.${d.zip ? 'zip' : 'docx'}`) },
          { fmt: 'JSON', label: 'JSON', action: () => download(`${API}/exports/regulatory/${d.kind}/${sid}`, `${d.kind}_${sid}.json`) },
        ],
      })),
      { id: 'deorbit', label: t('Deorbit & Debris Compliance'), description: t('Orbital lifetime, casualty risk, passivation'), formats: [
        { fmt: 'DOCX', label: 'DOCX', action: () => download(`${API}/exports/deorbit/${sid}?fmt=docx`, `Deorbit_${sid}.docx`) },
        { fmt: 'JSON', label: 'JSON', action: () => download(`${API}/exports/deorbit/${sid}`, `Deorbit_${sid}.json`) },
      ]},
    ],
  }
}

// 3.L1: field help (what the RSSSA guide asks for), shown under each team input.
// English text is the i18n key: literal t() calls so the i18n check sees every label.
export function fieldHelp(t: TFunction, path: string): string | undefined {
  switch (path) {
    case 'applicant.legal_name': return t('The legal name of the organisation that will hold the licence')
    case 'applicant.address': return t('Registered address of the applicant')
    case 'applicant.contact_name': return t('The person the regulator contacts about the application')
    case 'applicant.contact_email': return t('An e-mail address, e.g. licensing@example.org')
    case 'applicant.contact_phone': return t('A telephone number with the country code, e.g. +1 555 0100')
    case 'applicant.canadian_entity': return t('Whether the applicant is a Canadian entity')
    case 'applicant.security_officer': return t('The person responsible for security of the system')
    case 'itu_network_name': return t('The name under which the satellite network is filed with the ITU')
    case 'notes': return t('Who owns 10 % or more of the applicant, and who controls it')
    case 'cdpp.command_facility': return t('Where commands are sent from, and who may send them')
    case 'cdpp.data_facility': return t('Where data are received, processed and archived')
    case 'cdpp.backup_facility': return t('The facility that takes over if the main one is lost')
    case 'cdpp.command_encryption': return t('How commands are encrypted on the uplink')
    case 'cdpp.command_authentication': return t('How the spacecraft knows a command is genuine')
    case 'cdpp.downlink_encryption': return t('How the payload data are protected on the downlink')
    case 'cdpp.key_management': return t('How keys are generated, loaded, changed and revoked')
    case 'cdpp.key_custody': return t('Who holds the keys, and under what control')
    case 'cdpp.command_process': return t('How a command is prepared, checked, sent and logged')
    case 'cdpp.personnel_security': return t('Screening of the people with access to commanding or data')
    case 'cdpp.physical_security': return t('Physical protection of the facilities and stations')
    case 'cdpp.network_security': return t('Protection of the links between the facilities')
    case 'data_policy.distribution': return t('Who receives which products, and when')
    case 'data_policy.eula': return t('The licence under which users receive the data')
    case 'data_policy.retention': return t('How long raw data and products are kept')
    case 'data_policy.disposal': return t('How data are destroyed at the end of retention')
    case 'data_policy.sensed_state_access': return t('How a sensed state obtains the data of its territory')
    case 'data_policy.priority_access': return t('Government priority access, if the licence requires it')
    case 'launch.provider': return t('The company that provides the launch')
    case 'launch.vehicle': return t('The launch vehicle')
    case 'launch.site': return t('The launch site')
    case 'launch.date': return t('YYYY-MM or YYYY-MM-DD; empty uses the mission target date')
    default: return undefined
  }
}

const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/
const PHONE = /^\+?[0-9][0-9 ().-]{5,24}$/
const DATE = /^\d{4}(-\d{2}(-\d{2})?)?$/

/** The format problem of a typed value (mirrors licensing.field_problem on the server). */
export function fieldError(t: TFunction, fmt: string | undefined, v: unknown): string | undefined {
  const s = v === null || v === undefined ? '' : String(v).trim()
  if (!s || !fmt) return undefined
  if (fmt === 'email' && !EMAIL.test(s)) return t('Not an e-mail address')
  if (fmt === 'phone' && !PHONE.test(s)) return t('Not a telephone number (digits, spaces, + ( ) - .)')
  if (fmt === 'date' && !DATE.test(s)) return t('Not a date (YYYY, YYYY-MM or YYYY-MM-DD)')
  return undefined
}

type FieldSpec = { path: string; tab: string; rsssa: string; required: boolean; list?: boolean; format?: string }

function getPath(rec: Rec | null, path: string): unknown {
  let o: any = rec
  for (const k of path.split('.')) { if (o == null || typeof o !== 'object') return undefined; o = o[k] }
  return o
}

function isFilled(v: unknown, list?: boolean): boolean {
  if (list) return Array.isArray(v) && v.some(x => x && typeof x === 'object' && Object.values(x).some(y => String(y ?? '').trim() !== ''))
  if (typeof v === 'boolean') return true
  return v !== null && v !== undefined && String(v).trim() !== ''
}

/** Live progress of the required inputs (the server's ``progress.fields``, counted on the local record). */
export function liveProgress(t: TFunction, fields: FieldSpec[], rec: Rec | null) {
  const tabs: Record<string, [number, number]> = {}
  let n = 0, m = 0, a = 0, b = 0
  for (const f of fields) {
    if (!f.required) continue
    const v = getPath(rec, f.path)
    const ok = isFilled(v, f.list) && !fieldError(t, f.format, v)
    m++; if (ok) n++
    const tb = tabs[f.tab] ?? (tabs[f.tab] = [0, 0]); tb[1]++; if (ok) tb[0]++
    const sec = parseInt(f.rsssa, 10)
    if (sec >= 14 && sec <= 30) { b++; if (ok) a++ }
  }
  return { filled: n, total: m, percent: m ? Math.round(100 * n / m) : 100, tabs, rsssa: [a, b] as [number, number] }
}

function TextField({ label, value, onChange, area, path, fields }: {
  label: string; value: string; onChange: (v: string) => void; area?: boolean; path?: string; fields?: FieldSpec[]
}) {
  const { t } = useTranslation()
  const spec = path ? fields?.find(f => f.path === path) : undefined
  const help = path ? fieldHelp(t, path) : undefined
  const sec = spec?.rsssa ? t('RSSSA §{{n}}', { n: spec.rsssa }) : ''
  return (
    <Field label={<>{label}{spec?.required && <span aria-hidden="true" className="c-2"> *</span>}</>}
      help={[help, sec].filter(Boolean).join(' · ') || undefined}
      error={fieldError(t, spec?.format, value)}>
      {area ? <Textarea rows={2} value={value ?? ''} onChange={e => onChange(e.target.value)} aria-required={spec?.required || undefined} />
            : <Input value={value ?? ''} onChange={e => onChange(e.target.value)} aria-required={spec?.required || undefined} />}
    </Field>
  )
}

function RowsEditor({ rows, cols, onChange, addLabel }: {
  rows: Rec[]; cols: Array<{ key: string; label: string }>; onChange: (rows: Rec[]) => void; addLabel: string
}) {
  const { t } = useTranslation()
  return (
    <div className="stack gap-1">
      {rows.map((r, i) => (
        <div key={i} className="flex gap-1 ai-c">
          {cols.map(c => (
            <Input key={c.key} dense aria-label={c.label} placeholder={c.label} value={r[c.key] ?? ''}
              onChange={e => onChange(rows.map((x, j) => j === i ? { ...x, [c.key]: e.target.value } : x))} />
          ))}
          <Button size="sm" onClick={() => onChange(rows.filter((_, j) => j !== i))} aria-label={t('Remove')}>×</Button>
        </div>
      ))}
      <div><Button size="sm" onClick={() => onChange([...rows, {}])}>{addLabel}</Button></div>
    </div>
  )
}

/** Seats that see only the disposal part of the tab (the Propulsion seat owns the disposal function). */
const DISPOSAL_SEATS = new Set(['propulsion_engineer'])
const OVERRIDE_FIELDS = ['tx_power_w', 'antenna_gain_dbi', 'eirp_dbw'] as const

export function LicensingPanel({ studyId }: { studyId: string }) {
  const { t } = useTranslation()
  const seat = useSeatView()
  const disposalOnly = !!seat.active && DISPOSAL_SEATS.has(seat.active) && !seat.instructor
  const [tab, setTab] = useState<Section>(disposalOnly ? 'disposal' : 'applicant')
  useEffect(() => { if (disposalOnly) setTab(cur => (cur === 'disposal' || cur === 'documents') ? cur : 'disposal') }, [disposalOnly])
  const [data, setData] = useState<Rec | null>(null)
  const [rec, setRec] = useState<Rec | null>(null)
  const [version, setVersion] = useState(0)
  const [dirty, setDirty] = useState(false)
  const [msg, setMsg] = useState<{ tone: 'ok' | 'alarm'; text: string } | null>(null)
  const [busy, setBusy] = useState(false)
  const [evidence, setEvidence] = useState({ tool: 'DRAMA', version: '', text: '' })

  const load = useCallback(async () => {
    const r = await fetch(`${API}/lifecycle/licensing/${studyId}`)
    if (!r.ok) { setMsg({ tone: 'alarm', text: t('Could not load the licensing record ({{status}})', { status: r.status }) }); return }
    const j = await r.json()
    setData(j); setRec(j.record); setVersion(j.version); setDirty(false)
  }, [studyId, t])
  useEffect(() => { void load() }, [load])

  const set = (path: string[], value: unknown) => {
    setRec(prev => {
      const next: Rec = structuredClone(prev ?? {})
      let o = next
      for (const k of path.slice(0, -1)) { o[k] = o[k] ?? {}; o = o[k] }
      o[path[path.length - 1]] = value
      return next
    })
    setDirty(true)
  }

  const filings: Rec[] = useMemo(() => {
    const stored: Rec[] = rec?.filings ?? []
    return (data?.filings ?? []).map((f: Rec) => ({ ...f, ...(stored.find(s => s.id === f.id) ?? {}) }))
  }, [data, rec])
  const setFiling = (id: string, key: string, value: string) => {
    const next = filings.map(f => f.id === id ? { ...f, [key]: value } : f)
      .map(f => ({ id: f.id, status: f.status, submitted: f.submitted, received: f.received, granted: f.granted,
                   reference: f.reference, conditions: f.conditions, notes: f.notes }))
    set(['filings'], next)
  }

  const save = async () => {
    if (!rec) return
    setBusy(true); setMsg(null)
    const { filings: f, ...rest } = rec
    // The Propulsion seat writes the disposal part only (the server refuses the rest).
    const body = disposalOnly ? { disposal: rec.disposal ?? {}, version }
      : { ...rest, filings: (f ?? []).filter((x: Rec) => x && x.id), version }
    const r = await fetch(`${API}/lifecycle/licensing/${studyId}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    setBusy(false)
    if (r.status === 409) { setMsg({ tone: 'alarm', text: t('Someone else saved the licensing record first: reloaded.') }); await load(); return }
    if (!r.ok) { const j = await r.json().catch(() => ({})); setMsg({ tone: 'alarm', text: typeof j.detail === 'string' ? j.detail : (j.detail?.message ?? `${r.status}`) }); return }
    setMsg({ tone: 'ok', text: t('Licensing record saved') })
    await load()
  }

  const importEvidence = async () => {
    setBusy(true); setMsg(null)
    const r = await fetch(`${API}/lifecycle/licensing/${studyId}/evidence`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(evidence) })
    setBusy(false)
    if (!r.ok) { setMsg({ tone: 'alarm', text: t('Import failed ({{status}})', { status: r.status }) }); return }
    setEvidence({ tool: evidence.tool, version: '', text: '' })
    setMsg({ tone: 'ok', text: t('Result imported') })
    await load()
  }

  if (!data || !rec) return <div className="c2o-pane">{msg ? <Note tone={msg.tone}>{msg.text}</Note> : t('Loading…')}</div>
  const d: Rec = data.derived ?? {}
  const disp: Rec = d.disposal ?? {}
  const ap = rec.applicant ?? {}, cd = rec.cdpp ?? {}, dp = rec.data_policy ?? {}, ln = rec.launch ?? {}, rd = rec.disposal ?? {}

  const allTabs: Array<{ id: Section; label: string }> = [
    { id: 'applicant', label: t('Applicant') }, { id: 'protection', label: t('Command and data protection') },
    { id: 'policy', label: t('Data policy and launch') }, { id: 'frequencies', label: t('Frequencies') },
    { id: 'disposal', label: t('Disposal') }, { id: 'filings', label: t('Filings') }, { id: 'documents', label: t('Documents') },
  ]
  const fields: FieldSpec[] = data.progress?.fields ?? []
  const prog = liveProgress(t, fields, rec)
  for (const x of allTabs) {
    const tp = prog.tabs[x.id]
    if (tp) x.label = `${x.label} (${tp[0]}/${tp[1]})`
  }
  const tabs = disposalOnly ? allTabs.filter(x => x.id === 'disposal' || x.id === 'documents') : allTabs
  const overrides: Rec = rec.assignment_overrides ?? {}
  const setOverride = (aid: string, field: string, value: string) => {
    const cur: Rec = { ...(overrides[aid] ?? {}) }
    // '' clears the override (the record keeps the key; the server ignores empty values)
    cur[field] = value === '' ? '' : Number(value)
    set(['assignment_overrides'], { ...overrides, [aid]: cur })
  }

  return (
    <div className="c2o-pane stack gap-2">
      <div className="flex ai-c gap-2">
        <Tabs label={t('Licensing')} idBase="lic" value={tab} onChange={setTab} items={tabs} variant="segmented" />
        <span className="grow" />
        <Button size="sm" variant="primary" onClick={save} busy={busy} disabledReason={!dirty ? t('No changes') : undefined}>{t('Save')}</Button>
      </div>
      {msg && <Note tone={msg.tone} role={msg.tone === 'alarm' ? 'alert' : 'status'}>{msg.text}</Note>}
      {!disposalOnly && fields.length > 0 && (
        <div className="stack gap-0" data-testid="licensing-progress">
          <div className="flex ai-c gap-2 t-12">
            <span className="w-600">{t('Licensing inputs: {{n}} of {{m}} ({{p}} %)', { n: prog.filled, m: prog.total, p: prog.percent })}</span>
            <span className="c-2">{t('RSSSA §14–30: {{a}} of {{b}}', { a: prog.rsssa[0], b: prog.rsssa[1] })}</span>
            {dirty && <span className="c-2">{t('(not saved yet)')}</span>}
          </div>
          <progress max={prog.total} value={prog.filled} aria-label={t('Licensing inputs filled')} style={{ width: '100%', height: 6 }} />
        </div>
      )}
      {disposalOnly && <p className="t-12 c-2 m-0">{t('Your seat owns the disposal function: you see and edit the disposal part of the licensing record.')}</p>}

      <div {...tabPanelProps('lic', tab)} className="stack gap-2">
        {tab === 'applicant' && (<>
          <div className="grid gap-2" style={GRID}>
            <TextField label={t('Legal name')} value={ap.legal_name} path="applicant.legal_name" fields={fields} onChange={v => set(['applicant', 'legal_name'], v)} />
            <TextField label={t('Address')} value={ap.address} path="applicant.address" fields={fields} onChange={v => set(['applicant', 'address'], v)} />
            <TextField label={t('Contact person')} value={ap.contact_name} path="applicant.contact_name" fields={fields} onChange={v => set(['applicant', 'contact_name'], v)} />
            <TextField label={t('E-mail')} value={ap.contact_email} path="applicant.contact_email" fields={fields} onChange={v => set(['applicant', 'contact_email'], v)} />
            <TextField label={t('Telephone')} value={ap.contact_phone} path="applicant.contact_phone" fields={fields} onChange={v => set(['applicant', 'contact_phone'], v)} />
            <TextField label={t('Security officer')} value={ap.security_officer} path="applicant.security_officer" fields={fields} onChange={v => set(['applicant', 'security_officer'], v)} />
            <Field label={t('Canadian entity')}>
              <Select value={ap.canadian_entity === true ? 'yes' : ap.canadian_entity === false ? 'no' : ''}
                onChange={e => set(['applicant', 'canadian_entity'], e.target.value === '' ? null : e.target.value === 'yes')}>
                <option value="">—</option><option value="yes">{t('Yes')}</option><option value="no">{t('No')}</option>
              </Select>
            </Field>
            <TextField label={t('ITU satellite network name')} value={rec.itu_network_name} path="itu_network_name" fields={fields} onChange={v => set(['itu_network_name'], v)} />
          </div>
          <h4 className="c2o-panel__title">{t('System participants')}</h4>
          <RowsEditor rows={rec.participants ?? []} onChange={v => set(['participants'], v)} addLabel={t('Add participant')}
            cols={[{ key: 'name', label: t('Name') }, { key: 'role', label: t('Role') }, { key: 'country', label: t('Country') }]} />
          <h4 className="c2o-panel__title">{t('Affiliates')}</h4>
          <RowsEditor rows={rec.affiliates ?? []} onChange={v => set(['affiliates'], v)} addLabel={t('Add affiliate')}
            cols={[{ key: 'name', label: t('Name') }, { key: 'relationship', label: t('Relationship') }, { key: 'country', label: t('Country') }]} />
          <TextField area label={t('Ownership and control')} value={rec.notes} path="notes" fields={fields} onChange={v => set(['notes'], v)} />
        </>)}

        {tab === 'protection' && (
          <div className="grid gap-2" style={GRID}>
            <TextField area label={t('Command facility (mission control)')} value={cd.command_facility} path="cdpp.command_facility" fields={fields} onChange={v => set(['cdpp', 'command_facility'], v)} />
            <TextField area label={t('Data facility (processing and archive)')} value={cd.data_facility} path="cdpp.data_facility" fields={fields} onChange={v => set(['cdpp', 'data_facility'], v)} />
            <TextField area label={t('Backup facility')} value={cd.backup_facility} path="cdpp.backup_facility" fields={fields} onChange={v => set(['cdpp', 'backup_facility'], v)} />
            <TextField area label={t('Command encryption')} value={cd.command_encryption} path="cdpp.command_encryption" fields={fields} onChange={v => set(['cdpp', 'command_encryption'], v)} />
            <TextField area label={t('Command authentication')} value={cd.command_authentication} path="cdpp.command_authentication" fields={fields} onChange={v => set(['cdpp', 'command_authentication'], v)} />
            <TextField area label={t('Downlink encryption')} value={cd.downlink_encryption} path="cdpp.downlink_encryption" fields={fields} onChange={v => set(['cdpp', 'downlink_encryption'], v)} />
            <TextField area label={t('Key management')} value={cd.key_management} path="cdpp.key_management" fields={fields} onChange={v => set(['cdpp', 'key_management'], v)} />
            <TextField area label={t('Key custody')} value={cd.key_custody} path="cdpp.key_custody" fields={fields} onChange={v => set(['cdpp', 'key_custody'], v)} />
            <TextField area label={t('Command process and procedures')} value={cd.command_process} path="cdpp.command_process" fields={fields} onChange={v => set(['cdpp', 'command_process'], v)} />
            <TextField area label={t('Personnel security')} value={cd.personnel_security} path="cdpp.personnel_security" fields={fields} onChange={v => set(['cdpp', 'personnel_security'], v)} />
            <TextField area label={t('Physical security')} value={cd.physical_security} path="cdpp.physical_security" fields={fields} onChange={v => set(['cdpp', 'physical_security'], v)} />
            <TextField area label={t('Network security')} value={cd.network_security} path="cdpp.network_security" fields={fields} onChange={v => set(['cdpp', 'network_security'], v)} />
          </div>
        )}

        {tab === 'policy' && (
          <div className="grid gap-2" style={GRID}>
            <TextField area label={t('Data distribution')} value={dp.distribution} path="data_policy.distribution" fields={fields} onChange={v => set(['data_policy', 'distribution'], v)} />
            <TextField area label={t('End-user licence agreement (EULA)')} value={dp.eula} path="data_policy.eula" fields={fields} onChange={v => set(['data_policy', 'eula'], v)} />
            <TextField area label={t('Data retention')} value={dp.retention} path="data_policy.retention" fields={fields} onChange={v => set(['data_policy', 'retention'], v)} />
            <TextField area label={t('Data disposal')} value={dp.disposal} path="data_policy.disposal" fields={fields} onChange={v => set(['data_policy', 'disposal'], v)} />
            <TextField area label={t('Sensed-state access')} value={dp.sensed_state_access} path="data_policy.sensed_state_access" fields={fields} onChange={v => set(['data_policy', 'sensed_state_access'], v)} />
            <TextField area label={t('Priority access')} value={dp.priority_access} path="data_policy.priority_access" fields={fields} onChange={v => set(['data_policy', 'priority_access'], v)} />
            <TextField label={t('Launch provider')} value={ln.provider} path="launch.provider" fields={fields} onChange={v => set(['launch', 'provider'], v)} />
            <TextField label={t('Launch vehicle')} value={ln.vehicle} path="launch.vehicle" fields={fields} onChange={v => set(['launch', 'vehicle'], v)} />
            <TextField label={t('Launch site')} value={ln.site} path="launch.site" fields={fields} onChange={v => set(['launch', 'site'], v)} />
            <TextField label={t('Deployer')} value={ln.deployer} path="launch.deployer" fields={fields} onChange={v => set(['launch', 'deployer'], v)} />
            <TextField label={t('Launch date (overrides the mission target)')} value={ln.date} path="launch.date" fields={fields} onChange={v => set(['launch', 'date'], v)} />
          </div>
        )}

        {tab === 'frequencies' && (
          <div className="c2o-table-wrap">
            <table className="c2o-table t-12">
              <thead><tr>
                <th>{t('Assignment')}</th><th>{t('Station')}</th><th>{t('Direction')}</th><th>{t('Centre (MHz)')}</th>
                <th>{t('Emission')}</th><th>{t('Power (W)')}</th><th>{t('EIRP (dBW)')}</th><th>{t('PFD at 5° (dBW/m²/4 kHz)')}</th>
                <th>{t('Service')}</th><th>{t('Link case')}</th><th>{t('Override power (W)')}</th>
                <th>{t('Override gain (dBi)')}</th><th>{t('Override EIRP (dBW)')}</th>
              </tr></thead>
              <tbody>
                {(d.assignments ?? []).map((a: Rec) => (
                  <tr key={a.id}>
                    <td className="mono">{a.id}</td><td>{a.station}</td><td>{a.direction}{a.fallback ? ` (${t('fallback')})` : ''}</td>
                    <td className="mono">{a.centre_frequency_mhz}</td><td className="mono">{a.emission_designator}</td>
                    <td className="mono">{a.tx_power_w ?? '—'}</td><td className="mono">{a.eirp_dbw ?? '—'}</td>
                    <td className="mono">{a.pfd_5deg_dbw_m2_4khz ?? '—'}</td><td title={a.coordination}>{a.service}</td>
                    <td>{a.link_case ? `${a.link_case.name}${a.link_case.margin_db != null ? ` (${t('margin')} ${Number(a.link_case.margin_db).toFixed(1)} dB)` : ''}` : '—'}</td>
                    {OVERRIDE_FIELDS.map(k => (
                      <td key={k}>{a.transmits
                        ? <Input dense numeric aria-label={`${a.id} ${k}`} value={overrides[a.id]?.[k] ?? ''}
                            placeholder={k === 'eirp_dbw' ? String(a.eirp_dbw ?? '') : k === 'tx_power_w' ? String(a.tx_power_w ?? '') : String(a.antenna_gain_dbi ?? '')}
                            onChange={e => setOverride(a.id, k, e.target.value)} />
                        : '—'}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="t-12 c-2">{t('Derived from the TT&C properties, the mission link and the ground stations. Not amateur, not meteorological aids: the space operation service.')}</p>
            <p className="t-12 c-2">{t('Each earth station takes its power, antenna gain and line loss from its link case. An override here wins over the link case in the ISED documents; save, then the EIRP is recomputed.')}</p>
          </div>
        )}

        {tab === 'disposal' && (<>
          {disp.error && <Note tone="alarm">{disp.error}</Note>}
          {disp.sail
            ? <Note tone={disp.compliant ? 'ok' : 'caution'}>{t('With the {{area}} m² sail: {{s}} / {{n}} / {{w}} y (strong / nominal / weak cycle) from {{alt}} km; without it {{lo}}-{{hi}} y.', {
                area: disp.sail.deployed_area_m2, s: disp.lifetime_with_sail_y?.strong, n: disp.lifetime_with_sail_y?.nominal,
                w: disp.lifetime_with_sail_y?.weak, alt: disp.altitude_km, lo: disp.without_sail_range_y?.[0], hi: disp.without_sail_range_y?.[1] })}</Note>
            : <Note tone="caution">{t('No drag sail in the product tree: natural decay only.')}</Note>}
          <table className="c2o-table t-12">
            <thead><tr><th>{t('Check')}</th><th>{t('ISED condition')}</th><th>{t('Value')}</th><th>{t('Limit')}</th><th>{t('Result')}</th></tr></thead>
            <tbody>
              {(disp.checks ?? []).map((c: Rec) => (
                <tr key={c.id}><td className="mono">{c.id}</td><td>{c.rule}</td><td className="mono">{String(c.value)} {c.unit}</td>
                  <td className="mono">{c.limit} {c.unit}</td><td>{c.pass === true ? t('Pass') : c.pass === false ? t('Fail') : t('Open')}</td></tr>
              ))}
            </tbody>
          </table>
          <div className="grid gap-2" style={GRID}>
            <Field label={t('Mass used for the decay')}>
              <Select value={rd.mass_basis ?? 'allocation'} onChange={e => set(['disposal', 'mass_basis'], e.target.value)}>
                <option value="allocation">{t('Mass allocation (conservative)')}</option>
                <option value="with_margin">{t('With margins')}</option>
                <option value="cbe">{t('Current best estimate')}</option>
              </Select>
            </Field>
            <Field label={t('Independent release circuits')}>
              <Input numeric value={rd.independent_circuits ?? ''} onChange={e => set(['disposal', 'independent_circuits'], e.target.value === '' ? null : Number(e.target.value))} />
            </Field>
            <Field label={t('Mechanism reliability')}>
              <Input numeric value={rd.mechanism_reliability ?? ''} onChange={e => set(['disposal', 'mechanism_reliability'], e.target.value === '' ? null : Number(e.target.value))} />
            </Field>
            <Field label={t('Reliability of one release circuit')}>
              <Input numeric value={rd.circuit_reliability ?? ''} onChange={e => set(['disposal', 'circuit_reliability'], e.target.value === '' ? null : Number(e.target.value))} />
            </Field>
          </div>
          <h4 className="c2o-panel__title">{t('DRAMA / DAS result')}</h4>
          {(rec.evidence ?? []).map((ev: Rec, i: number) => (
            <p key={i} className="t-12 m-0">{ev.tool} {ev.version}: {t('lifetime')} {ev.lifetime_years ?? '—'} y, Pc {ev.collision_probability ?? '—'}, {t('casualty risk')} {ev.casualty_risk ?? '—'}</p>
          ))}
          <div className="grid gap-2" style={GRID}>
            <Field label={t('Tool')}>
              <Select value={evidence.tool} onChange={e => setEvidence({ ...evidence, tool: e.target.value })}>
                <option>DRAMA</option><option>DAS</option><option>STELA</option>
              </Select>
            </Field>
            <TextField label={t('Tool version')} value={evidence.version} onChange={v => setEvidence({ ...evidence, version: v })} />
          </div>
          <TextField area label={t('Paste the tool report (lifetime, collision probability and casualty risk are read from it)')}
            value={evidence.text} onChange={v => setEvidence({ ...evidence, text: v })} />
          <div><Button size="sm" onClick={importEvidence} busy={busy} disabledReason={!evidence.text ? t('Paste a report first') : undefined}>{t('Import result')}</Button></div>
          <DebrisAssessmentCard studyId={studyId} />
        </>)}

        {tab === 'filings' && (
          <table className="c2o-table t-12">
            <thead><tr><th>{t('Filing')}</th><th>{t('Start by')}</th><th>{t('Status')}</th><th>{t('Submitted')}</th><th>{t('Received')}</th><th>{t('Granted')}</th><th>{t('Conditions')}</th></tr></thead>
            <tbody>
              {filings.map(f => (
                <tr key={f.id}>
                  <td>{f.title}<div className="c-2">{f.authority}</div></td>
                  <td className="mono">{f.start_by}</td>
                  <td><Select dense aria-label={t('Status')} value={f.status} onChange={e => setFiling(f.id, 'status', e.target.value)}>
                    {(data.filing_statuses ?? STATUSES).map((s: string) => <option key={s} value={s}>{statusLabel(t, s)}</option>)}
                  </Select></td>
                  {(['submitted', 'received', 'granted'] as const).map(k => (
                    <td key={k}><Input dense type="date" aria-label={k === 'submitted' ? t('Submitted') : k === 'received' ? t('Received') : t('Granted')}
                      value={f[k] ?? ''} onChange={e => setFiling(f.id, k, e.target.value)} /></td>
                  ))}
                  <td><Input dense aria-label={t('Conditions')} value={f.conditions ?? ''} onChange={e => setFiling(f.id, 'conditions', e.target.value)} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {tab === 'documents' && (
          <div className="stack gap-1">
            {regulatoryDocs(t).map(doc => (
              <div key={doc.kind} className="flex ai-c gap-2 bb py-1">
                <div className="grow min0"><div className="w-600 t-12">{doc.label}</div><div className="t-12 c-2">{doc.description}</div></div>
                <Button size="sm" onClick={() => download(`${API}/exports/regulatory/${doc.kind}/${studyId}?fmt=docx`, `${doc.kind}_${studyId}.${doc.zip ? 'zip' : 'docx'}`)
                  .catch(e => setMsg({ tone: 'alarm', text: String(e) }))}>{doc.zip ? 'ZIP' : 'DOCX'}</Button>
              </div>
            ))}
            <p className="t-12 c-2">{t('To be confirmed before filing:')}</p>
            <ul className="t-12 c-2 m-0">{(data.to_be_confirmed ?? []).map((x: Rec) => <li key={x.id}>{x.text}</li>)}</ul>
          </div>
        )}
      </div>
    </div>
  )
}

const GATE_CHOICES = ['mdr', 'prr', 'srr', 'pdr', 'cdr']

function sci(v: unknown): string {
  return typeof v === 'number' ? (v === 0 ? '0' : v.toExponential(1)) : '—'
}

/**
 * The debris assessment in the tool (3.L8, PI addendum): lifetime with and without the sail
 * (OSCAR-like), collision probability (ARES-like) and casualty risk of the uncontrolled re-entry
 * (DAS-like), run, reviewed and accepted at a gate (SRR in the walkthrough).
 * Server: GET/POST /api/studies/{id}/debris-assessment[/run|/accept].
 */
export function DebrisAssessmentCard({ studyId }: { studyId: string }) {
  const { t } = useTranslation()
  const [data, setData] = useState<Rec | null>(null)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<{ tone: 'ok' | 'alarm'; text: string } | null>(null)
  const [gate, setGate] = useState('srr')
  const [deviation, setDeviation] = useState('')
  const base = `${API}/studies/${encodeURIComponent(studyId)}/debris-assessment`
  const load = useCallback(async () => {
    const r = await fetch(base)
    if (r.ok) setData(await r.json())
  }, [base])
  useEffect(() => { void load() }, [load])
  const post = async (path: string, body: Rec, ok: string) => {
    setBusy(true); setMsg(null)
    const r = await fetch(`${base}/${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    setBusy(false)
    const j = await r.json().catch(() => ({}))
    if (!r.ok) { setMsg({ tone: 'alarm', text: typeof j.detail === 'string' ? j.detail : (j.detail?.message ?? `${r.status}`) }); return }
    setMsg({ tone: 'ok', text: ok }); await load()
  }
  if (!data) return null
  const a: Rec | null = data.latest
  const ev: Rec = data.evidence ?? {}
  const lt: Rec = a?.lifetime ?? {}
  const cas: Rec = a?.casualty ?? {}
  const col: Rec = a?.collision ?? {}
  const scen = (o: Rec | undefined) => o ? ['strong', 'nominal', 'weak'].map(k => o[k] ?? '—').join(' / ') : '—'
  return (
    <section className="stack gap-1" aria-label={t('Debris assessment')} data-testid="debris-assessment">
      <div className="flex ai-c gap-2">
        <h4 className="c2o-panel__title m-0">{t('Debris assessment')}</h4>
        {a && <StatusBadge status={a.status === 'accepted' ? 'ok' : a.status === 'superseded' ? 'stale' : 'caution'}>
          {a.status === 'accepted' ? t('Accepted at {{gate}}', { gate: String(a.accepted_gate).toUpperCase() })
            : a.status === 'superseded' ? t('Superseded') : t('Not accepted yet')}</StatusBadge>}
        {ev.stale && <StatusBadge status="stale">{t('The design changed since this run')}</StatusBadge>}
        <span className="grow" />
        <Button size="sm" onClick={() => post('run', {}, t('Assessment run'))} busy={busy}>{a ? t('Run again') : t('Run the assessment')}</Button>
      </div>
      <p className="t-12 c-2 m-0">{t('Screening in the tool (lifetime as OSCAR, collision probability as ARES, re-entry casualty as DAS). A licence quotes DRAMA or DAS: import their result above.')}</p>
      {msg && <Note tone={msg.tone} role={msg.tone === 'alarm' ? 'alert' : 'status'}>{msg.text}</Note>}
      {!a && <p className="t-12 c-2 m-0">{t('No assessment yet: run it once the disposal design is set.')}</p>}
      {a && (<>
        <table className="c2o-table c2o-table--dense t-12">
          <tbody>
            <tr><td>{t('Version')}</td><td className="mono">v{a.version}</td></tr>
            <tr><td>{t('Lifetime with the sail, strong / nominal / weak cycle')}</td><td className="mono">{scen(lt.with_device_y)} y</td></tr>
            <tr><td>{t('Lifetime without the sail, strong / nominal / weak cycle')}</td><td className="mono">{scen(lt.without_device_y)} y</td></tr>
            <tr><td>{t('Collision probability, objects ≥ 10 cm (operational life)')}</td><td className="mono">{sci(col.operational_large)} ({t('limit')} {sci(col.limit_large)})</td></tr>
            <tr><td>{t('Collision probability, objects < 10 cm (operational life)')}</td><td className="mono">{sci(col.operational_small)} ({t('limit')} {sci(col.limit_small)})</td></tr>
            <tr><td>{t('Casualty expectation of the re-entry')}</td><td className="mono">{sci(cas.casualty_expectation)}{cas.one_in ? ` (1:${cas.one_in})` : ''} ({t('limit')} 1:10000)</td></tr>
            <tr><td>{t('Debris casualty area')}</td><td className="mono">{cas.dca_m2 ?? '—'} m²</td></tr>
          </tbody>
        </table>
        <table className="c2o-table c2o-table--dense t-12">
          <thead><tr><th>{t('Check')}</th><th>{t('ISED condition')}</th><th>{t('Value')}</th><th>{t('Result')}</th></tr></thead>
          <tbody>{(a.checks ?? []).map((c: Rec) => (
            <tr key={c.id}><td className="mono">{c.id}</td><td>{c.rule}</td><td className="mono">{String(c.value)} {c.unit}</td>
              <td>{c.pass === true ? t('Pass') : c.pass === false ? t('Fail') : t('Open')}</td></tr>))}</tbody>
        </table>
        {a.status !== 'accepted' && (
          <div className="flex gap-2 ai-e wrap">
            <Field label={t('Accept at gate')}>
              <Select dense value={gate} onChange={e => setGate(e.target.value)}>
                {GATE_CHOICES.map(g => <option key={g} value={g}>{g.toUpperCase()}</option>)}
              </Select>
            </Field>
            {!a.compliant && <TextField label={t('Deviation (a check fails)')} value={deviation} onChange={setDeviation} />}
            <Button size="sm" variant="primary" busy={busy} onClick={() => post('accept', { gate, deviation }, t('Assessment accepted'))}
              disabledReason={!a.compliant && !deviation.trim() ? t('A failing assessment needs a deviation note') : undefined}>
              {t('Accept the assessment')}</Button>
          </div>
        )}
        {a.status === 'accepted' && <p className="t-12 c-2 m-0">{t('Accepted by {{by}} at {{gate}}.', { by: a.accepted_by, gate: String(a.accepted_gate).toUpperCase() })}</p>}
      </>)}
    </section>
  )
}

/** The panel in a dialog (opened from the Export drawer's Licensing group). */
export function LicensingDialog({ studyId, onClose }: { studyId: string; onClose: () => void }) {
  const { t } = useTranslation()
  return (
    <Dialog open title={t('Licensing')} onClose={onClose} width={1000}
      actions={<button type="button" className="c2o-btn" onClick={onClose}>{t('Close')}</button>}>
      <LicensingPanel studyId={studyId} />
    </Dialog>
  )
}
