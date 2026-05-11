/**
 * useEquipmentView — View of selected equipment from the element tree.
 *
 * Single source of truth: components in modelStore with kb_component_id.
 */
import { useMemo } from 'react'
import { useModelStore } from '../stores/modelStore'

export interface EquipmentItem {
  category: string
  componentId: string
  name: string
  mass_kg: number
  power_w: number
  cost_keur: number
  quantity: number
  source: 'element_tree'
}

export function useEquipmentView(): EquipmentItem[] {
  const elements = useModelStore(s => s.elements)

  return useMemo(() => {
    const items: EquipmentItem[] = []
    for (const el of elements.values()) {
      if (el.element_type === 'component' && el.kb_component_id) {
        items.push({
          category: el.subsystem_domain || 'unknown',
          componentId: el.kb_component_id,
          name: el.name,
          mass_kg: el.mass_kg || 0,
          power_w: el.power_avg_w || 0,
          cost_keur: el.cost_recurring_keur || 0,
          quantity: el.quantity || 1,
          source: 'element_tree',
        })
      }
    }
    return items
  }, [elements])
}
