/**
 * ExchangePanel — model exchange (SCDF-160).
 *
 * Downloads: Capella (.zip), ECSS-E-TM-10-25 (.zip), ReqIF, SysML v2 text,
 * legacy MBSE JSON. Imports: Capella zip and ReqIF (multipart field `file`).
 * "Push to COMET" surfaces the server's 501 message when not configured.
 */
import { useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import type { ImportResult } from '../types/arcadia'
import { fs } from '../theme/tokens'

const API = '/api'


interface Fmt { id: string; label: string; ext: string; path: string; color: string; blurb: string }

// Labels and blurbs are display-only; ids, paths and file names are not translated.
const buildExports = (t: TFunction): Fmt[] => [
  { id: 'capella', label: 'Capella', ext: 'zip', path: 'export/capella.zip', color: 'var(--interactive)',
    blurb: t('Arcadia model (.aird/.capella + property values). Open in Capella 7.x; round-trips through the Capella import below.') },
  { id: 'ecss', label: 'ECSS-E-TM-10-25', ext: 'zip', path: 'export/ecss-10-25.zip', color: 'var(--cat-2)',
    blurb: t('Annex A JSON (engineering model, iterations, parameters). Consumed by ESA CDF tools, COMET / CDP4 and other Annex A readers.') },
  { id: 'reqif', label: 'ReqIF', ext: 'reqif', path: 'export/requirements.reqif', color: 'var(--status-ok)',
    blurb: t('Requirements Interchange Format (OMG). Import into IBM DOORS / DOORS Next, Polarion, Jama, Codebeamer.') },
  { id: 'sysml', label: 'SysML v2', ext: 'sysml', path: 'export/model.sysml', color: 'var(--status-caution)',
    blurb: t('KerML/SysML v2 textual notation: parts, ports, connections, requirements. For SysML v2 pilot tools, Syside, Cameo 2024+.') },
  { id: 'mbse', label: t('Legacy MBSE JSON'), ext: 'json', path: 'export/mbse-legacy.json', color: 'var(--text-3)',
    blurb: t('The pre-SCDF-160 SysML-style JSON. Kept for scripts and notebooks that already read it.') },
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
  const { t } = useTranslation()
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
        border: `1px dashed ${over ? color : 'var(--border)'}`, background: over ? `color-mix(in srgb, ${color} 6%, transparent)` : 'var(--bg-primary)',
      }}>
      <div style={{ fontSize: fs.label, fontWeight: 600, color }}>{busy ? t('Importing…') : t('Import {{label}}', { label })}</div>
      <div className="t-12 c-2 mt-1">{blurb}</div>
      <div className="t-12 c-2 mt-1">{t('Drop a file here or click to choose ({{accept}}).', { accept })}</div>
      <input ref={inputRef} type="file" accept={accept} style={{ display: 'none' }}
        onChange={e => { const f = e.target.files?.[0]; if (f) upload(f) }} />
    </div>
  )
}

