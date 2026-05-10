import { useState, useMemo, useEffect } from 'react'
import { useEquipmentSearch } from '../hooks/useSession'
import { useDesignStore } from '../stores/designStore'
import { useModelStore } from '../stores/modelStore'

// All KB component categories, grouped by domain
const CATEGORIES = [
  // Power
  { id: 'batteries', name: 'Batteries', domain: 'power' },
  { id: 'solar_cells', name: 'Solar Cells', domain: 'power' },
  { id: 'solar_panels', name: 'Solar Panels', domain: 'power' },
  { id: 'eps_boards', name: 'EPS Boards', domain: 'power' },
  // AOCS
  { id: 'reaction_wheels', name: 'Reaction Wheels', domain: 'aocs' },
  { id: 'star_trackers', name: 'Star Trackers', domain: 'aocs' },
  { id: 'sun_sensors', name: 'Sun Sensors', domain: 'aocs' },
  { id: 'magnetorquers', name: 'Magnetorquers', domain: 'aocs' },
  // Communications
  { id: 'transponders', name: 'Transponders', domain: 'link' },
  { id: 'antennas', name: 'Antennas', domain: 'link' },
  { id: 'gps_receivers', name: 'GPS Receivers', domain: 'link' },
  // Propulsion
  { id: 'thrusters', name: 'Thrusters', domain: 'propulsion' },
  // Structure & Mechanisms
  { id: 'cubesat_structures', name: 'CubeSat Structures', domain: 'structure' },
  { id: 'deployers', name: 'Deployers', domain: 'structure' },
  { id: 'mechanical_hardware', name: 'Mechanical Hardware', domain: 'structure' },
  // Data handling
  { id: 'obcs', name: 'OBCs', domain: 'data' },
  // Thermal
  { id: 'thermal_hardware', name: 'Thermal Hardware', domain: 'thermal' },
  // Integration
  { id: 'harnesses', name: 'Harnesses & Cables', domain: 'integration' },
  // Ground Segment Equipment
  { id: 'ground_antennas', name: 'Ground Antennas', domain: 'ground_rf' },
  { id: 'ground_rf', name: 'RF Equipment (LNA/HPA)', domain: 'ground_rf' },
  { id: 'ground_baseband', name: 'Modems & Baseband', domain: 'ground_rf' },
  { id: 'ground_software', name: 'MCS/FD Software', domain: 'ground_ops' },
  { id: 'ground_timing', name: 'Timing & Frequency', domain: 'ground_ops' },
]

const DOMAIN_LABELS: Record<string, string> = {
  power: 'Power', aocs: 'AOCS', link: 'Comms', propulsion: 'Propulsion',
  structure: 'Structure', data: 'Data Handling', thermal: 'Thermal', integration: 'Integration',
}

const DOMAIN_COLORS: Record<string, string> = {
  power: '#f59e0b', aocs: '#06b6d4', link: '#ec4899', propulsion: '#f97316',
  structure: '#84cc16', data: '#8b5cf6', thermal: '#ef4444', integration: '#6b7280',
}

