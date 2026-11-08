/**
 * Translate text the server or the design agents wrote in English (conflict titles,
 * details and suggested fixes, analysis-parameter descriptions).
 *
 * The server stores these as finished English sentences. serverText() matches one
 * against SERVER_TEMPLATES ({{name}} placeholders), translates the template and
 * re-inserts the captured values, themselves translated when they are catalogue keys
 * (a budget label, a verification method). Lists the server joins with "; " are
 * translated item by item. Text that matches nothing is returned unchanged.
 */
import i18n from 'i18next'
import { SERVER_TEMPLATES } from './serverTemplates'

type Compiled = { key: string; re: RegExp; names: string[] }

const escape = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

// Most specific first: the longest literal text wins, so "… System effect: X. Downstream: Y."
// is not taken by the shorter "… System effect: X." template.
const COMPILED: Compiled[] = SERVER_TEMPLATES
  .map(key => {
    const names: string[] = []
    const parts = key.split(/\{\{(\w+)\}\}/)
    let src = '^'
    parts.forEach((p, i) => {
      if (i % 2) { names.push(p); src += '(.+?)' } else src += escape(p)
    })
    return { key, re: new RegExp(src + '$', 's'), names, lit: parts.filter((_, i) => i % 2 === 0).join('').length }
  })
  .sort((a, b) => b.lit - a.lit)

function one(text: string, depth: number): string {
  const s = text.trim()
  if (!s) return text
  if (i18n.exists(s)) return i18n.t(s)
  for (const c of COMPILED) {
    const m = c.re.exec(s)
    if (!m) continue
    const values: Record<string, string> = {}
    c.names.forEach((n, i) => { values[n] = depth < 2 ? one(m[i + 1], depth + 1) : m[i + 1] })
    return i18n.t(c.key, { ...values, interpolation: { escapeValue: false } })
  }
  return text
}

export function serverText(text: string | null | undefined): string {
  if (!text) return text ?? ''
  if (!i18n.language?.startsWith('fr')) return text
  const whole = one(text, 0)
  if (whole !== text || !text.includes('; ')) return whole
  return text.split('; ').map(p => one(p, 0)).join('\u202f; ')
}
