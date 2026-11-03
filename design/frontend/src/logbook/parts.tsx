/**
 * Small logbook pieces used across SpaceCDF: the header button, the
 * contextual "Log this" button and the book glyph.
 */
import { useTranslation } from 'react-i18next'
import { Button } from '../components/ui/Button'
import { useLogbook, type Context, type EntryKind } from './api'
import { useLogbookUI } from './store'

export function BookGlyph({ size = 14 }: { size?: number }) {
  return (
    <svg className="c2o-lb-glyph" width={size} height={size} viewBox="0 0 16 16" aria-hidden="true" focusable="false">
      <path d="M3 2.5h7.5a1.5 1.5 0 0 1 1.5 1.5v9.5H4.5A1.5 1.5 0 0 1 3 12V2.5Z" fill="none" stroke="currentColor" strokeWidth="1.3" />
      <path d="M3 12a1.5 1.5 0 0 1 1.5-1.5H12" fill="none" stroke="currentColor" strokeWidth="1.3" />
      <path d="M5.5 5h4M5.5 7.25h4" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  )
}

/** Header button: book glyph, "Logbook", entry-count badge. Toggles the docked panel. */
export function LogbookButton() {
  const { t } = useTranslation()
  const open = useLogbookUI(s => s.open)
  const toggle = useLogbookUI(s => s.toggle)
  const { data } = useLogbook()
  const n = data?.total ?? 0
  return (
    <button type="button" className="c2o-btn c2o-lb-btn" aria-pressed={open} aria-controls="c2o-logbook"
      onClick={toggle}
      title={open ? t('Close the logbook') : t('Open your logbook: decisions, thoughts and worksheet answers')}>
      <BookGlyph />
      <span className="c2o-lb-btn__label">{t('Logbook')}</span>
      <span className="c2o-lb-badge mono" aria-label={t('{{count}} entries', { count: n, defaultValue_one: '{{count}} entry' })}>{n}</span>
    </button>
  )
}

/**
 * "Log this" next to a decision (accept/reject a proposal, apply a trade
 * result, a gate verdict). One click opens the panel with the subject as a
 * context chip. It never blocks or replaces the action itself.
 */
export function LogThis({ subject, kind = 'decision', context, label }: {
  subject: string; kind?: EntryKind; context?: Context; label?: string
}) {
  const { t } = useTranslation()
  const logThis = useLogbookUI(s => s.logThis)
  return (
    <Button size="sm" variant="quiet" className="c2o-lb-logthis"
      aria-label={t('Log this in your logbook: {{subject}}', { subject })}
      title={t('Write why in your logbook (does not change the design)')}
      onClick={e => { e.stopPropagation(); logThis({ decision: subject, ...context }, kind) }}>
      <BookGlyph size={12} />
      <span>{label ?? t('Log this')}</span>
    </Button>
  )
}
