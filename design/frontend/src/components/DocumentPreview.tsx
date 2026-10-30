/**
 * DocumentPreview — Renders JSON output from DID generators and regulatory
 * templates as a nicely formatted document view instead of raw JSON.
 *
 * Handles ECSS DID sections, BOM data, regulatory field templates, and
 * summary statistics. Supports inline SVG, pipe-delimited tables, and
 * bullet lists detected from content strings.
 */
import { useCallback } from 'react'

interface SectionData {
  number?: string
  title?: string
  content?: string
  subsections?: SectionData[]
  fields?: { name: string; value: any; auto_populated?: boolean }[]
}

interface Props {
  title: string
  content: any // JSON response from a DID generator or regulatory template
  onClose?: () => void
}

/* ------------------------------------------------------------------ */
/*  Colour tokens (inline — matches SpaceCDF dark theme)              */
/* ------------------------------------------------------------------ */

const C = {
  bg: '#0a0e1a',
  bgCard: '#111827',
  bgHeader: '#1f2937',
  border: '#374151',
  text: '#d1d5db',
  textMuted: '#9ca3af',
  textDim: '#6b7280',
  accent: '#3b82f6',
  success: '#10b981',
  warning: '#f59e0b',
  white: '#ffffff',
}

/* ------------------------------------------------------------------ */
/*  Utility — detect content type within a string                     */
/* ------------------------------------------------------------------ */

function containsSVG(text: string): boolean {
  return typeof text === 'string' && text.includes('<svg')
}

function isTableContent(text: string): boolean {
  if (typeof text !== 'string') return false
  const lines = text.split('\n').filter(l => l.trim())
  return lines.length >= 2 && lines.filter(l => l.includes('|')).length >= 2
}

function isBulletList(text: string): boolean {
  if (typeof text !== 'string') return false
  const lines = text.split('\n').filter(l => l.trim())
  return lines.length >= 2 && lines.filter(l => l.trim().startsWith('- ')).length > lines.length * 0.5
}

function looksNumeric(cell: string): boolean {
  const trimmed = cell.trim()
  return /^[\d.,]+(%| ?[kKMGT]?[A-Za-z]*)?$/.test(trimmed) || /^-?\d/.test(trimmed)
}

/* ------------------------------------------------------------------ */
/*  Sub-renderers                                                     */
/* ------------------------------------------------------------------ */

