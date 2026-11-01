/**
 * EquipmentBrowser — Browse and select components from the Knowledge Base.
 *
 * Shown at Level 3 (Equipment) in the BlocksPanel.
 * Fetches from GET /api/engineering/equipment/{domain}/search
 * Selecting a component creates a component element under the current focus.
 */
import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { fs } from '../theme/tokens'
import { subsystemStyle } from '../theme/tokens'

const API = '/api'

// English text is the i18n key
const DOMAIN_LABELS: Record<string, string> = {
  power: 'Power (EPS)', aocs: 'AOCS', ttc: 'Comms (TTC)', thermal: 'Thermal',
  structure: 'Structure', propulsion: 'Propulsion', obc: 'OBC / C&DH', ground: 'Ground',
}

const DOMAINS = [
  { id: 'power', label: DOMAIN_LABELS.power, color: subsystemStyle('power').color },
  { id: 'aocs', label: DOMAIN_LABELS.aocs, color: subsystemStyle('aocs').color },
  { id: 'ttc', label: DOMAIN_LABELS.ttc, color: subsystemStyle('ttc').color },
  { id: 'thermal', label: DOMAIN_LABELS.thermal, color: subsystemStyle('thermal').color },
  { id: 'structure', label: DOMAIN_LABELS.structure, color: subsystemStyle('structure').color },
  { id: 'propulsion', label: DOMAIN_LABELS.propulsion, color: subsystemStyle('propulsion').color },
  { id: 'obc', label: DOMAIN_LABELS.obc, color: subsystemStyle('obc').color },
  { id: 'ground', label: DOMAIN_LABELS.ground, color: subsystemStyle('ground').color },
]

