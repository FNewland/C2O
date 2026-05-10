/**
 * modelStore — Zustand cache of the backend design element model.
 *
 * The database owns the model. This store is an optimistic cache:
 * - Edits apply instantly (optimistic update)
 * - API call fires simultaneously
 * - WebSocket broadcasts sync all connected clients
 * - On conflict, rollback to server state
 */
import { create } from 'zustand'

export interface DesignElement {
  id: string
  study_id: string
  parent_id: string | null
  name: string
  element_type: string  // mission|segment|system|subsystem|component|software|mode|logical
  subsystem_domain: string | null
  segment: string  // space|ground|operations
  description: string
  mass_kg: number | null
  power_avg_w: number | null
  power_peak_w: number | null
  volume_cm3: number | null
  dimensions_mm: number[] | null
  cost_nre_keur: number | null
  cost_recurring_keur: number | null
  trl: number | null
  manufacturer: string | null
  kb_component_id: string | null
  quantity: number
  redundancy_type: string | null
  performance: Record<string, any> | null
  margin_percent: number
  owner_position: string | null
  diagram_x: number | null
  diagram_y: number | null
  diagram_collapsed: boolean
  version: number
  children?: DesignElement[]
}

export interface ElementInterface {
  id: string
  study_id: string
  name: string
  interface_type: string  // electrical|data|rf|mechanical|thermal|optical
  direction: string
  from_element_id: string
  to_element_id: string
  properties: Record<string, any> | null
  status: string
  diagram_label: string
  version: number
}

export interface BudgetSummary {
  element_id: string
  element_name: string
  budget_type: string
  allocation: number | null
  sum_nominal: number
  sum_with_margin: number
  remaining: number | null
  margin_pct: number | null
  status: string  // green|amber|red|exceeded|undefined
  lines: { element_id: string; name: string; nominal: number; with_margin: number; quantity: number }[]
}

interface ModelStore {
  // Cached model
  elements: Map<string, DesignElement>
  interfaces: Map<string, ElementInterface>
  loading: boolean
  error: string | null

  // Actions
  loadStudyModel: (studyId: string) => Promise<void>
  createElement: (studyId: string, data: Partial<DesignElement>) => Promise<string | null>
  updateElement: (id: string, changes: Partial<DesignElement>) => Promise<boolean>
  deleteElement: (id: string) => Promise<boolean>
  createInterface: (studyId: string, data: Partial<ElementInterface>) => Promise<string | null>
  deleteInterface: (id: string) => Promise<boolean>

  // WebSocket handler
  handleWsMessage: (msg: any) => void

  // Query helpers
  getChildren: (parentId: string) => DesignElement[]
  getSubtree: (elementId: string) => DesignElement[]
  getElementInterfaces: (elementId: string) => ElementInterface[]
  getRoots: () => DesignElement[]
  getElementsByDomain: (domain: string) => DesignElement[]
  computeBudget: (elementId: string, type: string) => BudgetSummary | null
  computeHierarchicalBudget: (rootId: string, budgetType: string) => number

  // Derived views — replaces flat designStore state
  getArchitectureSelections: () => Record<string, { option_id: string; option_name: string; mass_kg: number; power_w: number; cost_keur: number }>
  getSelectedEquipment: () => Array<{ category: string; componentId: string; name: string; mass_kg: number; power_w: number; cost_keur: number; quantity: number }>

  // Element maturity classification
  getElementMaturity: (elementId: string) => ElementMaturity
}

export type MaturityLevel = 'undefined' | 'parametric' | 'estimated' | 'selected' | 'specified' | 'verified'

export interface ElementMaturity {
  level: MaturityLevel
  label: string
  color: string
  description: string
  completeness: number // 0-100%
  missingFields: string[]
}

const API = '/api'

