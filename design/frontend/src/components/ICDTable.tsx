/**
 * ICDTable — Interface Control Document view (SCDF-160).
 *
 * One row per interface × exchange item from GET /api/studies/{id}/icd.
 * Inline: create an exchange item and attach it to an interface, edit item
 * name/kind/properties, detach, download CSV.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { useDesignStore } from '../stores/designStore'
import { EXCHANGE_ITEM_KINDS, type ExchangeItem, type ICDRow } from '../types/arcadia'
import { fs } from '../theme/tokens'
import { askConfirm } from './ui/Dialog'

const API = '/api'


const TYPE_COLORS: Record<string, string> = {
  electrical: 'var(--cat-4)', data: 'var(--cat-2)', rf: 'var(--cat-6)', mechanical: 'var(--cat-8)', thermal: 'var(--cat-5)',
}

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

  const { data: rows = [], isLoading } = useQuery<ICDRow[]>({
    queryKey: ['icd', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/icd`).then(jsonOrThrow),
    enabled: !!studyId, structuralSharing: false,
  })
  const { data: items = [] } = useQuery<ExchangeItem[]>({
    queryKey: ['exchange-items', studyId],
    queryFn: () => fetch(`${API}/studies/${studyId}/exchange-items`).then(jsonOrThrow),
    enabled: !!studyId, structuralSharing: false,
  })

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
      {isLoading && <div className="c-2">{t('Loading…')}</div>}
      {!isLoading && rows.length === 0 && (
        <div className="c-2 t-12">{t('No interfaces yet. Define interfaces between elements first; each one then appears here for exchange items.')}</div>
      )}
      {rows.length > 0 && (
        <table className="c2o-table c2o-table--dense">
          <thead>
            <tr>
              <th>{t('Interface')}</th><th>{t('From')}</th><th>{t('To')}</th><th>{t('Type')}</th>
              <th>{t('Exchange item')}</th><th>{t('Kind')}</th><th>{t('Key properties')}</th><th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => {
              const xi = r.exchange_item
              const firstOfIface = i === 0 || rows[i - 1].interface_id !== r.interface_id
              const color = TYPE_COLORS[r.interface_type || ''] || 'var(--text-3)'
              const isEditing = xi && editItem === xi.id
              return (
                <tr key={`${r.interface_id}-${xi?.id || 'none'}`}>
                  <td style={{ fontWeight: firstOfIface ? 600 : 400, color: firstOfIface ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                    {firstOfIface ? r.name || r.interface_id.slice(0, 8) : '〃'}
                  </td>
                  <td>{r.from_element.name || '—'}</td>
                  <td>{r.to_element.name || '—'}</td>
                  <td><span style={{ color, fontSize: fs.label }}>{r.interface_type || '—'}{r.direction ? ` · ${r.direction}` : ''}</span></td>
                  {isEditing ? (
                    <>
                      <td><input value={editName} onChange={e => setEditName(e.target.value)} className="c2o-input c2o-input--sm" /></td>
                      <td>
                        <select value={editKind} onChange={e => setEditKind(e.target.value)} className="c2o-select c2o-select--sm">
                          {EXCHANGE_ITEM_KINDS.map(k => <option key={k} value={k}>{k}</option>)}
                        </select>
                      </td>
                      <td><input value={editProps} onChange={e => setEditProps(e.target.value)} placeholder="rate_hz=10; bits=16" className="c2o-input c2o-input--sm w-full" /></td>
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
                  <td colSpan={8} className="bg-2">
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

export default ICDTable
