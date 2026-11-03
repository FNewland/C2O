/**
 * Pairwise comparison weighting (pure; no imports so it runs under plain Node in tests).
 *
 * For each pair (a, b) the slider value is 1 = a wins, 0.5 = equal, 0 = b wins. A pair
 * the user has not touched counts as EQUAL (0.5), as the slider shows: before Nov 2026 an
 * untouched pair counted 0 for both criteria, so all-equal criteria derived 0 % each
 * instead of 1/n (WP0, walkthrough #20).
 */
export const pairKey = (a: string, b: string): string => `${a}|${b}`

export function pairwiseWeights(criteria: string[], comparisons: Record<string, number>): Record<string, number> {
  const raw: Record<string, number> = {}
  for (const c of criteria) {
    let score = 0
    for (const other of criteria) {
      if (other === c) continue
      const val = comparisons[pairKey(c, other)]
      const rev = comparisons[pairKey(other, c)]
      score += val != null ? val : rev != null ? 1 - rev : 0.5
    }
    raw[c] = Math.max(score, 0)
  }
  const total = Object.values(raw).reduce((s, v) => s + v, 0)
  const out: Record<string, number> = {}
  for (const c of criteria) out[c] = total > 0 ? raw[c] / total : (criteria.length ? 1 / criteria.length : 0)
  return out
}
