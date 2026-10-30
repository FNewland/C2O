/**
 * SpaceCDF i18n runtime (packet C0) — i18next + react-i18next.
 *
 * NATURAL-LANGUAGE KEYS: the English text *is* the key.
 *   t('Run Analysis')            → 'Run Analysis' (en) / 'Lancer l'analyse' (fr)
 * en.json is empty: a key missing from every catalog renders as itself
 * (interpolated), so English output is byte-identical to the old literals.
 * fr.json maps English → French; a missing or empty French entry falls back
 * to English, never to a blank.
 *
 * Why not parseMissingKeyHandler: i18next calls it with the *raw* key, after
 * interpolation, so `{{name}}` placeholders would leak into the UI. The
 * built-in missing-key path already returns the interpolated key.
 *
 * Plurals (JSON v4, Intl.PluralRules): key = English plural form, singular
 * via defaultValue_one, French via `<key>_one` / `_many` / `_other` in fr.json:
 *   t('{{count}} elements', { count: n, defaultValue_one: '{{count}} element' })
 *
 * Language: `?lang=fr|en` (wins and is persisted) > localStorage 'scdf.lang'
 * > 'en'. <html lang> follows the active language. See GUIDE.md.
 */
import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './locales/en.json'
import fr from './locales/fr.json'

// Per-packet French catalogs (locales/fr.c1.json … fr.c4.json) let the
// parallel translation packets work without editing one shared file. They
// are merged over fr.json in file-name order; fold them into fr.json once
// wave 2 is done (the sync tool reads fr.json).
const frPackets = import.meta.glob<Record<string, string>>('./locales/fr.*.json', { eager: true, import: 'default' })
const frMerged: Record<string, string> = Object.assign(
  {}, fr as Record<string, string>,
  ...Object.keys(frPackets).sort().map(k => frPackets[k]),
)

export type Lang = 'en' | 'fr'
export const LANGS: readonly Lang[] = ['en', 'fr'] as const
export const LANG_STORAGE_KEY = 'scdf.lang'

export function normalizeLang(value: string | null | undefined): Lang | null {
  if (!value) return null
  const primary = value.trim().toLowerCase().replace('_', '-').split('-')[0]
  return (LANGS as readonly string[]).includes(primary) ? (primary as Lang) : null
}

function readStored(): Lang | null {
  try { return normalizeLang(localStorage.getItem(LANG_STORAGE_KEY)) } catch { return null }
}

function writeStored(lang: Lang): void {
  try { localStorage.setItem(LANG_STORAGE_KEY, lang) } catch { /* private mode etc. */ }
}

/** Initial language: ?lang= override (persisted) > localStorage > 'en'. */
export function detectInitialLang(): Lang {
  let fromUrl: Lang | null = null
  try { fromUrl = normalizeLang(new URLSearchParams(window.location.search).get('lang')) } catch { /* no window */ }
  if (fromUrl) { writeStored(fromUrl); return fromUrl }
  return readStored() ?? 'en'
}

function applyDocumentLang(lang: Lang): void {
  if (typeof document !== 'undefined') document.documentElement.lang = lang
}

const initialLang = detectInitialLang()

void i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en as Record<string, string> },
    fr: { translation: frMerged },
  },
  lng: initialLang,
  fallbackLng: 'en',
  supportedLngs: [...LANGS],
  keySeparator: false,          // keys are sentences: '.' is text, not a path
  nsSeparator: false,           // ':' is text, not a namespace marker
  returnNull: false,
  returnEmptyString: false,     // "" in fr.json = not yet translated → English
  interpolation: { escapeValue: false },  // React escapes rendered strings itself
  react: { useSuspense: false },          // resources are bundled; no async load
  initAsync: false,
})
applyDocumentLang(initialLang)

i18n.on('languageChanged', (lng) => {
  const lang = normalizeLang(lng) ?? 'en'
  writeStored(lang)
  applyDocumentLang(lang)
})

/** Current UI language ('en' | 'fr'). */
export function getLang(): Lang {
  return normalizeLang(i18n.language) ?? 'en'
}

/** Switch language (persists to localStorage and updates <html lang>). */
export function setLang(lang: Lang): Promise<unknown> {
  return i18n.changeLanguage(lang)
}

/**
 * Headers/body field to send the UI language to the backend AI endpoints.
 * POST /api/ai/ask takes `language` in the JSON body; the convenience
 * endpoints (/api/ai/critique-need …) take `?language=`. Errors stay English.
 */
export function aiLanguageField(): { language: Lang } {
  return { language: getLang() }
}

// ─── Number / date formatting ────────────────────────────────────────────
// Engineering values (telemetry-like numbers, values users type back into
// inputs, anything in a table of computed results) keep the decimal POINT
// in both languages (owner ruling R5). Use fmtEng for those — it is a
// drop-in for value.toFixed(d).
// Prose numbers inside translated sentences may use fmtProse, which follows
// the UI language (fr-FR: decimal comma, U+202F thousands separator).

const INTL_LOCALE: Record<Lang, string> = { en: 'en-CA', fr: 'fr-FR' }

export function intlLocale(lang: Lang = getLang()): string {
  return INTL_LOCALE[lang]
}

/** Engineering value: always '.', never grouped. Same as Number#toFixed. */
export function fmtEng(value: number | null | undefined, digits = 2, empty = '—'): string {
  if (value == null || !Number.isFinite(value)) return empty
  return value.toFixed(digits)
}

/** Prose number in the UI language (fr: '1 234,5'; en: '1,234.5'). */
export function fmtProse(value: number | null | undefined, opts: Intl.NumberFormatOptions = {}, empty = '—'): string {
  if (value == null || !Number.isFinite(value)) return empty
  return new Intl.NumberFormat(intlLocale(), opts).format(value)
}

/** Date (and optionally time) in the UI language. ISO timestamps meant to be copied stay ISO. */
export function fmtDate(value: Date | string | number, opts: Intl.DateTimeFormatOptions = { dateStyle: 'medium' }): string {
  const d = value instanceof Date ? value : new Date(value)
  return Number.isNaN(d.getTime()) ? String(value) : new Intl.DateTimeFormat(intlLocale(), opts).format(d)
}

export default i18n
