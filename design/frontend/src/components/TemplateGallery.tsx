import { useMemo, useState } from 'react'
import { useTemplates, useCreateStudyFromTemplate, type MissionTemplate } from '../hooks/useTemplates'

interface Props {
  onClose: () => void
  onInstantiated: (studyId: string) => void
}

const ARCHETYPE_LABELS: Record<string, string> = {
  cubesat_tech_demo: 'CubeSat Tech Demo',
  cubesat_eo: 'CubeSat EO',
  smallsat_eo: 'Smallsat EO',
  comsat_leo: 'Comsat LEO',
  comsat_geo: 'Comsat GEO',
  lunar_orbiter: 'Lunar',
  mars_orbiter: 'Mars',
  constellation_member: 'Constellation',
  science_l2: 'Science L2',
}

export function TemplateGallery({ onClose, onInstantiated }: Props) {
  const { data: templates, isLoading, error } = useTemplates()
  const instantiate = useCreateStudyFromTemplate()
  const [filter, setFilter] = useState<string>('all')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const archetypes = useMemo(() => {
    if (!templates) return []
    const set = new Set<string>()
    templates.forEach(t => set.add(t.archetype))
    return Array.from(set)
  }, [templates])

  const filtered = useMemo(() => {
    if (!templates) return []
    if (filter === 'all') return templates
    return templates.filter(t => t.archetype === filter)
  }, [templates, filter])

  const selected = filtered.find(t => t.id === selectedId) || null

  const handleInstantiate = async (tmpl: MissionTemplate) => {
    try {
      const study = await instantiate.mutateAsync(tmpl.id)
      onInstantiated(study.id)
    } catch (err) {
      alert(`Failed to create study: ${err}`)
    }
  }

  return (
    <div
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)',
        zIndex: 9000, display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'var(--bg-primary, #111827)',
          border: '1px solid var(--border, #374151)',
          borderRadius: '8px',
          padding: '1.5rem',
          width: '90%',
          maxWidth: '1100px',
          maxHeight: '85vh',
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.75rem', marginBottom: '0.75rem' }}>
          <h2 style={{ margin: 0 }}>Mission Templates</h2>
          <span style={{ color: 'var(--text-secondary, #9ca3af)', fontSize: '0.85rem' }}>
            Start a new study from a canonical archetype
          </span>
          <button className="btn btn-sm" onClick={onClose} style={{ marginLeft: 'auto' }}>Close</button>
        </div>

        {/* Filter chips */}
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
          <Chip active={filter === 'all'} onClick={() => setFilter('all')}>All</Chip>
          {archetypes.map(a => (
            <Chip key={a} active={filter === a} onClick={() => setFilter(a)}>
              {ARCHETYPE_LABELS[a] || a}
            </Chip>
          ))}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 1fr' : '1fr', gap: '1rem', overflow: 'hidden', flex: 1 }}>
          {/* Grid */}
          <div style={{ overflowY: 'auto', paddingRight: '0.5rem' }}>
            {isLoading && <div>Loading templates…</div>}
            {error && <div style={{ color: 'var(--danger, #f87171)' }}>Failed to load templates: {String(error)}</div>}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '0.75rem' }}>
              {filtered.map(t => (
                <TemplateCard
                  key={t.id}
                  tmpl={t}
                  selected={t.id === selectedId}
                  onClick={() => setSelectedId(t.id)}
                />
              ))}
            </div>
          </div>

          {/* Detail pane */}
          {selected && (
            <div
              style={{
                overflowY: 'auto',
                borderLeft: '1px solid var(--border, #374151)',
                paddingLeft: '1rem',
              }}
            >
              <h3 style={{ marginTop: 0 }}>{selected.name}</h3>
              <p style={{ color: 'var(--text-secondary, #9ca3af)' }}>{selected.description}</p>

              <Row label="Archetype" value={ARCHETYPE_LABELS[selected.archetype] || selected.archetype} />
              <Row label="Target phase" value={selected.target_phase.toUpperCase()} />
              <Row label="Margin policy" value={`${selected.margin_policy_percent}%`} />
              <Row label="Spacecraft class" value={selected.requirements.spacecraft_class} />
              <Row label="Target mass" value={`${selected.requirements.target_mass_kg ?? '—'} kg`} />
              <Row label="Target cost" value={`${selected.requirements.target_cost_meur ?? '—'} MEUR`} />
              <Row label="Design lifetime" value={`${selected.requirements.design_lifetime_years} y`} />

              {selected.typical_use_cases.length > 0 && (
                <>
                  <h4 style={{ marginBottom: '0.3rem' }}>Typical use cases</h4>
                  <ul style={{ marginTop: 0, paddingLeft: '1.2rem', fontSize: '0.85rem' }}>
                    {selected.typical_use_cases.map((uc, i) => <li key={i}>{uc}</li>)}
                  </ul>
                </>
              )}

              {selected.applicable_ecss.length > 0 && (
                <>
                  <h4 style={{ marginBottom: '0.3rem' }}>Applicable ECSS standards</h4>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                    {selected.applicable_ecss.map(s => (
                      <span
                        key={s}
                        title={s}
                        style={{
                          fontSize: '0.7rem',
                          padding: '0.15rem 0.4rem',
                          background: 'var(--bg-secondary, #1f2937)',
                          border: '1px solid var(--border, #374151)',
                          borderRadius: '3px',
                          fontFamily: 'monospace',
                        }}
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </>
              )}

              {selected.equipment_hints.length > 0 && (
                <>
                  <h4 style={{ marginBottom: '0.3rem', marginTop: '0.75rem' }}>Equipment hints</h4>
                  <ul style={{ marginTop: 0, paddingLeft: '1.2rem', fontSize: '0.8rem' }}>
                    {selected.equipment_hints.map((h, i) => (
                      <li key={i}><strong>{h.category}</strong>: {h.rationale}</li>
                    ))}
                  </ul>
                </>
              )}

              {selected.notes && (
                <>
                  <h4 style={{ marginBottom: '0.3rem' }}>Notes</h4>
                  <pre style={{
                    whiteSpace: 'pre-wrap',
                    fontSize: '0.8rem',
                    fontFamily: 'inherit',
                    color: 'var(--text-secondary, #9ca3af)',
                    margin: 0,
                  }}>{selected.notes}</pre>
                </>
              )}

              <button
                className="btn"
                style={{ marginTop: '1rem', width: '100%' }}
                onClick={() => handleInstantiate(selected)}
                disabled={instantiate.isPending}
              >
                {instantiate.isPending ? 'Creating…' : `Create study from ${selected.id}`}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function TemplateCard({
  tmpl, selected, onClick,
}: {
  tmpl: MissionTemplate
  selected: boolean
  onClick: () => void
}) {
  return (
    <div
      onClick={onClick}
      style={{
        cursor: 'pointer',
        padding: '0.75rem',
        borderRadius: '6px',
        border: `1px solid ${selected ? 'var(--accent, #3b82f6)' : 'var(--border, #374151)'}`,
        background: selected ? 'rgba(59,130,246,0.08)' : 'var(--bg-secondary, #1f2937)',
      }}
    >
      <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{tmpl.name}</div>
      <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary, #9ca3af)', marginTop: '0.15rem' }}>
        {ARCHETYPE_LABELS[tmpl.archetype] || tmpl.archetype} · {tmpl.target_phase.toUpperCase()}
      </div>
      <div style={{ fontSize: '0.78rem', marginTop: '0.4rem', lineHeight: 1.4, color: 'var(--text-secondary, #d1d5db)' }}>
        {tmpl.description.length > 140 ? tmpl.description.slice(0, 140) + '…' : tmpl.description}
      </div>
      <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
        {tmpl.tags.slice(0, 4).map(tag => (
          <span
            key={tag}
            style={{
              fontSize: '0.65rem',
              padding: '0.1rem 0.3rem',
              background: 'var(--bg-primary, #111827)',
              border: '1px solid var(--border, #374151)',
              borderRadius: '3px',
              color: 'var(--text-secondary, #9ca3af)',
            }}
          >
            {tag}
          </span>
        ))}
      </div>
    </div>
  )
}

function Chip({
  children, active, onClick,
}: { children: React.ReactNode; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: active ? 'var(--accent, #3b82f6)' : 'transparent',
        color: active ? 'white' : 'var(--text-secondary, #9ca3af)',
        border: `1px solid ${active ? 'var(--accent, #3b82f6)' : 'var(--border, #374151)'}`,
        padding: '0.25rem 0.6rem',
        borderRadius: '4px',
        cursor: 'pointer',
        fontSize: '0.75rem',
      }}
    >
      {children}
    </button>
  )
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', fontSize: '0.82rem', padding: '0.15rem 0' }}>
      <span style={{ color: 'var(--text-secondary, #9ca3af)', minWidth: '120px' }}>{label}</span>
      <span>{value}</span>
    </div>
  )
}
