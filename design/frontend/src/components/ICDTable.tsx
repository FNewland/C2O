/**
 * ICDTable — Interface Control Document view (SCDF-160).
 *
 * One row per interface × exchange item from GET /api/studies/{id}/icd.
 * Inline: create an exchange item and attach it to an interface, edit item
 * name/kind/properties, detach, download CSV.
 * W2.07: the "Requirements" column lists the interface requirement codes of each row (those
 * that name the interface or the exchange item, and the boundary rows that cover the link).
 * Wave 3 (3.R5, 3.R6): "ICD documents under issue control" above the table: each ICD the
 * requirements cite, its issue (draft, A, B …, baselined) and the sign-off of its provider and
 * consumer seats (Agree per side); the team puts ICDs under control (the PDR inventory), raises
 * the next issue and baselines a signed one. PDR-EC-02 reads the same state.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { useDesignStore } from '../stores/designStore'
import { EXCHANGE_ITEM_KINDS, type ExchangeItem, type ICDRow } from '../types/arcadia'
import { askConfirm } from './ui/Dialog'
import { canonicalType } from '../types/interfaces'
import { LinkStatusChip, TypeLabel } from '../workbench/linkParts'

const API = '/api'


async function jsonOrThrow(res: Response) {
  if (!res.ok) {
    let msg = `${res.status}`
    try { const b = await res.json(); msg = typeof b.detail === 'string' ? b.detail : JSON.stringify(b.detail ?? b) } catch { /* noop */ }
    throw new Error(msg)
  }
  return res.status === 204 ? null : res.json()
}

function propsToText(p: Record<string, unknown>): string {
  return Object.entries(p || {}).map(([k, v]) => `${k}=${typeof v === 'object' ? JSON.stringify(v) : String(v)}`).join('; ')
}
function textToProps(s: string): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  for (const part of s.split(';')) {
    const i = part.indexOf('=')
    if (i < 0) continue
    const k = part.slice(0, i).trim(); const raw = part.slice(i + 1).trim()
    if (!k) continue
    const n = Number(raw)
    out[k] = raw !== '' && !Number.isNaN(n) ? n : raw
  }
  return out
}

