/**
 * EN | FR toggle for the app shell. Styled like the StatusBar buttons.
 * Language names are shown in their own language and are not translated.
 */
import type { CSSProperties } from 'react'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { LANGS, type Lang } from './index'
import { fs } from '../theme/tokens'

const NATIVE_NAME: Record<Lang, string> = { en: 'English', fr: 'Français' }

export function LanguageToggle({ style }: { style?: CSSProperties }) {
  const { t } = useTranslation()
  const lang = useUIStore(s => s.lang)
  const setLang = useUIStore(s => s.setLang)

  return (
    <div
      role="group"
      aria-label={t('Interface language')}
      style={{
        display: 'inline-flex', borderRadius: 'var(--radius)', overflow: 'hidden',
        border: '1px solid var(--line-strong)', background: 'var(--surface-1)',
        ...style,
      }}
    >
      {LANGS.map((code, i) => {
        const active = code === lang
        return (
          <button
            key={code}
            type="button"
            lang={code}
            title={NATIVE_NAME[code]}
            aria-pressed={active}
            onClick={() => { if (!active) setLang(code) }}
            style={{
              minHeight: 26, padding: '0 var(--sp-2)', fontSize: fs.label, fontWeight: 600,
              fontFamily: 'var(--font-mono)',
              border: 'none', borderLeft: i > 0 ? '1px solid var(--line-strong)' : 'none',
              background: active ? 'var(--interactive)' : 'transparent',
              color: active ? 'var(--on-fill)' : 'var(--text-2)',
              cursor: active ? 'default' : 'pointer',
            }}
          >
            {code.toUpperCase()}
          </button>
        )
      })}
    </div>
  )
}