function ImportSummary({ r }: { r: ImportResult }) {
  const { t } = useTranslation()
  const counts = (o: Record<string, number> | number) =>
    typeof o === 'number' ? String(o) : Object.entries(o).filter(([, v]) => v).map(([k, v]) => `${k} ${v}`).join(', ') || '0'
  return (
    <div style={{ fontSize: fs.label, marginTop: '0.4rem', padding: '0.4rem 0.6rem', borderRadius: '4px', background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.3)' }}>
      <div className="c-ok w-600">{t('Imported {{format}}', { format: r.format })}{r.filename ? ` — ${r.filename}` : ''}</div>
      <div>{t('created: {{created}} · updated: {{updated}}', { created: counts(r.created), updated: counts(r.updated) })}{r.format === 'reqif' ? ` · ${t('relations: {{n}}', { n: r.relations_created })}` : ''}</div>
      {r.warnings?.length > 0 && (
        <details className="mt-1">
          <summary className="c-caution cursor-p">{t('{{count}} warnings', { count: r.warnings.length, defaultValue_one: '{{count}} warning' })}</summary>
          <ul className="mt-1 ml-4 c-2">{r.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
        </details>
      )}
    </div>
  )
}

export function ExchangePanel({ studyId, title }: { studyId: string | null; title?: string }) {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [err, setErr] = useState<string | null>(null)
  const [result, setResult] = useState<ImportResult | null>(null)
  const [cometMsg, setCometMsg] = useState<string | null>(null)
  const [cometOk, setCometOk] = useState(false)
  const [pushing, setPushing] = useState(false)

  if (!studyId) {
    return <div className="py-2 px-0 c-2 t-12">{t('Create or join a study to exchange models.')}</div>
  }
  const base = `${API}/studies/${studyId}`
  const slug = studyId.slice(0, 8)
  const EXPORTS = buildExports(t)

  const onImportDone = (r: ImportResult | null, e: string | null) => {
    setResult(r); setErr(e)
    if (r) qc.invalidateQueries()
  }

  const pushComet = async () => {
    setPushing(true); setCometMsg(null); setCometOk(false)
    try {
      const res = await fetch(`${base}/push/comet`, { method: 'POST' })
      const body = await res.json().catch(() => ({}))
      if (res.status === 501) setCometMsg(t('Not available: {{detail}}. Set COMET_URL (and COMET_USER / COMET_PASSWORD) on the server to enable Annex C.2 push.', { detail: body.detail || t('COMET push not configured') }))
      else if (!res.ok) setCometMsg(t('Push failed ({{status}}): {{detail}}', { status: res.status, detail: typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail ?? body) }))
      else { setCometMsg(t('Pushed to COMET: {{result}}', { result: JSON.stringify(body) })); setCometOk(true) }
    } catch (e) { setCometMsg(t('Push failed: {{message}}', { message: (e as Error).message })) }
    finally { setPushing(false) }
  }

  return (
    <div className="t-12">
      <div className="w-600 t-12 mb-1">{title ?? t('Model exchange')}</div>
      <div className="t-12 c-2 mb-2">
        {t("Export the study's Arcadia spine (elements, functions, interfaces, exchange items, requirements, parameters) to standard formats, or import from them.")}
      </div>

      <div className="stack gap-1 mb-2">
        {EXPORTS.map(f => (
          <div key={f.id} className="flex gap-2 ai-s py-1 px-2 rounded bg-0 bd">
            <button className="c2o-btn c2o-btn--sm" style={{ minWidth: 150 }} onClick={() => download(`${base}/${f.path}`, `${f.id}_${slug}.${f.ext}`, setErr)}>
              ↓ {f.label}
            </button>
            <div className="t-12 c-2 lh-text">{f.blurb}</div>
          </div>
        ))}
        <div className="flex gap-2 ai-s py-1 px-2 rounded bg-0 bd">
          <button className="c2o-btn c2o-btn--sm" style={{ minWidth: 150 }} disabled={pushing} onClick={pushComet}>
            {pushing ? t('Pushing…') : t('⇧ Push to COMET')}
          </button>
          <div className="t-12 c-2 lh-text">
            {t('ECSS-E-TM-10-25 Annex C.2 REST push to a COMET / CDP4 server (ESA CDF). Requires COMET_URL on the server.')}
            {cometMsg && <div style={{ color: cometOk ? 'var(--status-ok)' : 'var(--status-caution)', marginTop: '0.2rem' }}>{cometMsg}</div>}
          </div>
        </div>
      </div>

      <div className="flex gap-2 wrap">
        <ImportZone label="Capella" accept=".zip" endpoint={`${base}/import/capella`} color="var(--interactive)"
          blurb={t('Capella project zip (.aird + .capella). Elements, functions, interfaces and exchange items are merged by external id.')} onDone={onImportDone} />
        <ImportZone label="ReqIF" accept=".reqif,.reqifz,.xml" endpoint={`${base}/import/reqif`} color="var(--status-ok)"
          blurb={t('ReqIF from DOORS / Polarion / Jama. Requirements and their parent/child relations are created or updated.')} onDone={onImportDone} />
      </div>
      {result && <ImportSummary r={result} />}
      {err && <div className="c-alarm t-12 mt-2">{err}</div>}
    </div>
  )
}

export default ExchangePanel
