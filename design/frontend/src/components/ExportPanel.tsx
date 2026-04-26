import { useState } from 'react'
import { useDesignStore } from '../stores/designStore'

export function ExportPanel({ studyId }: { studyId?: string | null }) {
  const { result } = useDesignStore()
  const [exportStatus, setExportStatus] = useState<Record<string, string>>({})

  if (!result) {
    return (
      <div style={{ padding: '1rem', color: 'var(--text-secondary)' }}>
        <p>Run a design first to enable exports.</p>
      </div>
    )
  }

  const download = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  const handleExport = async (type: 'smo' | 'fsw' | 'docs' | 'mbse', label: string, review?: string) => {
    setExportStatus(s => ({ ...s, [type + (review || '')]: 'Exporting…' }))
    try {
      const sid = studyId || 'default'
      let path = ''
      if (type === 'docs') path = `/api/exports/docs/${sid}?review=${review || 'srr'}`
      else if (type === 'smo') path = `/api/exports/smo/${sid}`
      else if (type === 'mbse') path = `/api/exports/mbse/${sid}`
      else path = `/api/exports/fsw/${sid}`

      const res = await fetch(path, { method: 'POST' })
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
      const ct = res.headers.get('content-type') || ''

      if (ct.includes('application/zip') || ct.includes('octet-stream')) {
        const blob = await res.blob()
        const name = type === 'docs'
          ? `${review || 'srr'}_export.zip`
          : `${type}_export.zip`
        download(blob, name)
        setExportStatus(s => ({ ...s, [type + (review || '')]: `✓ ${label} downloaded` }))
      } else {
        // JSON response — for SMO/FSW which may return JSON with files
        const data = await res.json()
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        download(blob, `${type}_${sid}.json`)
        setExportStatus(s => ({ ...s, [type + (review || '')]: `✓ ${label} downloaded (JSON)` }))
      }
    } catch (err) {
      setExportStatus(s => ({ ...s, [type + (review || '')]: `✗ Error: ${String(err)}` }))
    }
  }

  return (
    <div style={{ padding: '1rem' }}>
      <h2>Export Design</h2>

      {/* SMO Simulator Config */}
      <div className="card">
        <h3>SMO Simulator Configuration</h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
          Generate ~20 YAML config files for the SpaceMissionSimulation platform.
          Includes subsystem configs, telemetry parameters, FDIR procedures, and monitoring rules.
        </p>
        <button className="btn btn-sm" onClick={() => handleExport('smo', 'SMO Configs')}>
          Export SMO Configs
        </button>
        {exportStatus.smo && <span style={{ fontSize: '0.75rem', marginLeft: '0.5rem', color: 'var(--success)' }}>{exportStatus.smo}</span>}
      </div>

      {/* Design Review Documents */}
      <div className="card">
        <h3>Design Review Documents</h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
          Generate design review documentation with auto-filled budget tables, equipment lists,
          and compliance matrices. Sections requiring human input are highlighted.
        </p>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-sm" onClick={() => handleExport('docs', 'SRR Document', 'srr')}>SRR</button>
          <button className="btn btn-sm" onClick={() => handleExport('docs', 'PDR Document', 'pdr')}>PDR</button>
          <button className="btn btn-sm" onClick={() => handleExport('docs', 'CDR Document', 'cdr')}>CDR</button>
        </div>
        {exportStatus.docssrr && <div style={{ fontSize: '0.75rem', marginTop: '0.5rem', color: 'var(--success)' }}>{exportStatus.docssrr}</div>}
        {exportStatus.docspdr && <div style={{ fontSize: '0.75rem', marginTop: '0.25rem', color: 'var(--success)' }}>{exportStatus.docspdr}</div>}
        {exportStatus.docscdr && <div style={{ fontSize: '0.75rem', marginTop: '0.25rem', color: 'var(--success)' }}>{exportStatus.docscdr}</div>}
      </div>

      {/* MBSE (ECSS-E-TM-10-25A-style) Export */}
      <div className="card">
        <h3>MBSE Export (ECSS-E-TM-10-25A-like)</h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
          Generate a SysML-like JSON containing blocks (Spacecraft → Subsystems),
          parameters with units &amp; sources, requirements, and traceability
          links. Diff-friendly for version control; importable into Cameo /
          Capella via a downstream converter. Carries the applicable ECSS
          standards from the originating template.
        </p>
        <button className="btn btn-sm" onClick={() => handleExport('mbse', 'MBSE JSON')}>
          Export MBSE JSON
        </button>
        {exportStatus.mbse && <span style={{ fontSize: '0.75rem', marginLeft: '0.5rem', color: 'var(--success)' }}>{exportStatus.mbse}</span>}
      </div>

      {/* Flight Software Architecture */}
      <div className="card">
        <h3>Flight Software Architecture</h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
          Generate cFS-style flight software scaffolding: C headers for parameter database,
          telemetry packets, mode tables, FDIR rules, and 10 application skeletons.
        </p>
        <button className="btn btn-sm" onClick={() => handleExport('fsw', 'FSW Architecture')}>
          Export FSW
        </button>
        {exportStatus.fsw && <span style={{ fontSize: '0.75rem', marginLeft: '0.5rem', color: 'var(--success)' }}>{exportStatus.fsw}</span>}
      </div>

      {/* Summary */}
      <div className="card" style={{ background: 'var(--bg-primary)' }}>
        <h3>Design Summary</h3>
        <div className="param-row">
          <span className="param-name">Converged</span>
          <span className="param-value">{result.converged ? 'Yes' : 'No'}</span>
        </div>
        <div className="param-row">
          <span className="param-name">Parameters</span>
          <span className="param-value">{Object.keys(result.parameters).length}</span>
        </div>
        <div className="param-row">
          <span className="param-name">Warnings</span>
          <span className="param-value">{result.warnings.length}</span>
        </div>
        <div className="param-row">
          <span className="param-name">Conflicts</span>
          <span className="param-value">{result.conflicts?.length || 0}</span>
        </div>
      </div>
    </div>
  )
}
