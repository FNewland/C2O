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

const API = '/api'

const inputStyle: React.CSSProperties = {
  padding: '0.15rem 0.35rem', fontSize: '0.66rem', borderRadius: '3px',
  background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)',
}
const smallBtn = (color = 'var(--text-secondary)'): React.CSSProperties => ({
  background: 'none', border: '1px solid var(--border)', borderRadius: '3px', cursor: 'pointer',
  fontSize: '0.62rem', padding: '0.1rem 0.35rem', color,
})
const th: React.CSSProperties = { textAlign: 'left', padding: '0.25rem 0.4rem', fontSize: '0.62rem', color: 'var(--text-secondary)', borderBottom: '1px solid var(--border)', whiteSpace: 'nowrap' }
const td: React.CSSProperties = { padding: '0.2rem 0.4rem', fontSize: '0.68rem', borderBottom: '1px solid var(--border)', verticalAlign: 'top' }

const TYPE_COLORS: Record<string, string> = {
  electrical: '#f59e0b', data: '#8b5cf6', rf: '#ec4899', mechanical: '#84cc16', thermal: '#ef4444',
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
    return <div style={{ padding: '1rem', color: 'var(--text-secondary)', fontSize: '0.78rem' }}>{t('Create or join a study to see the ICD.')}</div>
  }

  const nInterfaces = new Set(rows.map(r => r.interface_id)).size
  const nItems = rows.filter(r => r.exchange_item).length

  return (
    <div style={{ padding: '0.5rem 1rem', fontSize: '0.75rem', overflow: 'auto', height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <span style={{ fontWeight: 600, fontSize: '0.78rem' }}>{t('Interface Control Document')}</span>
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.65rem' }}>{t('{{interfaces}} interfaces · {{items}} exchange items · {{defined}} defined', { interfaces: nInterfaces, items: nItems, defined: items.length })}</span>
        <span style={{ flex: 1 }} />
        <a href={`${API}/studies/${studyId}/icd.csv`} download={`icd_${studyId}.csv`}
          style={{ ...smallBtn('#10b981'), textDecoration: 'none' }}>{t('Download CSV')}</a>
      </div>
      {error && (
        <div style={{ color: '#ef4444', fontSize: '0.68rem', marginBottom: '0.4rem' }}>
          {error} <button style={smallBtn('#ef4444')} onClick={() => setError(null)}>{t('dismiss')}</button>
        </div>
      )}
      {isLoading && <div style={{ color: 'var(--text-secondary)' }}>{t('Loading…')}</div>}
      {!isLoading && rows.length === 0 && (
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.7rem' }}>{t('No interfaces yet. Define interfaces between elements first; each one then appears here for exchange items.')}</div>
      )}
      {rows.length > 0 && (
        <table style={{ borderCollapse: 'collapse', width: '100%' }}>
          <thead>
            <tr>
              <th style={th}>{t('Interface')}</th><th style={th}>{t('From')}</th><th style={th}>{t('To')}</th><th style={th}>{t('Type')}</th>
              <th style={th}>{t('Exchange item')}</th><th style={th}>{t('Kind')}</th><th style={th}>{t('Key properties')}</th><th style={th}></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => {
              const xi = r.exchange_item
              const firstOfIface = i === 0 || rows[i - 1].interface_id !== r.interface_id
              const color = TYPE_COLORS[r.interface_type || ''] || '#6b7280'
              const isEditing = xi && editItem === xi.id
              return (
                <tr key={`${r.interface_id}-${xi?.id || 'none'}`}>
                  <td style={{ ...td, fontWeight: firstOfIface ? 600 : 400, color: firstOfIface ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                    {firstOfIface ? r.name || r.interface_id.slice(0, 8) : '〃'}
                  </td>
                  <td style={td}>{r.from_element.name || '—'}</td>
                  <td style={td}>{r.to_element.name || '—'}</td>
                  <td style={td}><span style={{ color, fontSize: '0.62rem' }}>{r.interface_type || '—'}{r.direction ? ` · ${r.direction}` : ''}</span></td>
                  {isEditing ? (
                    <>
                      <td style={td}><input value={editName} onChange={e => setEditName(e.target.value)} style={inputStyle} /></td>
                      <td style={td}>
                        <select value={editKind} onChange={e => setEditKind(e.target.value)} style={inputStyle}>
                          {EXCHANGE_ITEM_KINDS.map(k => <option key={k} value={k}>{k}</option>)}
                        </select>
                      </td>
                      <td style={td}><input value={editProps} onChange={e => setEditProps(e.target.value)} placeholder="rate_hz=10; bits=16" style={{ ...inputStyle, width: '100%' }} /></td>
                      <td style={{ ...td, whiteSpace: 'nowrap' }}>
                        <button style={smallBtn('#10b981')} onClick={() => updateItem.mutate({ id: xi!.id, name: editName, kind: editKind, props: editProps })}>{t('save')}</button>{' '}
                        <button style={smallBtn()} onClick={() => setEditItem(null)}>{t('cancel')}</button>
                      </td>
                    </>
                  ) : (
                    <>
                      <td style={td}>{xi ? xi.name : <span style={{ color: '#f59e0b', fontSize: '0.62rem' }}>{t('no exchange item')}</span>}</td>
                      <td style={td}>{xi?.kind || ''}</td>
                      <td style={{ ...td, color: 'var(--text-secondary)', fontSize: '0.62rem' }}>{xi ? propsToText(xi.properties) : propsToText(r.interface_properties)}</td>
                      <td style={{ ...td, whiteSpace: 'nowrap' }}>
                        {xi && <>
                          <button style={smallBtn()} onClick={() => { setEditItem(xi.id); setEditName(xi.name || ''); setEditKind(xi.kind || 'data'); setEditProps(propsToText(xi.properties)) }}>{t('edit')}</button>{' '}
                          <button style={smallBtn()} title={t('Detach from this interface')} onClick={() => detach.mutate({ ifaceId: r.interface_id, itemId: xi.id })}>{t('detach')}</button>{' '}
                          <button style={smallBtn('#ef4444')} title={t('Delete exchange item')} onClick={() => { if (confirm(t('Delete exchange item "{{name}}"?', { name: xi.name }))) deleteItem.mutate(xi.id) }}>×</button>{' '}
                        </>}
                        {firstOfIface && <button style={smallBtn('#3b82f6')} onClick={() => setAttachFor(attachFor === r.interface_id ? null : r.interface_id)}>{t('+ item')}</button>}
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
                  <td colSpan={8} style={{ ...td, background: 'var(--bg-card)' }}>
                    <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '0.62rem', color: 'var(--text-secondary)' }}>{t('New item:')}</span>
                      <input value={newName} onChange={e => setNewName(e.target.value)} placeholder={t('name')} style={inputStyle} />
                      <select value={newKind} onChange={e => setNewKind(e.target.value)} style={inputStyle}>
                        {EXCHANGE_ITEM_KINDS.map(k => <option key={k} value={k}>{k}</option>)}
                      </select>
                      <input value={newProps} onChange={e => setNewProps(e.target.value)} placeholder={t('props: rate_hz=10; protocol=CAN')} style={{ ...inputStyle, minWidth: 200 }} />
                      <button style={smallBtn('#10b981')} disabled={!newName.trim() || createAndAttach.isPending}
                        onClick={() => createAndAttach.mutate({ ifaceId: r.interface_id, name: newName.trim(), kind: newKind, props: newProps })}>{t('create & attach')}</button>
                      {available.length > 0 && <>
                        <span style={{ fontSize: '0.62rem', color: 'var(--text-secondary)', marginLeft: '0.5rem' }}>{t('or existing:')}</span>
                        <select value={attachExisting} onChange={e => setAttachExisting(e.target.value)} style={inputStyle}>
                          <option value="">{t('select…')}</option>
                          {available.map(it => <option key={it.id} value={it.id}>{it.name} ({it.kind})</option>)}
                        </select>
                        <button style={smallBtn('#3b82f6')} disabled={!attachExisting}
                          onClick={() => attach.mutate({ ifaceId: r.interface_id, itemId: attachExisting })}>{t('attach')}</button>
                      </>}
                      <button style={smallBtn()} onClick={() => setAttachFor(null)}>{t('cancel')}</button>
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
