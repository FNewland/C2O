/**
 * Light / dark switch for the app bar. Light is the design-work default;
 * dark is the control-room ramp shared with the SMO consoles. The choice
 * persists (theme/useTheme.ts, localStorage 'c2o.theme', try/catch).
 */
import type { CSSProperties } from 'react'
import { useTranslation } from 'react-i18next'
import { setTheme, useTheme } from '../../theme/useTheme'

export function ThemeToggle({ style }: { style?: CSSProperties }) {
  const { t } = useTranslation()
  const theme = useTheme()
  const next = theme === 'dark' ? 'light' : 'dark'
  return (
    <button
      type="button"
      className="c2o-btn c2o-theme-toggle"
      style={style}
      aria-label={theme === 'dark' ? t('Switch to light theme') : t('Switch to dark theme')}
      title={theme === 'dark' ? t('Switch to light theme') : t('Switch to dark theme')}
      onClick={() => setTheme(next)}
    >
      <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
        <circle cx="6" cy="6" r="5" fill="none" stroke="currentColor" strokeWidth="1.2" />
        <path d="M6 1a5 5 0 0 1 0 10Z" fill="currentColor" />
      </svg>
      <span className="c2o-theme-toggle__label">{theme === 'dark' ? t('Dark', { context: 'theme' }) : t('Light', { context: 'theme' })}</span>
    </button>
  )
}