export const useModelStore = create<ModelStore>((set, get) => ({
  elements: new Map(),
  interfaces: new Map(),
  loading: false,
  error: null,

  loadStudyModel: async (studyId: string) => {
    set({ loading: true, error: null })
    try {
      const res = await fetch(`${API}/studies/${studyId}/elements/tree`)
      if (!res.ok) throw new Error(`${res.status}`)
      const tree = await res.json()

      // Flatten tree into map
      const elements = new Map<string, DesignElement>()
      const flatten = (nodes: any[]) => {
        for (const node of nodes) {
          const { children, ...el } = node
          elements.set(el.id, el)
          if (children?.length) flatten(children)
        }
      }
      flatten(tree)

      // Load interfaces
      const iRes = await fetch(`${API}/studies/${studyId}/interfaces`)
      const ifaces = iRes.ok ? await iRes.json() : []
      const interfaces = new Map<string, ElementInterface>()
      for (const i of ifaces) interfaces.set(i.id, i)

      set({ elements, interfaces, loading: false })
    } catch (e) {
      set({ error: String(e), loading: false })
    }
  },

  createElement: async (studyId, data) => {
    try {
      const res = await fetch(`${API}/elements/?study_id=${studyId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!res.ok) return null
      const el = await res.json()
      set(s => { s.elements.set(el.id, el); return { elements: new Map(s.elements) } })
      return el.id
    } catch { return null }
  },

  updateElement: async (id, changes) => {
    const el = get().elements.get(id)
    if (!el) return false

    // Optimistic update
    const optimistic = { ...el, ...changes, version: el.version + 1 }
    set(s => { s.elements.set(id, optimistic); return { elements: new Map(s.elements) } })

    try {
      const res = await fetch(`${API}/elements/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...changes, version: el.version }),
      })
      if (!res.ok) {
        // Rollback
        set(s => { s.elements.set(id, el); return { elements: new Map(s.elements) } })
        return false
      }
      const updated = await res.json()
      set(s => { s.elements.set(id, updated); return { elements: new Map(s.elements) } })
      return true
    } catch {
      // Rollback
      set(s => { s.elements.set(id, el); return { elements: new Map(s.elements) } })
      return false
    }
  },

  deleteElement: async (id) => {
    // Optimistic delete — remove locally first, then try backend
    set(s => { s.elements.delete(id); return { elements: new Map(s.elements) } })
    try {
      await fetch(`${API}/elements/${id}`, { method: 'DELETE' })
    } catch { /* best-effort backend sync */ }
    return true
  },

  createInterface: async (studyId, data) => {
    try {
      const res = await fetch(`${API}/interfaces/?study_id=${studyId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!res.ok) return null
      const iface = await res.json()
      set(s => { s.interfaces.set(iface.id, iface); return { interfaces: new Map(s.interfaces) } })
      return iface.id
    } catch { return null }
  },

  deleteInterface: async (id) => {
    try {
      const res = await fetch(`${API}/interfaces/${id}`, { method: 'DELETE' })
      if (!res.ok) return false
      set(s => { s.interfaces.delete(id); return { interfaces: new Map(s.interfaces) } })
      return true
    } catch { return false }
  },

  handleWsMessage: (msg) => {
    switch (msg.type) {
      case 'element_created':
        set(s => { s.elements.set(msg.element.id, msg.element); return { elements: new Map(s.elements) } })
        break
      case 'element_updated':
        set(s => {
          const existing = s.elements.get(msg.element_id)
          if (existing) {
            const updated = { ...existing }
            for (const [k, [, newVal]] of Object.entries(msg.changes || {})) {
              (updated as any)[k] = newVal
            }
            s.elements.set(msg.element_id, updated)
          }
          return { elements: new Map(s.elements) }
        })
        break
      case 'element_deleted':
        set(s => { s.elements.delete(msg.element_id); return { elements: new Map(s.elements) } })
        break
      case 'interface_created':
        set(s => { s.interfaces.set(msg.interface.id, msg.interface); return { interfaces: new Map(s.interfaces) } })
        break
      case 'interface_deleted':
        set(s => { s.interfaces.delete(msg.interface_id); return { interfaces: new Map(s.interfaces) } })
        break
    }
  },

  // Query helpers
  getChildren: (parentId) => {
    const result: DesignElement[] = []
    for (const el of get().elements.values()) {
      if (el.parent_id === parentId) result.push(el)
    }
    return result
  },

  getSubtree: (elementId) => {
    const result: DesignElement[] = []
    const visit = (id: string) => {
      for (const el of get().elements.values()) {
        if (el.parent_id === id) {
          result.push(el)
          visit(el.id)
        }
      }
    }
    visit(elementId)
    return result
  },

  getElementInterfaces: (elementId) => {
    const result: ElementInterface[] = []
    for (const iface of get().interfaces.values()) {
      if (iface.from_element_id === elementId || iface.to_element_id === elementId) {
        result.push(iface)
      }
    }
    return result
  },

  getRoots: () => {
    const result: DesignElement[] = []
    for (const el of get().elements.values()) {
      if (!el.parent_id) result.push(el)
    }
    return result
  },

  getElementsByDomain: (domain) => {
    const result: DesignElement[] = []
    for (const el of get().elements.values()) {
      if (el.subsystem_domain === domain) result.push(el)
    }
    return result
  },

  // Derived views — replaces parallel flat state in designStore
  getArchitectureSelections: () => {
    const result: Record<string, { option_id: string; option_name: string; mass_kg: number; power_w: number; cost_keur: number }> = {}
    for (const el of get().elements.values()) {
      if (el.element_type === 'subsystem' && el.subsystem_domain) {
        result[el.subsystem_domain] = {
          option_id: el.id,
          option_name: el.name,
          mass_kg: el.mass_kg || 0,
          power_w: el.power_avg_w || 0,
          cost_keur: el.cost_recurring_keur || 0,
        }
      }
    }
    return result
  },

  getSelectedEquipment: () => {
    const result: Array<{ category: string; componentId: string; name: string; mass_kg: number; power_w: number; cost_keur: number; quantity: number }> = []
    for (const el of get().elements.values()) {
      if (el.element_type === 'component' && el.kb_component_id) {
        result.push({
          category: el.subsystem_domain || 'unknown',
          componentId: el.kb_component_id,
          name: el.name,
          mass_kg: el.mass_kg || 0,
          power_w: el.power_avg_w || 0,
          cost_keur: el.cost_recurring_keur || 0,
          quantity: el.quantity || 1,
        })
      }
    }
    return result
  },

  getElementMaturity: (elementId) => {
    const el = get().elements.get(elementId)
    if (!el) return { level: 'undefined', label: 'Undefined', color: '#6b7280', description: 'Element not found', completeness: 0, missingFields: [] }

    const missing: string[] = []
    if (!el.mass_kg && el.element_type === 'component') missing.push('mass')
    if (!el.power_avg_w && el.element_type === 'component') missing.push('power')
    if (!el.cost_recurring_keur) missing.push('cost')
    if (!el.manufacturer && el.element_type === 'component') missing.push('manufacturer')
    if (!el.trl) missing.push('TRL')
    if (!el.description) missing.push('description')

    // Determine maturity level based on data completeness and source
    let level: MaturityLevel = 'undefined'
    let label = 'Undefined'
    let color = '#6b7280'
    let description = 'No data defined'

    if (el.element_type === 'mission' || el.element_type === 'segment') {
      // Top-level containers — maturity = children completeness
      const children = get().getChildren(el.id)
      if (children.length === 0) {
        level = 'parametric'; label = 'Top-level only'; color = '#f59e0b'
        description = 'Container defined but no children decomposed'
      } else {
        level = 'specified'; label = 'Decomposed'; color = '#3b82f6'
        description = `${children.length} child elements defined`
      }
    } else if (el.element_type === 'system') {
      const children = get().getChildren(el.id)
      if (children.length === 0) {
        level = 'parametric'; label = 'Parametric'; color = '#f59e0b'
        description = 'System defined from parametric model, no subsystems yet'
      } else {
        level = 'specified'; label = 'Architecture set'; color = '#3b82f6'
        description = `${children.length} subsystems defined`
      }
    } else if (el.element_type === 'subsystem') {
      const children = get().getChildren(el.id)
      // Also count orphaned components with matching domain
      if (children.length === 0 && el.subsystem_domain) {
        for (const c of get().elements.values()) {
          if (c.element_type === 'component' && c.subsystem_domain === el.subsystem_domain && !c.parent_id) {
            children.push(c)
          }
        }
      }
      if (children.length === 0 && el.mass_kg) {
        level = 'parametric'; label = 'Parametric'; color = '#f59e0b'
        description = 'Mass/power from parametric estimate, no equipment selected'
      } else if (children.length === 0) {
        level = 'estimated'; label = 'Estimated'; color = '#f97316'
        description = 'Architecture option selected, awaiting equipment'
      } else {
        level = 'selected'; label = 'Equipment selected'; color = '#10b981'
        description = `${children.length} components selected`
      }
    } else if (el.element_type === 'component') {
      if (el.kb_component_id) {
        // From knowledge base — fully specified
        if (missing.length === 0) {
          level = 'specified'; label = 'Fully specified'; color = '#10b981'
          description = `${el.manufacturer || 'COTS'} component, TRL ${el.trl || '?'}`
        } else {
          level = 'selected'; label = 'KB component'; color = '#3b82f6'
          description = `From catalogue, missing: ${missing.join(', ')}`
        }
      } else if (el.mass_kg && el.power_avg_w) {
        level = 'estimated'; label = 'Custom estimate'; color = '#f59e0b'
        description = 'User-defined component, not from catalogue'
      } else {
        level = 'parametric'; label = 'Placeholder'; color = '#f97316'
        description = 'Minimal data — needs specification'
      }
    }

    // Calculate completeness percentage
    const totalFields = 6 // mass, power, cost, manufacturer, TRL, description
    const completeness = Math.round(((totalFields - missing.length) / totalFields) * 100)

    return { level, label, color, description, completeness, missingFields: missing }
  },

  computeHierarchicalBudget: (rootId, budgetType) => {
    const propMap: Record<string, keyof DesignElement> = {
      mass: 'mass_kg', power: 'power_avg_w', cost: 'cost_recurring_keur', volume: 'volume_cm3',
    }
    const prop = propMap[budgetType]
    if (!prop) return 0

    const sumTree = (id: string): number => {
      const children = get().getChildren(id)
      let total = 0
      for (const child of children) {
        if (child.element_type === 'component') {
          total += ((child[prop] as number) || 0) * (child.quantity || 1)
        } else {
          total += sumTree(child.id)  // recurse into subsystems/systems
        }
      }
      return total
    }
    return sumTree(rootId)
  },

  computeBudget: (elementId, type) => {
    const el = get().elements.get(elementId)
    if (!el) return null

    const propMap: Record<string, keyof DesignElement> = {
      mass: 'mass_kg', power: 'power_avg_w', cost: 'cost_recurring_keur', volume: 'volume_cm3',
    }
    const prop = propMap[type]
    if (!prop) return null

    const children = get().getChildren(elementId)
    const lines = children
      .filter(c => (c[prop] as number | null) !== null && (c[prop] as number) > 0)
      .map(c => ({
        element_id: c.id,
        name: c.name,
        nominal: ((c[prop] as number) || 0) * c.quantity,
        with_margin: ((c[prop] as number) || 0) * c.quantity * (1 + c.margin_percent / 100),
        quantity: c.quantity,
      }))

    const sum_nominal = lines.reduce((s, l) => s + l.nominal, 0)
    const sum_with_margin = lines.reduce((s, l) => s + l.with_margin, 0)

    return {
      element_id: elementId,
      element_name: el.name,
      budget_type: type,
      allocation: null, // Would come from BudgetAllocationRow
      sum_nominal: Math.round(sum_nominal * 1000) / 1000,
      sum_with_margin: Math.round(sum_with_margin * 1000) / 1000,
      remaining: null,
      margin_pct: null,
      status: 'undefined',
      lines,
    }
  },
}))
