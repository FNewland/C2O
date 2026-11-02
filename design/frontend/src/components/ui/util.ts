/** Non-component helpers shared by the C2O primitives (kept apart for React fast refresh). */

export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(' ')
}

export function tabId(idBase: string, id: string) { return `${idBase}-tab-${id}` }
export function panelId(idBase: string) { return `${idBase}-panel` }

/** Props for the element that shows the selected tab's content. */
export function tabPanelProps(idBase: string, value: string) {
  return { id: panelId(idBase), role: 'tabpanel' as const, 'aria-labelledby': tabId(idBase, value) }
}

/** Margin to allocation, percent of the allocation; null without an allocation. */
export function marginToAllocation(withMargin: number | null | undefined, allocation: number | null | undefined): number | null {
  if (allocation == null || allocation <= 0 || withMargin == null) return null
  return (allocation - withMargin) / allocation * 100
}

export function marginStatus(pct: number | null, cautionBelowPct = 20): 'ok' | 'caution' | 'alarm' | 'neutral' {
  if (pct == null) return 'neutral'
  if (pct <= 0) return 'alarm'
  if (pct < cautionBelowPct) return 'caution'
  return 'ok'
}

export function fmtNum(v: number, digits = 2): string {
  return v.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

