/**
 * AllocationLedger — the budget allocations each owner seat signs up to (wave 3, 3.A2).
 *
 * Systems proposes a line per element and budget (mass, orbit-average / peak / per-mode power,
 * data, pointing, registration, timing); the owner seat agrees it or disputes it with a reason.
 * Another seat's edit goes to the owner as a pending change (the seat fetch wrapper asks for the
 * confirmation and shows the toast). The Systems reserve and the closure per resource sit on top.
 *
 * Server: routers/elements.py (GET/POST /studies/{id}/allocation-ledger, POST …/propose,
 * PATCH …/{line}, POST …/{line}/agree, POST …/{line}/dispute). Mounted in BudgetPanel.
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import i18n from '../i18n'
import { Button, DataTable, Note, Panel, StatusBadge, askText, fmtNum, type Column } from '../components/ui'
import { seatLabel } from '../seats/api'
import { ImpactPreview } from '../components/ImpactPreview'

const API = '/api'

interface LedgerLine {
  id: string; element_code: string; element_id?: string | null; budget_type: string; mode_key: string; value: number | null; unit: string
  cbe: number | null; margined: number | null; requirement_code: string; owner_seat: string
  status: 'proposed' | 'agreed' | 'disputed'; agreed_by: string; agreed_at: string | null; version: number
  rationale: string; type_label?: { en: string; fr: string }
  data_json?: { dispute?: { reason: string; by: string }; requirement_sync?: { status: string; proposed_value?: number; requirement_code?: string }; pending_change_id?: string } | null
}
interface Closure { lines: number; sum: number; system_margin_percent: number; with_system_margin: number; limit: number | null; reserve: number | null; closes: boolean | null; unit: string }
interface Ledger { items: LedgerLine[]; closure: Record<string, Closure>; counts: { lines: number; by_status: Record<string, number> } }

// English text is the i18n key
const TYPE_LABEL: Record<string, string> = {
  mass: 'Mass', power_avg: 'Orbit-average power', power_peak: 'Peak power', power_mode: 'Power in a mode',
  data: 'Data volume', pointing: 'Pointing', registration: 'Registration', timing: 'Timing',
}
// English text is the i18n key
const STATUS_LABEL: Record<string, string> = { proposed: 'proposed', agreed: 'agreed', disputed: 'disputed' }
const KIND_FOR_BUDGET: Record<string, string[]> = {
  mass: ['mass'], power: ['power_avg', 'power_peak', 'power_mode'], data: ['data'],
  cost: [], performance: ['pointing', 'registration', 'timing'], all: ['mass', 'power_avg', 'power_peak', 'power_mode', 'data', 'pointing', 'registration', 'timing'],
}

async function send(url: string, method: string, body?: unknown): Promise<Response> {
  return fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) })
}

export function AllocationLedger({ studyId, budget = 'all' }: { studyId: string | null; budget?: string }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [previewId, setPreviewId] = useState<string | null>(null)
  const { data } = useQuery<Ledger>({
    queryKey: ['allocation-ledger', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/allocation-ledger`).then(r => r.json()),
    enabled: !!studyId, refetchInterval: 5000,
  })
  const refresh = () => qc.invalidateQueries({ queryKey: ['allocation-ledger', studyId] })
  const kinds = KIND_FOR_BUDGET[budget] ?? KIND_FOR_BUDGET.all
  const rows = (data?.items ?? []).filter(l => kinds.includes(l.budget_type))
  const lang = i18n.language === 'fr' ? 'fr' : 'en'

  async function act(fn: () => Promise<Response>) {
    setBusy(true); setError(null)
    try {
      const r = await fn()
      if (!r.ok && r.status !== 202) {
        const d = await r.json().catch(() => null)
        setError(typeof d?.detail === 'string' ? d.detail : d?.detail?.message ?? t('The change was refused ({{status}})', { status: r.status }))
      }
    } finally { setBusy(false); refresh() }
  }
  const agree = (l: LedgerLine) => act(() => send(`${API}/studies/${studyId}/allocation-ledger/${l.id}/agree`, 'POST', {}))
  const dispute = async (l: LedgerLine) => {
    const reason = await askText(t('Why do you dispute this allocation?'), '')
    if (reason) await act(() => send(`${API}/studies/${studyId}/allocation-ledger/${l.id}/dispute`, 'POST', { reason }))
  }
  const edit = async (l: LedgerLine) => {
    const v = await askText(t('New allocation ({{unit}})', { unit: l.unit }), l.value != null ? String(l.value) : '')
    if (v == null || v.trim() === '' || Number.isNaN(Number(v.replace(',', '.')))) return
    const why = await askText(t('Reason for the change'), '')
    await act(() => send(`${API}/studies/${studyId}/allocation-ledger/${l.id}`, 'PATCH', { value: Number(v.replace(',', '.')), why: why ?? '' }))
  }
  const propose = () => act(() => send(`${API}/studies/${studyId}/allocation-ledger/propose`, 'POST', {}))

  const status = (l: LedgerLine) => (
    <StatusBadge status={l.status === 'agreed' ? 'ok' : l.status === 'disputed' ? 'alarm' : 'caution'}>
      {t(STATUS_LABEL[l.status] ?? l.status)}
    </StatusBadge>
  )
  const columns: Column<LedgerLine>[] = [
    { key: 'el', header: t('Element'), render: l => <span className="mono">{l.element_code}</span>, sort: l => l.element_code },
    { key: 'type', header: t('Budget'), render: l => <>{t(TYPE_LABEL[l.budget_type] ?? l.budget_type)}{l.mode_key ? <span className="c-3"> · {l.mode_key}</span> : null}</>, sort: l => l.budget_type },
    { key: 'value', header: t('Allocation'), num: true, render: l => <><span className="mono">{fmtNum(l.value ?? 0, 3)}</span> {l.unit}</>, sort: l => l.value },
    { key: 'cbe', header: t('Current estimate'), num: true, render: l => l.margined != null ? <span className="mono">{fmtNum(l.margined, 3)}</span> : (l.cbe != null ? <span className="mono">{fmtNum(l.cbe, 3)}</span> : <span className="c-3">{t('none')}</span>) },
    { key: 'req', header: t('Requirement'), render: l => (
      <>
        <span className="mono">{l.requirement_code || '—'}</span>
        {l.data_json?.requirement_sync?.status === 'stale' && <StatusBadge status="stale">{t('requirement to update')}</StatusBadge>}
      </>) },
    { key: 'owner', header: t('Owner'), render: l => seatLabel(l.owner_seat, lang), sort: l => l.owner_seat },
    { key: 'status', header: t('State'), render: l => (
      <span title={l.data_json?.dispute ? `${l.data_json.dispute.by}: ${l.data_json.dispute.reason}` : l.agreed_by || undefined}>{status(l)}</span>
    ), sort: l => l.status },
    { key: 'v', header: t('Version'), num: true, render: l => <span className="mono">{l.version}</span> },
    { key: 'act', header: t('Actions'), render: l => (
      <span className="row gap-1">
        {l.status !== 'agreed' && <Button size="sm" onClick={() => agree(l)} busy={busy}>{t('Agree')}</Button>}
        {l.status !== 'disputed' && <Button size="sm" variant="quiet" onClick={() => dispute(l)} busy={busy}>{t('Dispute')}</Button>}
        <Button size="sm" variant="quiet" onClick={() => edit(l)} busy={busy}>{t('Edit')}</Button>
        {l.status !== 'agreed' && (l.budget_type === 'mass' || l.budget_type === 'power_avg') && l.element_id && l.value != null &&
          <Button size="sm" variant="quiet" aria-pressed={previewId === l.id}
            onClick={() => setPreviewId(previewId === l.id ? null : l.id)}>{t('Who is affected')}</Button>}
      </span>) },
  ]
  // wave 3 (3.L6): the proposed allocation against the element's rolled-up value (dry run)
  const previewLine = rows.find(r => r.id === previewId) ?? null
  const closures = Object.entries(data?.closure ?? {}).filter(([k]) => kinds.includes(k))
  const agreed = rows.filter(r => r.status === 'agreed').length

  return (
    <Panel title={t('Allocation ledger')} id="allocation-ledger"
      meta={t('{{agreed}}/{{n}} agreed by their owners', { agreed, n: rows.length })}
      actions={<Button size="sm" onClick={propose} busy={busy} title={t('Proposes a mass and a power line per subsystem from the roll-up')}>{t('Propose from the roll-up')}</Button>}>
      {closures.map(([k, c]) => (
        <p key={k} className="t-12 c-2 m-0" data-testid={`ledger-closure-${k}`}>
          {t('{{kind}}: allocations {{sum}} {{unit}}, with the {{pct}} % system margin {{with}} {{unit}}, limit {{limit}} {{unit}}; Systems reserve {{reserve}} {{unit}}.', {
            kind: t(TYPE_LABEL[k] ?? k), sum: fmtNum(c.sum, 3), unit: c.unit, pct: c.system_margin_percent,
            with: fmtNum(c.with_system_margin, 3), limit: c.limit != null ? fmtNum(c.limit, 3) : t('none'),
            reserve: c.reserve != null ? fmtNum(c.reserve, 3) : t('none') })}{' '}
          {c.closes === false && <StatusBadge status="alarm">{t('does not close')}</StatusBadge>}
        </p>
      ))}
      {error && <Note tone="caution" role="alert">{error}</Note>}
      <DataTable columns={columns} rows={rows} rowKey={l => l.id} dense caption={t('Allocation ledger')}
        empty={<span className="c-3">{t('No allocation yet. Propose the lines from the roll-up, then each owner seat agrees its line.')}</span>} />
      {previewLine && (
        <ImpactPreview studyId={studyId} compact change={{ kind: 'allocation', element_id: previewLine.element_id,
          resource: previewLine.budget_type === 'mass' ? 'mass' : 'power', value: previewLine.value }} />
      )}
    </Panel>
  )
}
