/**
 * ExchangePanel — model exchange (SCDF-160).
 *
 * Downloads: Capella (.zip), ECSS-E-TM-10-25 (.zip), ReqIF, SysML v2 text,
 * legacy MBSE JSON. Imports: Capella zip and ReqIF (multipart field `file`).
 * "Push to COMET" surfaces the server's 501 message when not configured.
 */
import { useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { ImportResult } from '../types/arcadia'

const API = '/api'

const btn = (color: string): React.CSSProperties => ({
  padding: '0.25rem 0.6rem', fontSize: '0.68rem', fontWeight: 600, borderRadius: '4px', cursor: 'pointer',
  background: `${color}20`, color, border: `1px solid ${color}60`, whiteSpace: 'nowrap',
})

interface Fmt { id: string; label: string; ext: string; path: string; color: string; blurb: string }

const EXPORTS: Fmt[] = [
  { id: 'capella', label: 'Capella', ext: 'zip', path: 'export/capella.zip', color: '#3b82f6',
    blurb: 'Arcadia model (.aird/.capella + property values). Open in Capella 7.x; round-trips through the Capella import below.' },
  { id: 'ecss', label: 'ECSS-E-TM-10-25', ext: 'zip', path: 'export/ecss-10-25.zip', color: '#8b5cf6',
    blurb: 'Annex A JSON (engineering model, iterations, parameters). Consumed by ESA CDF tools, COMET / CDP4 and other Annex A readers.' },
  { id: 'reqif', label: 'ReqIF', ext: 'reqif', path: 'export/requirements.reqif', color: '#10b981',
    blurb: 'Requirements Interchange Format (OMG). Import into IBM DOORS / DOORS Next, Polarion, Jama, Codebeamer.' },
  { id: 'sysml', label: 'SysML v2', ext: 'sysml', path: 'export/model.sysml', color: '#f59e0b',
    blurb: 'KerML/SysML v2 textual notation: parts, ports, connections, requirements. For SysML v2 pilot tools, Syside, Cameo 2024+.' },
  { id: 'mbse', label: 'Legacy MBSE JSON', ext: 'json', path: 'export/mbse-legacy.json', color: '#6b7280',
    blurb: 'The pre-SCDF-160 SysML-style JSON. Kept for scripts and notebooks that already read it.' },
]

async function download(url: string, filename: string, setErr: (m: string | null) => void) {
  try {
    const res = await fetch(url)
    if (!res.ok) {
      let msg = `${res.status}`
      try { const b = await res.json(); msg = typeof b.detail === 'string' ? b.detail : JSON.stringify(b.detail ?? b) } catch { /* noop */ }
      throw new Error(msg)
    }
    const blob = await res.blob()
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = filename; a.click(); URL.revokeObjectURL(a.href)
    setErr(null)
  } catch (e) { setErr(`${filename}: ${(e as Error).message}`) }
}

function ImportZone({ label, accept, endpoint, color, blurb, onDone }: {
  label: string; accept: string; endpoint: string; color: string; blurb: string; onDone: (r: ImportResult | null, err: string | null) => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  const [over, setOver] = useState(false)

  const upload = async (file: File) => {
    setBusy(true)
    try {
      const fd = new FormData(); fd.append('file', file, file.name)
      const res = await fetch(endpoint, { method: 'POST', body: fd })
      if (!res.ok) {
        let msg = `${res.status}`
        try { const b = await res.json(); msg = typeof b.detail === 'string' ? b.detail : JSON.stringify(b.detail ?? b) } catch { /* noop */ }
        throw new Error(msg)
      }
      onDone(await res.json(), null)
    } catch (e) { onDone(null, `${file.name}: ${(e as Error).message}`) }
    finally { setBusy(false); if (inputRef.current) inputRef.current.value = '' }
  }

  return (
    <div
      onDragOver={e => { e.preventDefault(); setOver(true) }} onDragLeave={() => setOver(false)}
      onDrop={e => { e.preventDefault(); setOver(false); const f = e.dataTransfer.files?.[0]; if (f) upload(f) }}
      onClick={() => inputRef.current?.click()}
      style={{
        flex: 1, minWidth: 220, padding: '0.6rem', borderRadius: '6px', cursor: busy ? 'wait' : 'pointer',
        border: `1px dashed ${over ? color : 'var(--border)'}`, background: over ? `${color}10` : 'var(--bg-primary)',
      }}>
      <div style={{ fontSize: '0.72rem', fontWeight: 600, color }}>{busy ? 'Importing…' : `Import ${label}`}</div>
      <div style={{ fontSize: '0.62rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>{blurb}</div>
      <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>Drop a file here or click to choose ({accept}).</div>
      <input ref={inputRef} type="file" accept={accept} style={{ display: 'none' }}
        onChange={e => { const f = e.target.files?.[0]; if (f) upload(f) }} />
    </div>
  )
}

function ImportSummary({ r }: { r: ImportResult }) {
  const counts = (o: Record<string, number> | number) =>
    typeof o === 'number' ? String(o) : Object.entries(o).filter(([, v]) => v).map(([k, v]) => `${k} ${v}`).join(', ') || '0'
  return (
    <div style={{ fontSize: '0.66rem', marginTop: '0.4rem', padding: '0.4rem 0.6rem', borderRadius: '4px', background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.3)' }}>
      <div style={{ color: '#6ee7b7', fontWeight: 600 }}>Imported {r.format}{r.filename ? ` — ${r.filename}` : ''}</div>
      <div>created: {counts(r.created)} · updated: {counts(r.updated)}{r.format === 'reqif' ? ` · relations: ${r.relations_created}` : ''}</div>
      {r.warnings?.length > 0 && (
        <details style={{ marginTop: '0.2rem' }}>
          <summary style={{ color: '#f59e0b', cursor: 'pointer' }}>{r.warnings.length} warning{r.warnings.length > 1 ? 's' : ''}</summary>
          <ul style={{ margin: '0.2rem 0 0 1rem', color: 'var(--text-secondary)' }}>{r.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
        </details>
      )}
    </div>
  )
}

export function ExchangePanel({ studyId, title = 'Model exchange' }: { studyId: string | null; title?: string }) {
  const qc = useQueryClient()
  const [err, setErr] = useState<string | null>(null)
  const [result, setResult] = useState<ImportResult | null>(null)
  const [cometMsg, setCometMsg] = useState<string | null>(null)
  const [pushing, setPushing] = useState(false)

  if (!studyId) {
    return <div style={{ padding: '0.5rem 0', color: 'var(--text-secondary)', fontSize: '0.72rem' }}>Create or join a study to exchange models.</div>
  }
  const base = `${API}/studies/${studyId}`
  const slug = studyId.slice(0, 8)

  const onImportDone = (r: ImportResult | null, e: string | null) => {
    setResult(r); setErr(e)
    if (r) qc.invalidateQueries()
  }

  const pushComet = async () => {
    setPushing(true); setCometMsg(null)
    try {
      const res = await fetch(`${base}/push/comet`, { method: 'POST' })
      const body = await res.json().catch(() => ({}))
      if (res.status === 501) setCometMsg(`Not available: ${body.detail || 'COMET push not configured'}. Set COMET_URL (and COMET_USER / COMET_PASSWORD) on the server to enable Annex C.2 push.`)
      else if (!res.ok) setCometMsg(`Push failed (${res.status}): ${typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail ?? body)}`)
      else setCometMsg(`Pushed to COMET: ${JSON.stringify(body)}`)
    } catch (e) { setCometMsg(`Push failed: ${(e as Error).message}`) }
    finally { setPushing(false) }
  }

  return (
    <div style={{ fontSize: '0.74rem' }}>
      <div style={{ fontWeight: 600, fontSize: '0.78rem', marginBottom: '0.15rem' }}>{title}</div>
      <div style={{ fontSize: '0.64rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
        Export the study's Arcadia spine (elements, functions, interfaces, exchange items, requirements, parameters) to standard formats, or import from them.
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', marginBottom: '0.6rem' }}>
        {EXPORTS.map(f => (
          <div key={f.id} style={{ display: 'flex', gap: '0.6rem', alignItems: 'flex-start', padding: '0.35rem 0.5rem', borderRadius: '4px', background: 'var(--bg-primary)', border: '1px solid var(--border)' }}>
            <button style={{ ...btn(f.color), minWidth: 150 }} onClick={() => download(`${base}/${f.path}`, `${f.id}_${slug}.${f.ext}`, setErr)}>
              ↓ {f.label}
            </button>
            <div style={{ fontSize: '0.64rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>{f.blurb}</div>
          </div>
        ))}
        <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'flex-start', padding: '0.35rem 0.5rem', borderRadius: '4px', background: 'var(--bg-primary)', border: '1px solid var(--border)' }}>
          <button style={{ ...btn('#ec4899'), minWidth: 150 }} disabled={pushing} onClick={pushComet}>
            {pushing ? 'Pushing…' : '⇧ Push to COMET'}
          </button>
          <div style={{ fontSize: '0.64rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
            ECSS-E-TM-10-25 Annex C.2 REST push to a COMET / CDP4 server (ESA CDF). Requires COMET_URL on the server.
            {cometMsg && <div style={{ color: cometMsg.startsWith('Pushed') ? '#6ee7b7' : '#f59e0b', marginTop: '0.2rem' }}>{cometMsg}</div>}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        <ImportZone label="Capella" accept=".zip" endpoint={`${base}/import/capella`} color="#3b82f6"
          blurb="Capella project zip (.aird + .capella). Elements, functions, interfaces and exchange items are merged by external id." onDone={onImportDone} />
        <ImportZone label="ReqIF" accept=".reqif,.reqifz,.xml" endpoint={`${base}/import/reqif`} color="#10b981"
          blurb="ReqIF from DOORS / Polarion / Jama. Requirements and their parent/child relations are created or updated." onDone={onImportDone} />
      </div>
      {result && <ImportSummary r={result} />}
      {err && <div style={{ color: '#ef4444', fontSize: '0.66rem', marginTop: '0.4rem' }}>{err}</div>}
    </div>
  )
}

export default ExchangePanel