function renderTable(text: string) {
  const lines = text.split('\n').filter(l => l.trim() && l.includes('|'))
  if (lines.length === 0) return null

  const parse = (line: string) =>
    line.split('|').map(c => c.trim()).filter((_, i, arr) => i > 0 && i < arr.length)

  // Skip separator rows (e.g. |---|---|)
  const dataLines = lines.filter(l => !/^\|?[\s-:|]+\|?$/.test(l))
  if (dataLines.length === 0) return null

  const header = parse(dataLines[0])
  const rows = dataLines.slice(1).map(parse)

  return (
    <div style={{ overflowX: 'auto', marginBottom: '0.75rem' }}>
      <table style={{
        width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem',
        border: `1px solid ${C.border}`,
      }}>
        <thead>
          <tr>
            {header.map((h, i) => (
              <th key={i} style={{
                padding: '0.4rem 0.6rem', textAlign: 'left', fontWeight: 600,
                background: C.bgHeader, color: C.white,
                borderBottom: `2px solid ${C.border}`,
                borderRight: i < header.length - 1 ? `1px solid ${C.border}` : undefined,
              }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri} style={{
              background: ri % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)',
            }}>
              {row.map((cell, ci) => (
                <td key={ci} style={{
                  padding: '0.35rem 0.6rem',
                  borderBottom: `1px solid ${C.border}`,
                  borderRight: ci < row.length - 1 ? `1px solid ${C.border}` : undefined,
                  fontFamily: looksNumeric(cell) ? 'monospace' : 'inherit',
                  color: C.text,
                }}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function renderBullets(text: string) {
  const lines = text.split('\n').filter(l => l.trim())
  return (
    <ul style={{ paddingLeft: '1.25rem', margin: '0.5rem 0', listStyleType: 'disc' }}>
      {lines.map((line, i) => {
        const content = line.trim().startsWith('- ') ? line.trim().slice(2) : line.trim()
        return (
          <li key={i} style={{
            fontSize: '0.78rem', color: C.text, marginBottom: '0.25rem', lineHeight: 1.5,
          }}>{content}</li>
        )
      })}
    </ul>
  )
}

function renderPlainText(text: string) {
  return (
    <div style={{ fontSize: '0.78rem', color: C.text, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
      {text}
    </div>
  )
}

function renderContentBlock(text: string) {
  if (!text || typeof text !== 'string') return null

  // Check for SVG content
  if (containsSVG(text)) {
    return <div dangerouslySetInnerHTML={{ __html: text }} style={{ marginBottom: '0.75rem' }} />
  }

  // Check for pipe-delimited tables
  if (isTableContent(text)) {
    // There may be mixed content — split around table blocks
    const lines = text.split('\n')
    const blocks: { type: 'table' | 'bullets' | 'text'; content: string }[] = []
    let current: string[] = []
    let currentType: 'table' | 'bullets' | 'text' = 'text'

    const flush = () => {
      if (current.length > 0) {
        blocks.push({ type: currentType, content: current.join('\n') })
        current = []
      }
    }

    for (const line of lines) {
      const hasTable = line.includes('|')
      if (hasTable && currentType !== 'table') {
        flush()
        currentType = 'table'
      } else if (!hasTable && currentType === 'table' && line.trim()) {
        flush()
        currentType = 'text'
      }
      if (line.trim() || currentType === 'table') current.push(line)
    }
    flush()

    return (
      <>
        {blocks.map((b, i) =>
          b.type === 'table' ? <div key={i}>{renderTable(b.content)}</div> :
            isBulletList(b.content) ? <div key={i}>{renderBullets(b.content)}</div> :
              <div key={i}>{renderPlainText(b.content)}</div>
        )}
      </>
    )
  }

  // Check for bullet lists
  if (isBulletList(text)) return renderBullets(text)

  // Plain text
  return renderPlainText(text)
}

/* ------------------------------------------------------------------ */
/*  Section Card                                                      */
/* ------------------------------------------------------------------ */

function SectionCard({ section, depth = 0 }: { section: SectionData; depth?: number }) {
  const isSubsection = depth > 0
  const headingSize = isSubsection ? '0.82rem' : '0.92rem'
  const marginLeft = depth * 1

  return (
    <div style={{
      marginBottom: '0.75rem',
      marginLeft: `${marginLeft}rem`,
      padding: '0.75rem 1rem',
      background: C.bgCard,
      borderRadius: '6px',
      border: `1px solid ${C.border}`,
      borderLeft: `3px solid ${C.accent}`,
    }}>
      {(section.number || section.title) && (
        <h3 style={{
          fontSize: headingSize, fontWeight: 600, color: C.white, margin: '0 0 0.5rem 0',
        }}>
          {section.number && (
            <span style={{ color: C.accent, marginRight: '0.5rem' }}>{section.number}</span>
          )}
          {section.title}
        </h3>
      )}

      {/* Regular content */}
      {section.content && renderContentBlock(section.content)}

      {/* Regulatory template fields */}
      {section.fields && section.fields.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          {section.fields.map((field, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'flex-start', gap: '0.5rem',
              padding: '0.3rem 0.5rem', borderRadius: '4px',
              background: 'rgba(255,255,255,0.02)',
            }}>
              <span style={{
                width: '8px', height: '8px', borderRadius: '50%', marginTop: '4px', flexShrink: 0,
                background: field.auto_populated ? C.success : C.warning,
              }} title={field.auto_populated ? 'Auto-populated' : 'Manual entry required'} />
              <span style={{ fontSize: '0.75rem', color: C.textMuted, minWidth: '140px', flexShrink: 0 }}>
                {field.name}
              </span>
              <span style={{ fontSize: '0.75rem', color: C.text, flex: 1 }}>
                {typeof field.value === 'object' ? JSON.stringify(field.value) : String(field.value ?? '')}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Nested subsections */}
      {section.subsections && section.subsections.length > 0 && (
        <div style={{ marginTop: '0.5rem' }}>
          {section.subsections.map((sub, i) => (
            <SectionCard key={i} section={sub} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  BOM Renderer                                                      */
/* ------------------------------------------------------------------ */

function BOMView({ lines }: { lines: any[] }) {
  // Group by category or subsystem
  const groups: Record<string, any[]> = {}
  for (const line of lines) {
    const key = line.category || line.subsystem || 'Other'
    if (!groups[key]) groups[key] = []
    groups[key].push(line)
  }

  return (
    <div>
      {Object.entries(groups).map(([group, items]) => (
        <div key={group} style={{ marginBottom: '0.75rem' }}>
          <div style={{
            fontSize: '0.78rem', fontWeight: 600, color: C.accent, padding: '0.3rem 0.5rem',
            background: C.bgHeader, borderRadius: '4px 4px 0 0',
            borderBottom: `1px solid ${C.border}`,
          }}>{group}</div>
          <table style={{
            width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem',
            border: `1px solid ${C.border}`,
          }}>
            <thead>
              <tr>
                {['Item', 'Qty', 'Mass (kg)', 'Power (W)', 'Cost (kEUR)'].map((h, i) => (
                  <th key={i} style={{
                    padding: '0.3rem 0.5rem', textAlign: i > 0 ? 'right' : 'left',
                    background: C.bgHeader, color: C.textMuted, fontWeight: 500,
                    borderBottom: `1px solid ${C.border}`,
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((item, ri) => (
                <tr key={ri} style={{
                  background: ri % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)',
                }}>
                  <td style={{ padding: '0.3rem 0.5rem', color: C.text }}>{item.name || item.item}</td>
                  <td style={{ padding: '0.3rem 0.5rem', textAlign: 'right', fontFamily: 'monospace', color: C.text }}>{item.quantity ?? item.qty ?? 1}</td>
                  <td style={{ padding: '0.3rem 0.5rem', textAlign: 'right', fontFamily: 'monospace', color: C.text }}>{item.mass_kg != null ? Number(item.mass_kg).toFixed(2) : '-'}</td>
                  <td style={{ padding: '0.3rem 0.5rem', textAlign: 'right', fontFamily: 'monospace', color: C.text }}>{item.power_w != null ? Number(item.power_w).toFixed(1) : '-'}</td>
                  <td style={{ padding: '0.3rem 0.5rem', textAlign: 'right', fontFamily: 'monospace', color: C.text }}>{item.cost_keur != null ? Number(item.cost_keur).toFixed(0) : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Summary Stats Bar                                                 */
/* ------------------------------------------------------------------ */

function SummaryBar({ summary }: { summary: Record<string, any> }) {
  const entries = Object.entries(summary).filter(([, v]) => v != null)
  if (entries.length === 0) return null

  return (
    <div style={{
      display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1rem',
      padding: '0.75rem', background: C.bgCard, borderRadius: '6px',
      border: `1px solid ${C.border}`,
    }}>
      {entries.map(([key, value]) => (
        <div key={key} style={{ textAlign: 'center', minWidth: '80px' }}>
          <div style={{
            fontSize: '1.1rem', fontWeight: 700, color: C.accent,
            fontFamily: 'monospace',
          }}>
            {typeof value === 'number' ? value.toLocaleString() : String(value)}
          </div>
          <div style={{
            fontSize: '0.65rem', color: C.textDim, textTransform: 'uppercase', letterSpacing: '0.5px',
          }}>
            {key.replace(/_/g, ' ')}
          </div>
        </div>
      ))}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Metadata Header                                                   */
/* ------------------------------------------------------------------ */

function MetadataHeader({ content }: { content: any }) {
  const items: { label: string; value: string }[] = []

  if (content.standard) items.push({ label: 'Standard', value: content.standard })
  if (content.document_standard) items.push({ label: 'Standard', value: content.document_standard })
  if (content.phase) items.push({ label: 'Phase', value: content.phase })
  if (content.generated_at || content.generation_date) {
    const date = content.generated_at || content.generation_date
    items.push({ label: 'Generated', value: typeof date === 'string' ? date.slice(0, 19).replace('T', ' ') : String(date) })
  }
  if (content.total_requirements != null) {
    items.push({ label: 'Requirements', value: String(content.total_requirements) })
  }

  if (items.length === 0) return null

  return (
    <div style={{
      display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '0.75rem',
      padding: '0.5rem 0.75rem', background: C.bgCard, borderRadius: '6px',
      border: `1px solid ${C.border}`, fontSize: '0.72rem',
    }}>
      {items.map((item, i) => (
        <span key={i} style={{ color: C.textMuted }}>
          <span style={{ fontWeight: 600, color: C.textDim }}>{item.label}: </span>
          <span style={{ color: C.text }}>{item.value}</span>
        </span>
      ))}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Main Component                                                    */
/* ------------------------------------------------------------------ */

export function DocumentPreview({ title, content, onClose }: Props) {
  const handleDownloadJSON = useCallback(() => {
    const blob = new Blob([JSON.stringify(content, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${title.replace(/\s+/g, '_')}.json`
    a.click()
    URL.revokeObjectURL(url)
  }, [content, title])

  const handlePrint = useCallback(() => {
    window.print()
  }, [])

  const sections: SectionData[] = content?.sections || []
  const hasBOM = Array.isArray(content?.lines)
  const hasSummary = content?.summary && typeof content.summary === 'object'

  return (
    <div style={{
      background: C.bg,
      border: `1px solid ${C.border}`,
      borderRadius: '8px',
      maxHeight: '80vh',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      {/* Title bar */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0.5rem',
        padding: '0.6rem 1rem',
        background: C.bgHeader,
        borderBottom: `1px solid ${C.border}`,
        flexShrink: 0,
      }}>
        <span style={{ flex: 1, fontWeight: 700, fontSize: '0.92rem', color: C.white }}>
          {title}
        </span>
        <button onClick={handlePrint} style={{
          padding: '0.25rem 0.6rem', fontSize: '0.7rem', borderRadius: '4px',
          background: 'transparent', color: C.textMuted, border: `1px solid ${C.border}`,
          cursor: 'pointer',
        }}>Print</button>
        <button onClick={handleDownloadJSON} style={{
          padding: '0.25rem 0.6rem', fontSize: '0.7rem', borderRadius: '4px',
          background: C.accent, color: C.white, border: 'none', cursor: 'pointer',
        }}>Download JSON</button>
        {onClose && (
          <button onClick={onClose} style={{
            padding: '0.25rem 0.5rem', fontSize: '0.85rem', borderRadius: '4px',
            background: 'transparent', color: C.textMuted, border: 'none',
            cursor: 'pointer', lineHeight: 1,
          }} title="Close">&times;</button>
        )}
      </div>

      {/* Scrollable body */}
      <div style={{
        padding: '1rem',
        overflowY: 'auto',
        flex: 1,
      }}>
        {/* Metadata row */}
        <MetadataHeader content={content} />

        {/* Summary stats bar */}
        {hasSummary && <SummaryBar summary={content.summary} />}

        {/* BOM data */}
        {hasBOM && <BOMView lines={content.lines} />}

        {/* Sections */}
        {sections.length > 0 && sections.map((section, i) => (
          <SectionCard key={i} section={section} />
        ))}

        {/* Fallback: if no sections and no BOM, render raw fields */}
        {sections.length === 0 && !hasBOM && (
          <div style={{ padding: '0.5rem' }}>
            {Object.entries(content || {}).filter(([k]) =>
              !['summary', 'standard', 'document_standard', 'phase', 'generated_at', 'generation_date', 'total_requirements'].includes(k)
            ).map(([key, value]) => {
              // If value is a string that looks like content, render it
              if (typeof value === 'string') {
                return (
                  <div key={key} style={{ marginBottom: '0.75rem' }}>
                    <div style={{
                      fontSize: '0.78rem', fontWeight: 600, color: C.textMuted,
                      marginBottom: '0.25rem', textTransform: 'capitalize',
                    }}>{key.replace(/_/g, ' ')}</div>
                    {renderContentBlock(value)}
                  </div>
                )
              }
              // If it is an object/array, render as formatted JSON
              if (value != null && typeof value === 'object') {
                return (
                  <div key={key} style={{ marginBottom: '0.75rem' }}>
                    <div style={{
                      fontSize: '0.78rem', fontWeight: 600, color: C.textMuted,
                      marginBottom: '0.25rem', textTransform: 'capitalize',
                    }}>{key.replace(/_/g, ' ')}</div>
                    <pre style={{
                      fontSize: '0.72rem', color: C.text, background: C.bgCard,
                      padding: '0.5rem', borderRadius: '4px', overflow: 'auto',
                      maxHeight: '200px', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                      border: `1px solid ${C.border}`,
                    }}>
                      {JSON.stringify(value, null, 2)}
                    </pre>
                  </div>
                )
              }
              return null
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default DocumentPreview