export function ICDTable({ studyId: studyIdProp }: { studyId?: string | null }) {
  const { t } = useTranslation()
  const uiStudyId = useUIStore(s => s.studyId)
  const designStudyId = useDesignStore(s => s.studyId)
  const studyId = studyIdProp ?? uiStudyId ?? designStudyId
  const qc = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const [attachFor, setAttachFor] = useState<string | null>(null)   // interface_id being edited
  const [attachExisting, setAttachExisting] = useState('')
  const [newName, setNewName] = useState('')
  const [newKind, setNewKind] = useState('data')
  const [newProps, setNewProps] = useState('')
  const [editItem, setEditItem] = useState<string | null>(null)
  const [editName, setEditName] = useState('')
  const [editKind, setEditKind] = useState('data')
  const [editProps, setEditProps] = useState('')

  // Rejected links are excluded from analyses and from the ICD (interface contract).
  const { data: rows = [], isLoading } = useQuery<ICDRow[]>({
    queryKey: ['icd', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/icd`).then(jsonOrThrow)
      .then((rs: ICDRow[]) => (Array.isArray(rs) ? rs.filter(r => r.status !== 'rejected') : [])),
    enabled: !!studyId, structuralSharing: false,
  })
  const { data: items = [] } = useQuery<ExchangeItem[]>({
    queryKey: ['exchange-items', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/exchange-items`).then(jsonOrThrow),
    enabled: !!studyId, structuralSharing: false,
  })

  const { data: reqs = [] } = useQuery<any[]>({
    queryKey: ['requirements', studyId],
    queryFn: () => fetch(`${API}/requirements/tree?study_id=${studyId}`).then(jsonOrThrow),
    enabled: !!studyId, structuralSharing: false,
  })
  const irCodes = (ifaceId: string, itemId?: string) => reqs
    .filter(r => r.level === 'interface' && r.status !== 'retired')
    .filter(r => {
      const ir = r.ir_json || {}
      if (itemId && (ir.exchange_item_ids || []).includes(itemId)) return true
      return ir.interface_id === ifaceId || (ir.interface_ids || []).includes(ifaceId) || (ir.covers_interface_ids || []).includes(ifaceId)
    })
    .map(r => r.code as string).sort()

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['icd', studyId] })
    qc.invalidateQueries({ queryKey: ['exchange-items', studyId] })
    qc.invalidateQueries({ queryKey: ['interfaces', studyId] })
  }
  const onErr = (e: Error) => setError(e.message)

  const idsForInterface = (ifaceId: string) =>
    rows.filter(r => r.interface_id === ifaceId && r.exchange_item).map(r => r.exchange_item!.id)

  const setInterfaceItems = async (ifaceId: string, ids: string[]) =>
    fetch(`${API}/interfaces/${ifaceId}/exchange-items`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ exchange_item_ids: ids }),
    }).then(jsonOrThrow)

  const createAndAttach = useMutation({
    mutationFn: async ({ ifaceId, name, kind, props }: { ifaceId: string; name: string; kind: string; props: string }) => {
      const item = await fetch(`${API}/exchange-items/?study_id=${studyId}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, kind, properties: textToProps(props) }),
      }).then(jsonOrThrow)
      await setInterfaceItems(ifaceId, [...idsForInterface(ifaceId), item.id])
    },
    onSuccess: () => { invalidate(); setAttachFor(null); setNewName(''); setNewProps('') }, onError: onErr,
  })
  const attach = useMutation({
    mutationFn: ({ ifaceId, itemId }: { ifaceId: string; itemId: string }) =>
      setInterfaceItems(ifaceId, [...new Set([...idsForInterface(ifaceId), itemId])]),
    onSuccess: () => { invalidate(); setAttachFor(null); setAttachExisting('') }, onError: onErr,
  })
  const detach = useMutation({
    mutationFn: ({ ifaceId, itemId }: { ifaceId: string; itemId: string }) =>
      setInterfaceItems(ifaceId, idsForInterface(ifaceId).filter(i => i !== itemId)),
    onSuccess: invalidate, onError: onErr,
  })
  const updateItem = useMutation({
    mutationFn: ({ id, name, kind, props }: { id: string; name: string; kind: string; props: string }) =>
      fetch(`${API}/exchange-items/${id}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, kind, properties: textToProps(props) }),
      }).then(jsonOrThrow),
    onSuccess: () => { invalidate(); setEditItem(null) }, onError: onErr,
  })
  const deleteItem = useMutation({
    mutationFn: (id: string) => fetch(`${API}/exchange-items/${id}`, { method: 'DELETE' }).then(jsonOrThrow),
    onSuccess: invalidate, onError: onErr,
  })

  if (!studyId) {
    return <div className="p-4 c-2 t-12">{t('Create or join a study to see the ICD.')}</div>
  }

  const nInterfaces = new Set(rows.map(r => r.interface_id)).size
  const nItems = rows.filter(r => r.exchange_item).length

  return (
    <div className="c2o-pane">
      <div className="flex ai-c gap-2 mb-2">
        <span className="w-600 t-12">{t('Interface Control Document')}</span>
        <span className="c-2 t-12">{t('{{interfaces}} interfaces · {{items}} exchange items · {{defined}} defined', { interfaces: nInterfaces, items: nItems, defined: items.length })}</span>
        <span className="grow" />
        <a href={`${API}/studies/${studyId}/icd.csv`} download={`icd_${studyId}.csv`}
          className="c2o-btn c2o-btn--sm" style={{ textDecoration: 'none' }}>{t('Download CSV')}</a>
      </div>
      {error && (
        <div className="c-alarm t-12 mb-2">
          {error} <button className="c2o-btn c2o-btn--sm" onClick={() => setError(null)}>{t('dismiss')}</button>
        </div>
      )}
      <IcdIssues studyId={studyId} onError={setError} />
      {isLoading && <div className="c-2">{t('Loading…')}</div>}
      {!isLoading && rows.length === 0 && (
        <div className="c-2 t-12">{t('No interfaces yet. Define interfaces between elements first; each one then appears here for exchange items.')}</div>
      )}
      {rows.length > 0 && (
        <table className="c2o-table c2o-table--dense">
          <thead>
            <tr>
              <th>{t('Interface')}</th><th>{t('From')}</th><th>{t('To')}</th><th>{t('Type')}</th>
              <th>{t('Exchange item')}</th><th>{t('Kind')}</th><th>{t('Key properties')}</th><th>{t('Requirements')}</th><th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => {
              const xi = r.exchange_item
              const firstOfIface = i === 0 || rows[i - 1].interface_id !== r.interface_id
              const ctype = canonicalType(r.type ?? r.interface_type)
              const suggested = r.status === 'suggested'
              const isEditing = xi && editItem === xi.id
              return (
                <tr key={`${r.interface_id}-${xi?.id || 'none'}`}>
                  <td style={{ fontWeight: firstOfIface ? 600 : 400, color: firstOfIface ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                    {firstOfIface ? r.name || r.interface_id.slice(0, 8) : '〃'}
                  </td>
                  <td>{r.from_element.name || '—'}</td>
                  <td>{r.to_element.name || '—'}</td>
                  <td><span className="row gap-2 wrap">
                    <TypeLabel type={ctype} short />
                    {suggested && firstOfIface && <LinkStatusChip status="suggested" />}
                  </span></td>
                  {isEditing ? (
                    <>
                      <td><input value={editName} onChange={e => setEditName(e.target.value)} className="c2o-input c2o-input--sm" /></td>
                      <td>
                        <select value={editKind} onChange={e => setEditKind(e.target.value)} className="c2o-select c2o-select--sm">
                          {EXCHANGE_ITEM_KINDS.map(k => <option key={k} value={k}>{k}</option>)}
                        </select>
                      </td>
                      <td><input value={editProps} onChange={e => setEditProps(e.target.value)} placeholder="rate_hz=10; bits=16" className="c2o-input c2o-input--sm w-full" /></td>
                      <td className="mono t-12">{irCodes(r.interface_id, xi?.id).join(', ') || '—'}</td>
                      <td className="nowrap">
                        <button className="c2o-btn c2o-btn--sm" onClick={() => updateItem.mutate({ id: xi!.id, name: editName, kind: editKind, props: editProps })}>{t('save')}</button>{' '}
                        <button className="c2o-btn c2o-btn--sm" onClick={() => setEditItem(null)}>{t('cancel')}</button>
                      </td>
                    </>
                  ) : (
                    <>
                      <td>{xi ? xi.name : <span className="c-caution t-12">{t('no exchange item')}</span>}</td>
                      <td>{xi?.kind || ''}</td>
                      <td className="c-2 t-12">{xi ? propsToText(xi.properties) : propsToText(r.interface_properties)}</td>
                      <td className="mono t-12">{irCodes(r.interface_id, xi?.id).join(', ') || '—'}</td>
                      <td className="nowrap">
                        {xi && <>
                          <button className="c2o-btn c2o-btn--sm" onClick={() => { setEditItem(xi.id); setEditName(xi.name || ''); setEditKind(xi.kind || 'data'); setEditProps(propsToText(xi.properties)) }}>{t('edit')}</button>{' '}
                          <button className="c2o-btn c2o-btn--sm" title={t('Detach from this interface')} onClick={() => detach.mutate({ ifaceId: r.interface_id, itemId: xi.id })}>{t('detach')}</button>{' '}
                          <button className="c2o-btn c2o-btn--sm" title={t('Delete exchange item')} onClick={async () => { if ((await askConfirm(t('Delete exchange item "{{name}}"?', { name: xi.name })))) deleteItem.mutate(xi.id) }}>×</button>{' '}
                        </>}
                        {firstOfIface && <button className="c2o-btn c2o-btn--sm" onClick={() => setAttachFor(attachFor === r.interface_id ? null : r.interface_id)}>{t('+ item')}</button>}
                      </td>
                    </>
                  )}
                </tr>
              )
            }).flatMap((row, i) => {
              const r = rows[i]
              const firstOfIface = i === 0 || rows[i - 1].interface_id !== r.interface_id
              if (!(firstOfIface && attachFor === r.interface_id)) return [row]
              const attached = new Set(idsForInterface(r.interface_id))
              const available = items.filter(it => !attached.has(it.id))
              return [row, (
                <tr key={`attach-${r.interface_id}`}>
                  <td colSpan={9} className="bg-2">
                    <div className="flex gap-2 ai-c wrap">
                      <span className="t-12 c-2">{t('New item:')}</span>
                      <input value={newName} onChange={e => setNewName(e.target.value)} placeholder={t('name')} className="c2o-input c2o-input--sm" />
                      <select value={newKind} onChange={e => setNewKind(e.target.value)} className="c2o-select c2o-select--sm">
                        {EXCHANGE_ITEM_KINDS.map(k => <option key={k} value={k}>{k}</option>)}
                      </select>
                      <input value={newProps} onChange={e => setNewProps(e.target.value)} placeholder={t('props: rate_hz=10; protocol=CAN')} className="c2o-input c2o-input--sm" style={{ minWidth: 200 }} />
                      <button className="c2o-btn c2o-btn--sm" disabled={!newName.trim() || createAndAttach.isPending}
                        onClick={() => createAndAttach.mutate({ ifaceId: r.interface_id, name: newName.trim(), kind: newKind, props: newProps })}>{t('create & attach')}</button>
                      {available.length > 0 && <>
                        <span className="t-12 c-2 ml-2">{t('or existing:')}</span>
                        <select value={attachExisting} onChange={e => setAttachExisting(e.target.value)} className="c2o-select c2o-select--sm">
                          <option value="">{t('select…')}</option>
                          {available.map(it => <option key={it.id} value={it.id}>{it.name} ({it.kind})</option>)}
                        </select>
                        <button className="c2o-btn c2o-btn--sm" disabled={!attachExisting}
                          onClick={() => attach.mutate({ ifaceId: r.interface_id, itemId: attachExisting })}>{t('attach')}</button>
                      </>}
                      <button className="c2o-btn c2o-btn--sm" onClick={() => setAttachFor(null)}>{t('cancel')}</button>
                    </div>
                  </td>
                </tr>
              )]
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}

// ─── wave 3: ICD issue control ───

interface IcdItem {
  icd_ref: string; title: string; refs: string[]; codes: string[]; controlled: boolean; issue: string | null
  revision: number | null; state: string; provider_seat: string | null; consumer_seat: string | null
  signed?: string[]; unsigned?: string[]; agreed: boolean; stale: boolean; history: number; required_at?: string | null
}

// English text is the i18n key
const ICD_STATE_LABEL: Record<string, string> = {
  none: 'not under issue control', draft: 'draft', issue_a: 'Issue A', issue_b: 'Issue B or later',
  baselined: 'baselined', superseded: 'superseded',
}

export function IcdIssues({ studyId, onError }: { studyId: string; onError: (m: string) => void }) {
  const { t, i18n } = useTranslation()
  const qc = useQueryClient()
  const [pick, setPick] = useState('')
  const [open, setOpen] = useState<string | null>(null)
  const fr = i18n.language.startsWith('fr')
  const { data } = useQuery<{ items: IcdItem[]; counts: Record<string, number>; unsigned_by_seat: Record<string, string[]> }>({
    queryKey: ['icds', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/icds`).then(jsonOrThrow),
    enabled: !!studyId, structuralSharing: false,
  })
  const { data: seats } = useQuery<any>({
    queryKey: ['seat-catalogue'],
    queryFn: () => fetch(`${API}/seats/catalogue`).then(r => (r.ok ? r.json() : { seats: [] })),
    staleTime: Infinity,
  })
  const { data: hist } = useQuery<any>({
    queryKey: ['icd-history', studyId, open],
    queryFn: () => fetch(`${API}/studies/${studyId}/icds/${encodeURIComponent(open!)}/history`).then(jsonOrThrow),
    enabled: !!open,
  })
  const seatLabel = (id?: string | null) => {
    const s = (seats?.seats ?? []).find((x: any) => x.id === id)
    return s ? (fr ? s.label.fr : s.label.en) : (id ?? '')
  }
  const post = async (url: string, body: unknown) => {
    try {
      await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(jsonOrThrow)
      qc.invalidateQueries({ queryKey: ['icds', studyId] })
      qc.invalidateQueries({ queryKey: ['icd-history', studyId] })
    } catch (e: any) { onError(e.message) }
  }
  const items = data?.items ?? []
  const controlled = items.filter(i => i.controlled)
  const free = items.filter(i => !i.controlled)
  const issued = (i: IcdItem) => ['issue_a', 'issue_b', 'baselined'].includes(i.state)
  return (
    <section className="card mb-2" aria-label={t('ICD documents under issue control')}>
      <div className="flex ai-c gap-2 wrap mb-1">
        <span className="w-600 t-12">{t('ICD documents under issue control')}</span>
        {data && <span className="t-12 c-2">{t('{{agreed}}/{{n}} agreed by both seats · {{issued}} at Issue A or later',
          { agreed: data.counts.agreed ?? 0, n: data.counts.controlled ?? 0, issued: data.counts.at_issue_a ?? 0 })}</span>}
        <span className="grow" />
        <select className="c2o-select c2o-select--sm" value={pick} onChange={e => setPick(e.target.value)} aria-label={t('ICD to put under issue control')}>
          <option value="">{t('Put an ICD under issue control…')}</option>
          {free.map(i => <option key={i.icd_ref} value={i.icd_ref}>{i.icd_ref} ({i.codes.join(', ')})</option>)}
        </select>
        <button className="c2o-btn c2o-btn--sm" disabled={!pick}
          onClick={() => { void post(`${API}/studies/${studyId}/icds/inventory`, { icd_refs: [pick], required_at: 'pdr' }); setPick('') }}>
          {t('Add to the PDR inventory')}</button>
      </div>
      {controlled.length === 0
        ? <p className="t-12 c-2 m-0">{t('No ICD under issue control yet. Put the ICDs the PDR needs under control, raise Issue A and have both owning seats sign it.')}</p>
        : (
          <table className="c2o-table t-12" style={{ width: '100%' }}>
            <thead><tr>
              <th>{t('ICD')}</th><th>{t('Requirements')}</th><th>{t('Issue')}</th><th>{t('Provider')}</th>
              <th>{t('Consumer')}</th><th>{t('State')}</th><th />
            </tr></thead>
            <tbody>
              {controlled.map(i => {
                const side = (which: 'provider' | 'consumer') => {
                  const seat = which === 'provider' ? i.provider_seat : i.consumer_seat
                  const ok = (i.signed ?? []).includes(seat ?? '')
                  return (
                    <span className="row gap-1 ai-c">
                      <span className={ok ? 'c-ok' : 'c-2'}>{ok ? '✓ ' : ''}{seatLabel(seat)}</span>
                      {issued(i) && <button className="c2o-btn c2o-btn--sm"
                        onClick={() => void post(`${API}/studies/${studyId}/icds/${encodeURIComponent(i.icd_ref)}/signoff`, { side: which, agree: !ok })}>
                        {ok ? t('Withdraw') : t('Agree')}</button>}
                    </span>)
                }
                return [
                  <tr key={i.icd_ref}>
                    <td className="mono">{i.icd_ref}<div className="c-2">{i.title}</div></td>
                    <td className="mono">{i.codes.join(', ')}</td>
                    <td className="mono">{i.issue ? `${i.issue}${i.revision ? `.${i.revision}` : ''}` : t('draft')}</td>
                    <td>{side('provider')}</td>
                    <td>{side('consumer')}</td>
                    <td>
                      <span className={i.agreed ? 'c-ok' : i.stale ? 'c-caution' : 'c-2'}>
                        {t(ICD_STATE_LABEL[i.state] ?? i.state)}{i.agreed ? ` · ${t('agreed')}` : ''}
                        {i.stale ? ` · ${t('changed since signed')}` : ''}</span>
                    </td>
                    <td className="row gap-1">
                      <button className="c2o-btn c2o-btn--sm"
                        onClick={() => void post(`${API}/studies/${studyId}/icds/${encodeURIComponent(i.icd_ref)}/issue`, {})}>
                        {i.issue ? t('Raise the next issue') : t('Raise Issue A')}</button>
                      {i.agreed && i.state !== 'baselined' && <button className="c2o-btn c2o-btn--sm"
                        onClick={() => void post(`${API}/studies/${studyId}/icds/${encodeURIComponent(i.icd_ref)}/issue`, { baseline: true })}>
                        {t('Baseline')}</button>}
                      <button className="c2o-btn c2o-btn--sm" onClick={() => setOpen(open === i.icd_ref ? null : i.icd_ref)}>
                        {t('History ({{n}})', { n: i.history })}</button>
                    </td>
                  </tr>,
                  open === i.icd_ref && (
                    <tr key={`${i.icd_ref}-h`}><td colSpan={7}>
                      <ul className="m-0 t-12">
                        {(hist?.items ?? []).map((h: any) => (
                          <li key={h.id}><span className="mono">{h.issue || t('draft')}{h.revision ? `.${h.revision}` : ''}</span>
                            {' · '}{t(ICD_STATE_LABEL[h.state] ?? h.state)}
                            {Object.keys(h.signoffs || {}).length > 0 && ` · ${t('signed by {{seats}}', { seats: Object.keys(h.signoffs).map(seatLabel).join(', ') })}`}
                            {h.change_note ? ` · ${h.change_note}` : ''}</li>))}
                      </ul>
                    </td></tr>),
                ]
              })}
            </tbody>
          </table>)}
    </section>
  )
}

export default ICDTable
