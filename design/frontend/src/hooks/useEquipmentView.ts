/**
 * useEquipmentView — Merged view of selected equipment from BOTH sources:
 * 1. Element tree (modelStore) — components with kb_component_id
 * 2. Flat store (designStore.selectedEquipment) — legacy/quick selections
 *
 * Element tree takes priority. Flat store provides fallback when tree is sparse.
 * This replaces direct reads of designStore.selectedEquipment in consumers.
 */
import { useMemo } from 'react'
import { useDesignStore } from '../stores/designStore'
import { useModelStore } from '../stores/modelStore'

export interface EquipmentItem {
  category: string
  componentId: string
  name: string
  mass_kg: number
  power_w: number
  cost_keur: number
  quantity: number
  source: 'element_tree' | 'flat_store'
}

export function useEquipmentView(): EquipmentItem[] {
  const flatEquipment = useDesignStore(s => s.selectedEquipment)
  const elements = useModelStore(s => s.elements)

  return useMemo(() => {
    // Collect from element tree
    const treeItems: EquipmentItem[] = []
    const treeComponentIds = new Set<string>()
    for (const el of elements.values()) {
      if (el.element_type === 'component' && el.kb_component_id) {
        treeItems.push({
          category: el.subsystem_domain || 'unknown',
          componentId: el.kb_component_id,
          name: el.name,
          mass_kg: el.mass_kg || 0,
          power_w: el.power_avg_w || 0,
          cost_keur: el.cost_recurring_keur || 0,
          quantity: el.quantity || 1,
          source: 'element_tree',
        })
        treeComponentIds.add(el.kb_component_id)
      }
    }

    // If element tree has components, use those and only add flat-store items not in tree
    if (treeItems.length > 0) {
      for (const eq of (flatEquipment || [])) {
        if (!treeComponentIds.has(eq.componentId)) {
          treeItems.push({ ...eq, source: 'flat_store' })
        }
      }
      return treeItems
    }

    // Fallback: flat store only
    return (flatEquipment || []).map(eq => ({ ...eq, source: 'flat_store' as const }))
  }, [elements, flatEquipment])
}
