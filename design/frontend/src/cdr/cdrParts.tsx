/**
 * cdrParts — pieces shared by the TM/TC, FDIR, AOCS modes and Operations tabs: the panel
 * hook (load, propose, import, patch), the header with the dataset line and the group's
 * findings, the row status cell (proposal actions, or "EOSAT-1 reference" when read-only),
 * the owner tag and small editors.
 */
import { type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { askConfirm, Button, Note, Panel, Select, StatusBadge, Tag } from '../components/ui'
import { seatLabel } from '../seats/api'
import { pickLang } from '../types/interfaces'
import { CommitInput, FindingsList, ProposalCell } from '../workbench/electricalParts'
import { acceptAllCdr, importEosat1, proposeCdr, removeImport, type CdrGroup, type CdrKind, type CdrRow, type CdrView } from './cdrApi'
import { findingsOf, fmt, num, type CdrPanelCtx } from './cdrUtil'
import './cdr.css'

const GROUP_OF: Record<string, CdrGroup> = {
  settings: 'tmtc', apids: 'tmtc', services: 'tmtc', parameters: 'tmtc', hk: 'tmtc', commands: 'tmtc', events: 'tmtc', rate_tiers: 'tmtc', ttc: 'tmtc',
  monitors: 'fdir', event_actions: 'fdir', load_shed: 'fdir', safe_mode: 'fdir', fdir_levels: 'fdir', limits: 'fdir',
  aocs_modes: 'aocs', aocs_transitions: 'aocs', aocs_control: 'aocs', line_states: 'aocs', positions: 'ops', gonogo: 'ops', flight_rules: 'ops',
  link_framing: 'tmtc', stores: 'tmtc', rt_profiles: 'tmtc', service_allowances: 'tmtc', payload_products: 'tmtc', pass_classes: 'ops', pass_plan: 'ops',
}

/** The tab frame: title, dataset line, propose / reference actions, findings, then the body. */
export function CdrFrame({ ctx, group, title, owners, children, testId }: {
  ctx: CdrPanelCtx; group: CdrGroup; title: string; owners: string; children: (view: CdrView) => ReactNode; testId: string
}) {
  const { t } = useTranslation()
  const { view, isLoading, loadError, busy, error, lastRun, setLastRun, run, studyId } = ctx
  if (!studyId) return null
  if (isLoading) return <div className="c2o-pane t-13 c-3">{t('Loading…')}</div>
  if (loadError || !view) {
    return <div className="c2o-pane"><Note tone="alarm">{t('The CDR model could not be loaded: {{message}}', { message: String(loadError?.message ?? '') })}</Note></div>
  }
  const findings = findingsOf(view, group)
  const s = view.summary.by_group[group] ?? { alarm: 0, caution: 0 }
  const ref = view.dataset === 'reference'
  const propose = () => run('propose', async () => {
    const r = await proposeCdr(studyId)
    setLastRun(t('{{created}} new, {{updated}} updated, {{unchanged}} unchanged', { ...r }))
  })
  const loadRef = () => run('import', async () => {
    if (view.dataset === 'design') {
      const ok = await askConfirm(t('The study holds a design database. Loading the EOSAT-1 reference replaces it.'),
        { title: t('Replace the design database?'), confirmLabel: t('Replace'), danger: true })
      if (!ok) return
    }
    const r = await importEosat1(studyId, view.dataset === 'design')
    setLastRun(t('EOSAT-1 reference loaded: {{n}} rows', { n: r.imported }))
  })
  const dropRef = () => run('unimport', async () => { await removeImport(studyId); setLastRun(null) })
  const kindsOf = Object.entries(view.rows).filter(([k]) => (GROUP_OF[k] ?? 'tmtc') === group).flatMap(([, rs]) => rs)
  const open = kindsOf.filter(r => r.status === 'suggested').length
  const acceptAll = () => run('accept-all', async () => {
    const r = await acceptAllCdr(studyId, group)
    setLastRun(t('{{accepted}} accepted, {{left}} left for their owner', { accepted: r.accepted, left: r.left_for_owner }))
  })
  return (
    <div className="c2o-pane c2o-el c2o-cdr" data-testid={testId}>
      <Panel title={title}
        meta={t('{{alarms}} alarm, {{cautions}} caution', { alarms: s.alarm, cautions: s.caution })}
        actions={<>
          {!ref && open > 0 && <Button size="sm" onClick={acceptAll} busy={busy === 'accept-all'}
            title={t('Accept the suggestions of this tab that your seat may review')}>{t('Accept {{n}} suggestions', { n: open })}</Button>}
          {!ref && <Button size="sm" variant="primary" onClick={propose} busy={busy === 'propose'}
            title={t('Propose the default database from the design. Rejected and edited rows are kept.')}>{t('Propose from design')}</Button>}
          {ref
            ? <Button size="sm" onClick={dropRef} busy={busy === 'unimport'}>{t('Remove EOSAT-1 reference')}</Button>
            : <Button size="sm" onClick={loadRef} busy={busy === 'import'}
                title={t('Load the complete EOSAT-1 database (read-only) to study it')}>{t('Load EOSAT-1 reference')}</Button>}
        </>}>
        <p className="t-12 c-2 m-0 pb-2">
          {ref ? <><StatusBadge status="info">{t('Reference')}</StatusBadge> {t('EOSAT-1 reference database (sim/configs/eosat1), read-only: study it, then remove it to design your own.')}</>
            : view.dataset === 'empty' ? t('No CDR database yet. Propose it from the design (elements, modes, power lines, buses, sensors and actuators) or load the EOSAT-1 reference.')
              : t('Design database: rule proposals are accepted, edited or rejected by the owning seat.')}
          {' '}<span className="c-3">{owners}</span>
        </p>
        {lastRun && <p className="t-12 c-3 m-0 pb-2" role="status">{t('Last run: {{summary}}', { summary: lastRun })}</p>}
        {error && <Note tone="alarm" role="alert">{t('The server refused the change: {{message}}', { message: error })}</Note>}
        <FindingsList findings={findings} empty={t('No finding in this part of the CDR model.')} />
        {children(view)}
      </Panel>
    </div>
  )
}

/** Status cell: proposal actions, or the read-only reference tag. */
export function RowState({ ctx, kind, row, label }: { ctx: CdrPanelCtx; kind: CdrKind; row: CdrRow; label: string }) {
  const { t, i18n: ii } = useTranslation()
  if (row.origin.startsWith('import:')) {
    return <span title={pickLang(row.rationale, ii.language)}><Tag>{t('EOSAT-1 reference')}</Tag></span>
  }
  return <ProposalCell row={row} label={label} busy={ctx.busy === row.id}
    onPatch={b => ctx.patch(kind, row.id, b)} onDelete={() => ctx.remove(kind, row.id)} />
}

export function OwnerTag({ seat }: { seat: string }) {
  const { i18n: ii } = useTranslation()
  return <span className="c2o-tag t-12" title={seat}>{seatLabel(seat, ii.language) || seat}</span>
}

/** A number field committing on Enter / blur; read-only rows show the value. */
export function NumCell({ ctx, kind, row, field, label, digits = 3, width = 72 }: {
  ctx: CdrPanelCtx; kind: CdrKind; row: CdrRow; field: string; label: string; digits?: number; width?: number
}) {
  const v = row.data[field]
  if (row.origin.startsWith('import:')) return <span className="mono">{fmt(v, digits)}</span>
  return <CommitInput label={label} value={fmt(v, digits)} width={width}
    onCommit={s => { const n = num(s); if (n !== undefined) ctx.patchData(kind, row.id, { [field]: n }) }} />
}

export function SelectCell({ ctx, kind, row, field, label, options }: {
  ctx: CdrPanelCtx; kind: CdrKind; row: CdrRow; field: string; label: string; options: { value: string; label: string }[]
}) {
  const v = String(row.data[field] ?? '')
  if (row.origin.startsWith('import:')) return <span>{options.find(o => o.value === v)?.label ?? v}</span>
  return (
    <Select dense aria-label={label} value={v} onChange={e => ctx.patchData(kind, row.id, { [field]: e.target.value })}>
      {!options.some(o => o.value === v) && <option value={v}>{v}</option>}
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </Select>
  )
}

export function CheckCell({ ctx, kind, row, field, label }: { ctx: CdrPanelCtx; kind: CdrKind; row: CdrRow; field: string; label: string }) {
  return <input type="checkbox" checked={!!row.data[field]} aria-label={label} disabled={row.origin.startsWith('import:')}
    onChange={e => ctx.patchData(kind, row.id, { [field]: e.target.checked })} />
}

/** A search box filtering long tables (parameters, telecommands, events). */
export function Filter({ value, onChange, label }: { value: string; onChange: (v: string) => void; label: string }) {
  return <input className="c2o-input c2o-input--sm c2o-cdr__filter" type="search" value={value} placeholder={label}
    aria-label={label} onChange={e => onChange(e.target.value)} />
}

export function Section({ id, title, children, note }: { id: string; title: string; children: ReactNode; note?: ReactNode }) {
  return (
    <section className="c2o-el__sec" aria-labelledby={id}>
      <h4 id={id} className="c2o-links__h">{title}</h4>
      {note && <p className="t-12 c-3 m-0 pb-2 measure">{note}</p>}
      {children}
    </section>
  )
}