export function EquipmentBrowser({ onClose }: { onClose?: () => void }) {
  const { t } = useTranslation()
  const studyId = useUIStore(s => s.studyId)
  const focusElementId = useUIStore(s => s.focusElementId)
  const [domain, setDomain] = useState('power')
  const [search, setSearch] = useState('')
  const qc = useQueryClient()

  // Auto-select domain from the focused parent element's subsystem_domain
  const allElements: any[] = qc.getQueryData(['elements', studyId]) || []
  const focusElement = allElements.find((e: any) => e.id === focusElementId)
  useEffect(() => {
    if (focusElement?.subsystem_domain) {
      const match = DOMAINS.find(d => d.id === focusElement.subsystem_domain)
      if (match) setDomain(match.id)
    }
  }, [focusElementId, focusElement?.subsystem_domain])

  const { data, isLoading } = useQuery({
    queryKey: ['kb-equipment', domain, studyId],
    queryFn: async () => {
      const url = studyId
        ? `${API}/engineering/equipment/${domain}/search?study_id=${studyId}`
        : `${API}/engineering/equipment/${domain}/search`
      const res = await fetch(url)
      if (!res.ok) return { domain, categories: {} }
      return res.json()
    },
  })

  const selectMutation = useMutation({
    mutationFn: async (component: any) => {
      if (!studyId || !focusElementId) return
      const res = await fetch(`${API}/elements/?study_id=${studyId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: component.name || component.id || 'Component',
          element_type: 'component',
          parent_id: focusElementId,
          segment: 'space',
          subsystem_domain: domain,
          mass_kg: component.mass_kg ?? null,
          power_avg_w: component.power_w ?? component.power_avg_w ?? null,
          cost_recurring_keur: component.cost_keur ?? null,
          trl: component.trl ?? null,
          manufacturer: component.manufacturer ?? null,
          kb_component_id: component.id ?? null,
          quantity: 1,
        }),
      })
      if (!res.ok) throw new Error(await res.text())
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['elements', studyId] })
    },
  })

  // Flatten categories into a list for display
  const allComponents: Array<{ category: string; component: any; fit_score: number; notes: string[] }> = []
  if (data?.categories) {
    for (const [cat, items] of Object.entries(data.categories)) {
      for (const item of items as any[]) {
        allComponents.push({ category: cat, ...item })
      }
    }
  }

  // Filter by search
  const filtered = search
    ? allComponents.filter(c => {
        const name = (c.component?.name || c.component?.id || '').toLowerCase()
        const mfr = (c.component?.manufacturer || '').toLowerCase()
        return name.includes(search.toLowerCase()) || mfr.includes(search.toLowerCase())
      })
    : allComponents

  const domainInfo = DOMAINS.find(d => d.id === domain)!

  return (
    <div style={{ padding: '0.5rem 1rem', fontSize: fs.label }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
        <span style={{ fontWeight: 600, fontSize: fs.label }}>{t('Equipment Catalog')}</span>
        <span style={{ flex: 1 }} />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder={t('Search...')}
          style={{
            padding: '0.2rem 0.4rem', fontSize: fs.label, borderRadius: '3px', width: 140,
            background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)',
          }}
        />
        {onClose && (
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>×</button>
        )}
      </div>

      {/* Domain tabs */}
      <div style={{ display: 'flex', gap: '0.2rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
        {DOMAINS.map(d => (
          <button
            key={d.id}
            onClick={() => setDomain(d.id)}
            style={{
              padding: '0.2rem 0.5rem', fontSize: fs.label, borderRadius: '3px',
              background: domain === d.id ? d.color : 'var(--bg-card)',
              color: domain === d.id ? 'white' : 'var(--text-secondary)',
              border: 'none', cursor: 'pointer',
            }}
          >
            {t(d.label)}
          </button>
        ))}
      </div>

      {isLoading && <div style={{ color: 'var(--text-secondary)', padding: '0.5rem 0' }}>{t('Loading components...')}</div>}

      {!focusElementId && (
        <div style={{ color: 'var(--warning)', padding: '0.3rem', background: 'rgba(245,158,11,0.1)', borderRadius: '3px', marginBottom: '0.4rem' }}>
          {t('Drill into a subsystem first to add equipment to it.')}
        </div>
      )}

      {/* Component list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', maxHeight: 300, overflow: 'auto' }}>
        {filtered.length === 0 && !isLoading && (
          <div style={{ color: 'var(--text-secondary)', padding: '0.5rem 0' }}>{t('No components found.')}</div>
        )}
        {filtered.map((item, i) => {
          const c = item.component || {}
          return (
            <div key={`${item.category}-${c.id || c.name || i}`} style={{
              display: 'flex', alignItems: 'center', gap: '0.4rem',
              padding: '0.3rem 0.4rem', borderRadius: '4px',
              background: 'var(--bg-card)', border: '1px solid var(--border)',
            }}>
              {/* Category */}
              <span style={{
                fontSize: fs.label, padding: '0.05rem 0.2rem', borderRadius: '2px',
                background: `color-mix(in srgb, ${domainInfo.color} 13%, transparent)`, color: domainInfo.color,
                fontWeight: 600, flexShrink: 0, textTransform: 'uppercase',
              }}>
                {item.category.replace(/_/g, ' ')}
              </span>

              {/* Name + manufacturer */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 500, fontSize: fs.label }}>{c.name || c.id}</div>
                {c.manufacturer && <div style={{ fontSize: fs.label, color: 'var(--text-secondary)' }}>{c.manufacturer}</div>}
              </div>

              {/* Specs */}
              <div style={{ display: 'flex', gap: '0.4rem', fontSize: fs.label, color: 'var(--text-secondary)', flexShrink: 0 }}>
                {c.mass_kg != null && <span>{c.mass_kg} kg</span>}
                {(c.power_w || c.power_avg_w) != null && <span>{c.power_w || c.power_avg_w} W</span>}
                {c.cost_keur != null && <span>{c.cost_keur} kEUR</span>}
                {c.trl != null && <span>TRL{c.trl}</span>}
              </div>

              {/* Fit score */}
              {item.fit_score > 0 && (
                <span style={{
                  fontSize: fs.label, padding: '0.05rem 0.2rem', borderRadius: '2px', flexShrink: 0,
                  background: item.fit_score > 0.7 ? 'rgba(16,185,129,0.15)' : item.fit_score > 0.4 ? 'rgba(245,158,11,0.15)' : 'rgba(239,68,68,0.15)',
                  color: item.fit_score > 0.7 ? 'var(--success)' : item.fit_score > 0.4 ? 'var(--warning)' : 'var(--danger)',
                  fontWeight: 600,
                }}>
                  {(item.fit_score * 100).toFixed(0)}%
                </span>
              )}

              {/* Select button */}
              <button
                onClick={() => selectMutation.mutate(c)}
                disabled={!focusElementId || selectMutation.isPending}
                style={{
                  padding: '0.15rem 0.4rem', fontSize: fs.label, fontWeight: 600, borderRadius: '3px',
                  background: focusElementId ? 'var(--success)' : 'var(--border)',
                  color: 'white', border: 'none', cursor: focusElementId ? 'pointer' : 'not-allowed',
                  flexShrink: 0,
                }}
              >
                {t('+ Add')}
              </button>
            </div>
          )
        })}
      </div>

      {/* Custom equipment form */}
      <CustomEquipmentForm
        studyId={studyId}
        focusElementId={focusElementId}
        domain={domain}
        onCreated={() => qc.invalidateQueries({ queryKey: ['elements', studyId] })}
      />
    </div>
  )
}

function CustomEquipmentForm({ studyId, focusElementId, domain, onCreated }: {
  studyId: string | null; focusElementId: string | null; domain: string; onCreated: () => void
}) {
  const { t } = useTranslation()
  const [expanded, setExpanded] = useState(false)
  const [name, setName] = useState('')
  const [mass, setMass] = useState('')
  const [power, setPower] = useState('')
  const [cost, setCost] = useState('')
  const [trl, setTrl] = useState('5')
  const [mfr, setMfr] = useState('')
  const [qty, setQty] = useState('1')

  const create = async () => {
    if (!studyId || !focusElementId || !name) return
    await fetch(`${API}/elements/?study_id=${studyId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        element_type: 'component',
        parent_id: focusElementId,
        segment: 'space',
        subsystem_domain: domain,
        mass_kg: mass ? parseFloat(mass) : null,
        power_avg_w: power ? parseFloat(power) : null,
        cost_recurring_keur: cost ? parseFloat(cost) : null,
        trl: trl ? parseInt(trl) : null,
        manufacturer: mfr || null,
        quantity: parseInt(qty) || 1,
      }),
    })
    setName(''); setMass(''); setPower(''); setCost(''); setMfr('')
    setExpanded(false)
    onCreated()
  }

  if (!expanded) {
    return (
      <button onClick={() => setExpanded(true)} style={{
        marginTop: '0.4rem', padding: '0.3rem 0.6rem', fontSize: fs.label, fontWeight: 600,
        borderRadius: '4px', background: 'var(--bg-card)', border: '1px solid var(--border)',
        color: 'var(--text-secondary)', cursor: 'pointer', width: '100%', textAlign: 'left',
      }}>
        {t('+ Define Custom Equipment')}
      </button>
    )
  }

  const inp: React.CSSProperties = {
    padding: '0.2rem 0.3rem', fontSize: fs.label, borderRadius: '3px',
    background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-primary)',
  }

  return (
    <div style={{
      marginTop: '0.4rem', padding: '0.4rem', borderRadius: '4px',
      background: 'var(--bg-card)', border: '1px solid var(--accent)',
    }}>
      <div style={{ fontSize: fs.label, fontWeight: 600, color: 'var(--accent)', marginBottom: '0.3rem' }}>
        {t('Custom Equipment')}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.3rem', marginBottom: '0.3rem' }}>
        <input value={name} onChange={e => setName(e.target.value)} placeholder={t('Name *')} style={{ ...inp, gridColumn: '1 / -1' }} autoFocus />
        <input value={mass} onChange={e => setMass(e.target.value)} placeholder={t('Mass (kg)')} type="number" step="0.01" style={inp} />
        <input value={power} onChange={e => setPower(e.target.value)} placeholder={t('Power (W)')} type="number" step="0.1" style={inp} />
        <input value={cost} onChange={e => setCost(e.target.value)} placeholder={t('Cost (kEUR)')} type="number" step="1" style={inp} />
        <input value={trl} onChange={e => setTrl(e.target.value)} placeholder={t('TRL (1-9)')} type="number" min="1" max="9" style={inp} />
        <input value={mfr} onChange={e => setMfr(e.target.value)} placeholder={t('Manufacturer')} style={inp} />
        <input value={qty} onChange={e => setQty(e.target.value)} placeholder={t('Qty')} type="number" min="1" style={inp} />
      </div>
      <div style={{ display: 'flex', gap: '0.3rem' }}>
        <button onClick={create} disabled={!name || !focusElementId} style={{
          padding: '0.25rem 0.5rem', fontSize: fs.label, fontWeight: 600, borderRadius: '3px',
          background: 'var(--success)', color: 'white', border: 'none', cursor: 'pointer',
        }}>{t('Add')}</button>
        <button onClick={() => setExpanded(false)} style={{
          padding: '0.25rem 0.5rem', fontSize: fs.label, borderRadius: '3px',
          background: 'var(--bg-secondary)', color: 'var(--text-secondary)', border: 'none', cursor: 'pointer',
        }}>{t('Cancel')}</button>
      </div>
    </div>
  )
}