// Map each KB category to the parameter edits that selecting a component produces.
const SELECTION_EFFECTS: Record<string, { paramId: string; extract: (c: any) => number | null; label: string }[]> = {
  batteries: [
    { paramId: 'power.battery_capacity_wh', extract: c => c.performance?.capacity_wh ?? null, label: 'Battery Capacity' },
    { paramId: 'power.battery_mass_kg', extract: c => c.mass_kg ?? null, label: 'Battery Mass' },
  ],
  solar_cells: [
    { paramId: 'power.sa_power_eol_w', extract: c => c.performance?.power_w ?? null, label: 'SA Power EOL' },
    { paramId: 'power.sa_mass_kg', extract: c => c.mass_kg ?? null, label: 'SA Mass' },
  ],
  solar_panels: [
    { paramId: 'power.sa_power_eol_w', extract: c => c.performance?.power_w ?? null, label: 'SA Power EOL' },
    { paramId: 'power.sa_mass_kg', extract: c => c.mass_kg ?? null, label: 'SA Mass' },
  ],
  eps_boards: [
    { paramId: 'power.eps_mass_kg', extract: c => c.mass_kg ?? null, label: 'EPS Mass' },
    { paramId: 'power.eps_power_w', extract: c => c.power_w ?? null, label: 'EPS Power' },
  ],
  reaction_wheels: [
    { paramId: 'aocs.mass_kg', extract: c => c.mass_kg ? c.mass_kg * 4 : null, label: 'AOCS Mass (4x wheels)' },
    { paramId: 'aocs.wheel_momentum_nms', extract: c => c.performance?.momentum_nms ?? null, label: 'Wheel Momentum' },
  ],
  star_trackers: [
    { paramId: 'aocs.pointing_accuracy_deg', extract: c => c.performance?.accuracy_arcsec ? c.performance.accuracy_arcsec / 3600 : null, label: 'Pointing Accuracy' },
    { paramId: 'aocs.tracker_mass_kg', extract: c => c.mass_kg ?? null, label: 'Star Tracker Mass' },
  ],
  sun_sensors: [
    { paramId: 'aocs.sun_sensor_mass_kg', extract: c => c.mass_kg ?? null, label: 'Sun Sensor Mass' },
  ],
  magnetorquers: [
    { paramId: 'aocs.magnetorquer_mass_kg', extract: c => c.mass_kg ? c.mass_kg * 3 : null, label: 'Magnetorquer Mass (3-axis)' },
  ],
  transponders: [
    { paramId: 'link.ttc_mass_kg', extract: c => c.mass_kg ?? null, label: 'TTC Mass' },
    { paramId: 'link.ttc_power_w', extract: c => c.power_w ?? null, label: 'TTC Power' },
  ],
  antennas: [
    { paramId: 'link.antenna_mass_kg', extract: c => c.mass_kg ?? null, label: 'Antenna Mass' },
  ],
  gps_receivers: [
    { paramId: 'link.gps_mass_kg', extract: c => c.mass_kg ?? null, label: 'GPS Mass' },
    { paramId: 'link.gps_power_w', extract: c => c.power_w ?? null, label: 'GPS Power' },
  ],
  thrusters: [
    { paramId: 'propulsion.isp_s', extract: c => c.performance?.isp_s ?? null, label: 'Isp' },
    { paramId: 'propulsion.total_mass_kg', extract: c => c.mass_kg ?? null, label: 'Thruster Mass' },
  ],
  cubesat_structures: [
    { paramId: 'structure.mass_kg', extract: c => c.mass_kg ?? null, label: 'Structure Mass' },
  ],
  deployers: [
    { paramId: 'structure.deployer_mass_kg', extract: c => c.mass_kg ?? null, label: 'Deployer Mass' },
  ],
  obcs: [
    { paramId: 'data.obc_mass_kg', extract: c => c.mass_kg ?? null, label: 'OBC Mass' },
    { paramId: 'data.obc_power_w', extract: c => c.power_w ?? null, label: 'OBC Power' },
  ],
  thermal_hardware: [
    { paramId: 'thermal.hardware_mass_kg', extract: c => c.mass_kg ?? null, label: 'Thermal HW Mass' },
  ],
  harnesses: [
    { paramId: 'integration.harness_mass_kg', extract: c => c.mass_kg ?? null, label: 'Harness Mass' },
  ],
  mechanical_hardware: [
    { paramId: 'structure.hardware_mass_kg', extract: c => c.mass_kg ?? null, label: 'Mechanical HW Mass' },
  ],
}

interface SelectedEquipment {
  category: string
  component: any
  quantity: number
  timestamp: number
}

interface Props {
  studyId: string | null
  onClose: () => void
  onSelect: (category: string, component: any) => void
  mode?: 'modal' | 'inline'  // inline skips the fixed overlay
}

export function EquipmentBrowser({ studyId, onClose, onSelect, mode = 'modal' }: Props) {
  // SYSTEM-V: Filter categories based on subsystems defined in the element tree
  const modelElements = useModelStore(s => s.elements)
  const definedDomains = useMemo(() => {
    const domains = new Set<string>()
    for (const el of modelElements.values()) {
      if (el.element_type === 'subsystem' && el.subsystem_domain) {
        domains.add(el.subsystem_domain)
      }
    }
    return domains
  }, [modelElements])

  // Map equipment categories to subsystem domains
  const categoryToDomain: Record<string, string> = {
    batteries: 'power', solar_cells: 'power', solar_panels: 'power', eps_boards: 'power',
    reaction_wheels: 'aocs', star_trackers: 'aocs', sun_sensors: 'aocs', magnetorquers: 'aocs',
    transponders: 'ttc', antennas: 'ttc', gps_receivers: 'obc',
    thrusters: 'propulsion', cubesat_structures: 'structure', deployers: 'structure', mechanical_hardware: 'structure',
    obcs: 'obc', thermal_hardware: 'thermal', harnesses: 'structure',
    ground_antennas: 'ground', ground_rf: 'ground', ground_baseband: 'ground', ground_software: 'ground', ground_timing: 'ground',
  }

  // Filter categories to only show those whose domain exists in the element tree
  // If no subsystems defined yet, show all (don't block the user)
  const filteredCategories = definedDomains.size > 0
    ? CATEGORIES.filter(c => definedDomains.has(categoryToDomain[c.id] || '') || !categoryToDomain[c.id])
    : CATEGORIES

  const [activeCategory, setActiveCategory] = useState<string>(filteredCategories[0]?.id || 'batteries')
  const [sortKey, setSortKey] = useState<'fit' | 'mass' | 'cost' | 'trl'>('fit')
  // Key = category:componentId to allow multiple per category
  const [selections, setSelections] = useState<Map<string, SelectedEquipment>>(new Map())
  const [compareMode, setCompareMode] = useState(false)
  const [compareIds, setCompareIds] = useState<Set<string>>(new Set())
  const [showCustomForm, setShowCustomForm] = useState(false)
  const [customComp, setCustomComp] = useState({ name: '', manufacturer: '', mass_kg: 0, power_w: 0, cost_keur: 0, trl: 5, notes: '' })

  // Equipment needs from requirements analysis
  const [needs, setNeeds] = useState<Record<string, { required: boolean; reason: string; quantity: number }>>({})
  useEffect(() => {
    if (!studyId) return
    fetch(`/api/engineering/equipment/needs/${studyId}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data?.needs) {
          const map: Record<string, { required: boolean; reason: string; quantity: number }> = {}
          for (const n of data.needs) map[n.category] = { required: n.required, reason: n.reason, quantity: n.quantity }
          setNeeds(map)
        }
      })
      .catch(() => {})
  }, [studyId])

  // Load components for the active category's domain
  const activeDomain = CATEGORIES.find(c => c.id === activeCategory)?.domain || 'power'
  const { data, isLoading, error } = useEquipmentSearch(activeDomain, studyId)

  // Handle multiple response formats: {categories: {cat: [...]}} or {components: [...]} or [{component, fit_score}]
  const rawData = data as any
  let categories: Record<string, any[]> = {}
  if (rawData?.categories) {
    categories = rawData.categories
  } else if (rawData?.components) {
    // Flat list — group by active category
    categories[activeCategory] = rawData.components.map((c: any) => ({ component: c, fit_score: 0.5 }))
  } else if (Array.isArray(rawData)) {
    categories[activeCategory] = rawData
  }
  const selectedRfBand = useDesignStore(s => s.selectedRfBand)

  // Filter transponders/antennas by selected RF band if set
  let activeRows = categories[activeCategory] || []
  if (selectedRfBand && (activeCategory === 'transponders' || activeCategory === 'antennas')) {
    activeRows = activeRows.filter((row: any) => {
      const c = row.component || row
      const name = (c.name || '').toUpperCase()
      const band = (c.frequency_band || c.band || '').toUpperCase()
      const bandLabel = selectedRfBand.toUpperCase()
      return band.includes(bandLabel) || name.includes(bandLabel + '-BAND') || name.includes(bandLabel + ' BAND') || !band // Show if band unknown
    })
  }

  const sortRows = (rows: any[]) => {
    return [...rows].sort((a, b) => {
      const ca = a.component || a
      const cb = b.component || b
      switch (sortKey) {
        case 'mass': return (ca.mass_kg || 0) - (cb.mass_kg || 0)
        case 'cost': return (ca.cost_keur || 999999) - (cb.cost_keur || 999999)
        case 'trl': return (cb.trl || 0) - (ca.trl || 0)
        default: return (b.fit_score || 0) - (a.fit_score || 0)
      }
    })
  }

  // Check RF band compatibility between selected transponders and antennas
  const checkRfCompatibility = (category: string, component: any): string | null => {
    const getBand = (c: any): string | null => {
      const b = c.frequency_band || c.band || c.performance?.frequency_band || ''
      if (b) return b.toUpperCase().replace('-BAND', '').trim()
      const name = (c.name || '').toUpperCase()
      for (const band of ['UHF', 'VHF', 'S', 'X', 'KA', 'L']) {
        if (name.includes(band + '-BAND') || name.includes(band + ' BAND') || name.includes(band + 'BAND')) return band
      }
      return null
    }

    if (category === 'antennas') {
      const antBand = getBand(component)
      for (const [, sel] of selections) {
        if (sel.category === 'transponders') {
          const txBand = getBand(sel.component)
          if (txBand && antBand && txBand !== antBand) {
            return `Incompatible: this ${antBand}-band antenna won't work with selected ${txBand}-band transponder "${sel.component.name}"`
          }
        }
      }
    }
    if (category === 'transponders') {
      const txBand = getBand(component)
      for (const [, sel] of selections) {
        if (sel.category === 'antennas') {
          const antBand = getBand(sel.component)
          if (txBand && antBand && txBand !== antBand) {
            return `Incompatible: this ${txBand}-band transponder won't work with selected ${antBand}-band antenna "${sel.component.name}"`
          }
        }
      }
    }
    return null
  }

  const handleSelectComponent = (category: string, component: any, qty: number = 1) => {
    // Check RF compatibility before allowing selection
    const warning = checkRfCompatibility(category, component)
    if (warning) {
      if (!confirm(`⚠ ${warning}\n\nSelect anyway?`)) return
    }

    const key = `${category}:${component.id || component.name}`
    setSelections(prev => {
      const next = new Map(prev)
      const existing = next.get(key)
      if (existing) {
        // Already selected — do nothing (use qty input to change quantity)
        return prev
      } else {
        next.set(key, { category, component, quantity: qty, timestamp: Date.now() })
      }
      return next
    })
  }

  const handleQuantityChange = (key: string, qty: number) => {
    setSelections(prev => {
      const next = new Map(prev)
      const existing = next.get(key)
      if (existing) next.set(key, { ...existing, quantity: Math.max(1, qty) })
      return next
    })
  }

  const handleDeselectItem = (key: string) => {
    setSelections(prev => {
      const next = new Map(prev)
      next.delete(key)
      return next
    })
  }

  // Live budget totals
  const budgetTotals = useMemo(() => {
    let mass = 0, power = 0, cost = 0
    for (const [, sel] of selections) {
      mass += (sel.component.mass_kg || 0) * sel.quantity
      power += (sel.component.power_w || 0) * sel.quantity
      cost += (sel.component.cost_keur || 0) * sel.quantity
    }
    return { mass, power, cost }
  }, [selections])

  // Legacy: remove all selections for a category
  const handleDeselectCategory = (category: string) => {
    setSelections(prev => {
      const next = new Map(prev)
      for (const [key, sel] of next) {
        if (sel.category === category) next.delete(key)
      }
      return next
    })
  }

  // SYSTEM-V: Currently installed components from element tree (removable)
  const deleteElement = useModelStore(s => s.deleteElement)
  const installedComponents = useMemo(() => {
    const result: Array<{ id: string; name: string; domain: string; mass_kg: number; power_w: number; cost_keur: number; quantity: number; kb_component_id: string | null }> = []
    for (const el of modelElements.values()) {
      if (el.element_type === 'component') {
        result.push({
          id: el.id, name: el.name, domain: el.subsystem_domain || 'unknown',
          mass_kg: el.mass_kg || 0, power_w: el.power_avg_w || 0,
          cost_keur: el.cost_recurring_keur || 0, quantity: el.quantity || 1,
          kb_component_id: el.kb_component_id,
        })
      }
    }
    return result
  }, [modelElements])

  const handleRemoveInstalled = async (elementId: string, name: string) => {
    if (!confirm(`Remove ${name} from the design?`)) return
    await deleteElement(elementId)
    // Also remove from flat designStore
    const existing = useDesignStore.getState().selectedEquipment
    useDesignStore.setState({
      selectedEquipment: existing.filter(e => e.name !== name),
    })
    useDesignStore.getState().markStale('equipment')
  }

  const handleApplyAll = () => {
    for (const [category, sel] of selections) {
      onSelect(category, sel.component)
    }
  }

  const handleApplyAndClose = () => {
    for (const [category, sel] of selections) {
      onSelect(category, sel.component)
    }
    onClose()
  }

  const toggleCompare = (id: string) => {
    setCompareIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else if (next.size < 3) next.add(id)
      return next
    })
  }

  const handleCustomSubmit = () => {
    const comp = {
      id: `custom-${Date.now()}`,
      ...customComp,
      heritage_missions: [],
      performance: {},
      custom: true,
    }
    handleSelectComponent(activeCategory, comp)
    setShowCustomForm(false)
    setCustomComp({ name: '', manufacturer: '', mass_kg: 0, power_w: 0, cost_keur: 0, trl: 5, notes: '' })
  }

  // Check if a specific component is selected in the active category
  const selectedIds = new Set(
    Array.from(selections.values())
      .filter(s => s.category === activeCategory)
      .map(s => s.component.id || s.component.name)
  )
  const categorySelectionCount = Array.from(selections.values()).filter(s => s.category === activeCategory).length

  // Items for comparison
  const compareItems = useMemo(() => {
    if (!compareMode || compareIds.size === 0) return []
    return activeRows.filter(r => {
      const c = r.component || r
      return compareIds.has(c.id || c.name)
    })
  }, [compareMode, compareIds, activeRows])

  // Group categories by domain for sidebar
  const groupedCategories = useMemo(() => {
    const groups: Record<string, typeof CATEGORIES> = {}
    for (const cat of filteredCategories) {
      if (!groups[cat.domain]) groups[cat.domain] = []
      groups[cat.domain].push(cat)
    }
    return groups
  }, [])

  const innerContent = (
      <div style={{
        background: 'var(--bg-primary, #111827)', border: mode === 'modal' ? '1px solid var(--border, #374151)' : 'none',
        borderRadius: mode === 'modal' ? '8px' : '0', width: '100%', maxWidth: mode === 'modal' ? '1200px' : 'none',
        maxHeight: mode === 'modal' ? '90vh' : '100%', height: mode === 'inline' ? '100%' : 'auto',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
      } as React.CSSProperties} onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div style={{
          padding: '0.6rem 1rem', borderBottom: '1px solid var(--border, #374151)',
          display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap',
        }}>
          <h2 style={{ fontSize: '1rem', margin: 0 }}>Equipment Browser</h2>
          <span style={{ fontSize: '0.68rem', color: '#6b7280' }}>
            {filteredCategories.length} categories · {activeRows.length} components
          </span>
          <span style={{ fontSize: '0.6rem', padding: '0.1rem 0.4rem', background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.3)', borderRadius: '3px', color: '#93c5fd' }}>
            Filtered by architecture selections
          </span>
          <div style={{ flex: 1 }} />
          <button className="btn btn-sm" onClick={() => { setCompareMode(!compareMode); setCompareIds(new Set()) }}
            style={{ fontSize: '0.7rem', background: compareMode ? '#8b5cf6' : undefined }}>
            {compareMode ? 'Exit Compare' : 'Compare'}
          </button>
          <button className="btn btn-sm" onClick={() => setShowCustomForm(!showCustomForm)}
            style={{ fontSize: '0.7rem', background: showCustomForm ? '#f59e0b' : undefined }}>
            {showCustomForm ? 'Cancel Custom' : 'Design Custom'}
          </button>
          <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
            {selections.size} of {filteredCategories.length} selected
          </span>
          {selections.size > 0 && (
            <>
              <button className="btn btn-sm" onClick={handleApplyAll}
                style={{ background: '#10b981', fontSize: '0.75rem' }}>
                Apply {selections.size} Selection{selections.size !== 1 ? 's' : ''}
              </button>
              <button className="btn btn-sm" onClick={handleApplyAndClose}
                style={{ background: '#3b82f6', fontSize: '0.75rem' }}>
                Apply & Close
              </button>
            </>
          )}
          <button className="btn btn-sm" onClick={onClose}>Close</button>
        </div>

        {/* Selected equipment summary bar with live budget */}
        {selections.size > 0 && (
          <div style={{
            padding: '0.5rem 1rem', background: 'rgba(16,185,129,0.08)',
            borderBottom: '1px solid var(--border, #374151)',
          }}>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '0.3rem' }}>
              <span style={{ fontSize: '0.72rem', color: '#10b981', fontWeight: 600 }}>Selected:</span>
              {Array.from(selections.entries()).map(([key, sel]) => (
                <span key={key} style={{
                  display: 'inline-flex', alignItems: 'center', gap: '0.3rem',
                  background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)',
                  borderRadius: '4px', padding: '0.15rem 0.5rem', fontSize: '0.72rem',
                }}>
                  <span style={{ color: '#9ca3af', fontSize: '0.6rem' }}>{sel.category.replace(/_/g, ' ')}</span>
                  <span style={{ fontWeight: 600, color: '#10b981' }}>{sel.component.name}</span>
                  <input type="number" min={1} max={10} value={sel.quantity}
                    onChange={e => handleQuantityChange(key, Number(e.target.value))}
                    style={{ width: 30, background: 'transparent', border: '1px solid #374151', borderRadius: '3px', color: '#d1d5db', fontSize: '0.65rem', textAlign: 'center', padding: '0 2px' }}
                    onClick={e => e.stopPropagation()} />
                  <span style={{ color: '#6b7280', fontSize: '0.65rem' }}>{((sel.component.mass_kg || 0) * sel.quantity).toFixed(2)}kg</span>
                  {sel.component.custom && <span style={{ fontSize: '0.6rem', color: '#f59e0b' }}>(custom)</span>}
                  <button onClick={() => handleDeselectItem(key)}
                    style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.8rem', padding: 0, lineHeight: 1 }}>
                    x
                  </button>
                </span>
              ))}
            </div>
            {/* Live budget totals */}
            <div style={{ display: 'flex', gap: '1rem', fontSize: '0.7rem' }}>
              <span style={{ color: '#9ca3af' }}>Budget impact:</span>
              <span style={{ fontFamily: 'monospace', color: '#d1d5db' }}>{budgetTotals.mass.toFixed(2)} kg</span>
              <span style={{ fontFamily: 'monospace', color: '#d1d5db' }}>{budgetTotals.power.toFixed(1)} W</span>
              <span style={{ fontFamily: 'monospace', color: '#d1d5db' }}>{budgetTotals.cost.toFixed(0)} kEUR</span>
            </div>
          </div>
        )}

        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          {/* Category sidebar — grouped by domain */}
          <div style={{
            width: '180px', borderRight: '1px solid var(--border, #374151)',
            overflowY: 'auto', flexShrink: 0,
          }}>
            {Object.entries(groupedCategories).map(([domain, cats]) => (
              <div key={domain}>
                <div style={{
                  fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase',
                  color: DOMAIN_COLORS[domain] || '#6b7280', padding: '0.5rem 0.75rem 0.15rem',
                  letterSpacing: '0.05em',
                }}>{DOMAIN_LABELS[domain] || domain}</div>
                {cats.map(cat => {
                  const isActive = activeCategory === cat.id
                  const hasSelection = Array.from(selections.values()).some(s => s.category === cat.id)
                  const need = needs[cat.id]
                  const isNeeded = need?.required
                  const isOptional = need && !need.required
                  const notNeeded = Object.keys(needs).length > 0 && !need
                  return (
                    <button key={cat.id} onClick={() => setActiveCategory(cat.id)}
                      title={need?.reason || ''}
                      style={{
                        display: 'flex', alignItems: 'center', gap: '0.4rem', width: '100%',
                        padding: '0.4rem 0.75rem', border: 'none', cursor: 'pointer', textAlign: 'left',
                        background: isActive ? 'var(--bg-secondary, #1f2937)' : 'transparent',
                        borderLeft: isActive ? `3px solid ${DOMAIN_COLORS[cat.domain] || '#3b82f6'}` : '3px solid transparent',
                        fontSize: '0.78rem',
                        color: notNeeded ? '#4b5563' : isActive ? '#f3f4f6' : '#9ca3af',
                        opacity: notNeeded ? 0.5 : 1,
                      }}>
                      {hasSelection ? (
                        <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981', flexShrink: 0 }} />
                      ) : isNeeded ? (
                        <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#3b82f6', flexShrink: 0 }} title="Required" />
                      ) : isOptional ? (
                        <span style={{ width: 8, height: 8, borderRadius: '50%', border: '1.5px solid #6b7280', flexShrink: 0 }} title="Optional" />
                      ) : null}
                      <span style={{ flex: 1 }}>{cat.name}</span>
                      {need && <span style={{ fontSize: '0.6rem', color: '#6b7280' }}>×{need.quantity}</span>}
                    </button>
                  )
                })}
              </div>
            ))}
          </div>

          {/* Component table + custom form + compare view */}
          <div style={{ flex: 1, overflow: 'auto', padding: '0.75rem' }}>
            {/* Custom equipment form */}
            {showCustomForm && (
              <div style={{
                padding: '0.75rem', background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.3)',
                borderRadius: '6px', marginBottom: '0.75rem',
              }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#f59e0b', marginBottom: '0.4rem' }}>
                  Design Custom Component — {CATEGORIES.find(c => c.id === activeCategory)?.name}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.4rem', marginBottom: '0.4rem' }}>
                  <div>
                    <label style={formLabel}>Name</label>
                    <input className="input" value={customComp.name} onChange={e => setCustomComp(p => ({ ...p, name: e.target.value }))} placeholder="Custom component name" style={{ fontSize: '0.75rem', width: '100%' }} />
                  </div>
                  <div>
                    <label style={formLabel}>Manufacturer</label>
                    <input className="input" value={customComp.manufacturer} onChange={e => setCustomComp(p => ({ ...p, manufacturer: e.target.value }))} placeholder="In-house / vendor" style={{ fontSize: '0.75rem', width: '100%' }} />
                  </div>
                  <div>
                    <label style={formLabel}>TRL</label>
                    <input className="input" type="number" min={1} max={9} value={customComp.trl} onChange={e => setCustomComp(p => ({ ...p, trl: Number(e.target.value) }))} style={{ fontSize: '0.75rem', width: '100%' }} />
                  </div>
                  <div>
                    <label style={formLabel}>Mass (kg)</label>
                    <input className="input" type="number" step={0.01} value={customComp.mass_kg} onChange={e => setCustomComp(p => ({ ...p, mass_kg: Number(e.target.value) }))} style={{ fontSize: '0.75rem', width: '100%' }} />
                  </div>
                  <div>
                    <label style={formLabel}>Power (W)</label>
                    <input className="input" type="number" step={0.1} value={customComp.power_w} onChange={e => setCustomComp(p => ({ ...p, power_w: Number(e.target.value) }))} style={{ fontSize: '0.75rem', width: '100%' }} />
                  </div>
                  <div>
                    <label style={formLabel}>Cost (kEUR)</label>
                    <input className="input" type="number" step={1} value={customComp.cost_keur} onChange={e => setCustomComp(p => ({ ...p, cost_keur: Number(e.target.value) }))} style={{ fontSize: '0.75rem', width: '100%' }} />
                  </div>
                </div>
                <input className="input" value={customComp.notes} onChange={e => setCustomComp(p => ({ ...p, notes: e.target.value }))}
                  placeholder="Notes (interface details, performance specs, rationale...)" style={{ fontSize: '0.72rem', width: '100%', marginBottom: '0.4rem' }} />
                <button className="btn btn-sm" onClick={handleCustomSubmit} disabled={!customComp.name}
                  style={{ background: '#f59e0b', fontSize: '0.72rem' }}>Add Custom to Selection</button>
              </div>
            )}

            {/* Compare view */}
            {compareMode && compareIds.size >= 2 && (
              <div style={{
                padding: '0.75rem', background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.3)',
                borderRadius: '6px', marginBottom: '0.75rem',
              }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#8b5cf6', marginBottom: '0.4rem' }}>
                  Side-by-Side Comparison ({compareIds.size} components)
                </div>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
                  <thead>
                    <tr style={{ background: 'rgba(139,92,246,0.1)' }}>
                      <th style={th}>Parameter</th>
                      {compareItems.map(r => {
                        const c = r.component || r
                        return <th key={c.id || c.name} style={{ ...th, textAlign: 'center' }}>{c.name}</th>
                      })}
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { label: 'Manufacturer', get: (c: any) => c.manufacturer || '—' },
                      { label: 'Mass (kg)', get: (c: any) => c.mass_kg?.toFixed(3) || '—', best: 'min' },
                      { label: 'Power (W)', get: (c: any) => c.power_w?.toFixed(1) || '—', best: 'min' },
                      { label: 'Cost (kEUR)', get: (c: any) => c.cost_keur?.toFixed(0) || '—', best: 'min' },
                      { label: 'TRL', get: (c: any) => String(c.trl || '—'), best: 'max' },
                      { label: 'Heritage', get: (c: any) => (c.heritage_missions || []).join(', ') || 'None' },
                      { label: 'Fit Score', get: (c: any, r: any) => r.fit_score !== undefined ? `${(r.fit_score * 100).toFixed(0)}%` : '—', best: 'max' },
                    ].map(row => {
                      const values = compareItems.map(r => {
                        const c = r.component || r
                        return { val: row.get(c, r), num: parseFloat(row.get(c, r)) }
                      })
                      const nums = values.map(v => v.num).filter(n => !isNaN(n))
                      const bestVal = row.best === 'min' ? Math.min(...nums) : row.best === 'max' ? Math.max(...nums) : null
                      return (
                        <tr key={row.label} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                          <td style={{ ...td, fontWeight: 600, color: '#9ca3af' }}>{row.label}</td>
                          {values.map((v, i) => (
                            <td key={i} style={{
                              ...td, textAlign: 'center', fontFamily: 'monospace',
                              color: bestVal !== null && v.num === bestVal ? '#10b981' : '#d1d5db',
                              fontWeight: bestVal !== null && v.num === bestVal ? 700 : 400,
                            }}>{v.val}</td>
                          ))}
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {/* Currently installed components from element tree */}
            {installedComponents.length > 0 && (
              <div style={{
                padding: '0.5rem 0.75rem', marginBottom: '0.75rem', borderRadius: '6px',
                background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.2)',
              }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#93c5fd', marginBottom: '0.3rem' }}>
                  Installed Components ({installedComponents.length})
                </div>
                <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
                  {installedComponents.map(comp => (
                    <span key={comp.id} style={{
                      display: 'inline-flex', alignItems: 'center', gap: '0.25rem',
                      background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)',
                      borderRadius: '4px', padding: '0.15rem 0.5rem', fontSize: '0.68rem',
                    }}>
                      <span style={{ color: '#6b7280', fontSize: '0.6rem' }}>{comp.domain}</span>
                      <span style={{ fontWeight: 500, color: '#93c5fd' }}>{comp.name}</span>
                      <span style={{ color: '#6b7280', fontSize: '0.6rem' }}>
                        {comp.mass_kg.toFixed(2)}kg · {comp.power_w.toFixed(1)}W
                        {comp.quantity > 1 && ` ×${comp.quantity}`}
                      </span>
                      <button onClick={() => handleRemoveInstalled(comp.id, comp.name)}
                        style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.8rem', padding: 0, lineHeight: 1 }}
                        title="Remove from design">
                        ×
                      </button>
                    </span>
                  ))}
                </div>
                <div style={{ fontSize: '0.65rem', color: '#6b7280', marginTop: '0.25rem' }}>
                  Total: {installedComponents.reduce((s, c) => s + c.mass_kg * c.quantity, 0).toFixed(2)} kg
                  · {installedComponents.reduce((s, c) => s + c.power_w * c.quantity, 0).toFixed(1)} W
                  · {installedComponents.reduce((s, c) => s + c.cost_keur * c.quantity, 0).toFixed(0)} kEUR
                </div>
              </div>
            )}

            {/* Sort controls */}
            <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.5rem', alignItems: 'center' }}>
              <span style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Sort:</span>
              {(['fit', 'mass', 'cost', 'trl'] as const).map(k => (
                <button key={k} onClick={() => setSortKey(k)}
                  style={{
                    background: sortKey === k ? 'var(--accent, #3b82f6)' : 'transparent',
                    color: sortKey === k ? 'white' : '#9ca3af',
                    border: '1px solid var(--border, #374151)', borderRadius: '4px',
                    padding: '0.15rem 0.45rem', fontSize: '0.68rem', cursor: 'pointer', textTransform: 'uppercase',
                  }}
                >{k}</button>
              ))}
              {compareMode && <span style={{ fontSize: '0.68rem', color: '#8b5cf6', marginLeft: '0.5rem' }}>Click rows to compare (max 3)</span>}
            </div>

            {isLoading && <div className="loading"><div className="spinner" /> Loading...</div>}
            {error && <div className="warning-item">Failed to load: {String(error)}</div>}

            {activeRows.length > 0 && (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-secondary, #1f2937)' }}>
                    {compareMode && <th style={th}>Cmp</th>}
                    <th style={th}>Name</th>
                    <th style={th}>Manufacturer</th>
                    <th style={th}>Mass (kg)</th>
                    <th style={th}>Power (W)</th>
                    <th style={th}>Cost (kEUR)</th>
                    <th style={th}>TRL</th>
                    <th style={th}>Heritage</th>
                    <th style={th}>Fit</th>
                    <th style={th}>Req Status</th>
                    <th style={th}></th>
                  </tr>
                </thead>
                <tbody>
                  {sortRows(activeRows).map((row: any) => {
                    const c = row.component || row
                    const id = c.id || c.name
                    const heritage = Array.isArray(c.heritage_missions) ? c.heritage_missions.join(', ') : ''
                    const isChosen = selectedIds.has(id)
                    const isComparing = compareIds.has(id)
                    const notes: string[] = row.notes || []
                    const hasGaps = notes.some((n: string) => n.includes('BELOW'))
                    const meetsAll = notes.length > 0 && !hasGaps
                    return (
                      <tr key={id}
                        onClick={compareMode ? () => toggleCompare(id) : undefined}
                        style={{
                          background: isChosen ? 'rgba(16,185,129,0.12)' : isComparing ? 'rgba(139,92,246,0.1)' : 'transparent',
                          borderBottom: '1px solid rgba(255,255,255,0.05)',
                          cursor: compareMode ? 'pointer' : 'default',
                        }}>
                        {compareMode && (
                          <td style={td}>
                            <input type="checkbox" checked={isComparing} readOnly
                              style={{ accentColor: '#8b5cf6' }} />
                          </td>
                        )}
                        <td style={td}>
                          <div style={{ fontWeight: 600 }}>{c.name}</div>
                          <div style={{ fontSize: '0.65rem', color: '#9ca3af' }}>{id}</div>
                        </td>
                        <td style={td}>{c.manufacturer || '—'}</td>
                        <td style={tdNum}>{c.mass_kg?.toFixed(3) || '—'}</td>
                        <td style={tdNum}>{c.power_w?.toFixed(1) || '—'}</td>
                        <td style={tdNum}>{c.cost_keur?.toFixed(0) || '—'}</td>
                        <td style={tdNum}>{c.trl || '—'}</td>
                        <td style={{ ...td, fontSize: '0.68rem', maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {heritage || '—'}
                        </td>
                        <td style={tdNum}>
                          {row.fit_score !== undefined && (
                            <span style={{
                              padding: '0.1rem 0.35rem', borderRadius: '3px', fontSize: '0.68rem', fontWeight: 600,
                              background: fitColor(row.fit_score, 0.2), color: fitColor(row.fit_score, 1),
                            }}>{(row.fit_score * 100).toFixed(0)}%</span>
                          )}
                        </td>
                        <td style={td}>
                          {hasGaps ? (
                            <span title={notes.filter((n: string) => n.includes('BELOW')).join('\n')}
                              style={{ fontSize: '0.68rem', padding: '0.1rem 0.35rem', borderRadius: '3px', background: 'rgba(239,68,68,0.15)', color: '#ef4444', cursor: 'help' }}>
                              {notes.filter((n: string) => n.includes('BELOW')).length} gap{notes.filter((n: string) => n.includes('BELOW')).length !== 1 ? 's' : ''}
                            </span>
                          ) : meetsAll ? (
                            <span style={{ fontSize: '0.68rem', padding: '0.1rem 0.35rem', borderRadius: '3px', background: 'rgba(16,185,129,0.15)', color: '#10b981' }}>
                              meets
                            </span>
                          ) : (
                            <span style={{ fontSize: '0.68rem', color: '#6b7280' }}>—</span>
                          )}
                        </td>
                        <td style={td}>
                          {!compareMode && (
                            isChosen ? (
                              <span style={{ color: '#10b981', fontWeight: 600, fontSize: '0.72rem' }}>Selected</span>
                            ) : (
                              <button className="btn btn-sm"
                                onClick={() => handleSelectComponent(activeCategory, c)}
                                style={{ padding: '0.18rem 0.55rem', fontSize: '0.7rem' }}
                              >Select</button>
                            )
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}

            {!isLoading && activeRows.length === 0 && (
              <div style={{ color: '#6b7280', fontSize: '0.8rem', padding: '1rem' }}>
                No components in this category. Try a different domain search or design a custom component.
              </div>
            )}

            {/* Show what selecting this component would do */}
            {selections.has(activeCategory) && (
              <div style={{
                marginTop: '0.75rem', padding: '0.5rem 0.75rem', borderRadius: '6px',
                background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)',
              }}>
                <div style={{ fontSize: '0.72rem', color: '#10b981', fontWeight: 600, marginBottom: '0.3rem' }}>
                  Parameters affected by {selections.get(activeCategory)!.component.name}:
                </div>
                {(SELECTION_EFFECTS[activeCategory] || []).map(eff => {
                  const val = eff.extract(selections.get(activeCategory)!.component)
                  return val !== null ? (
                    <div key={eff.paramId} style={{ fontSize: '0.72rem', color: '#9ca3af' }}>
                      <span style={{ fontFamily: 'monospace' }}>{eff.paramId}</span> = <strong style={{ color: '#10b981' }}>{typeof val === 'number' ? val.toFixed(3) : val}</strong>
                      <span style={{ color: '#6b7280' }}> ({eff.label})</span>
                    </div>
                  ) : null
                })}
              </div>
            )}
          </div>
        </div>
      </div>
  )

  if (mode === 'inline') return innerContent

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
      zIndex: 9000, display: 'flex', alignItems: 'center', justifyContent: 'center',
    }} onClick={onClose}>
      {innerContent}
    </div>
  )
}

const formLabel: React.CSSProperties = { display: 'block', fontSize: '0.65rem', color: '#9ca3af', marginBottom: '0.15rem', textTransform: 'uppercase', letterSpacing: '0.03em' }
const th: React.CSSProperties = { padding: '0.35rem 0.5rem', textAlign: 'left', fontSize: '0.68rem', textTransform: 'uppercase', color: '#9ca3af', letterSpacing: '0.03em' }
const td: React.CSSProperties = { padding: '0.35rem 0.5rem', verticalAlign: 'top' }
const tdNum: React.CSSProperties = { ...td, textAlign: 'right', fontFamily: 'monospace', fontVariantNumeric: 'tabular-nums' }

function fitColor(score: number, alpha: number): string {
  if (score > 0.7) return `rgba(16,185,129,${alpha})`
  if (score > 0.4) return `rgba(245,158,11,${alpha})`
  return `rgba(239,68,68,${alpha})`
}
