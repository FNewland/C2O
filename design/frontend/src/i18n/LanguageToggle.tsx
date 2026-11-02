/**
 * EN | FR toggle for the app shell. Styled like the StatusBar buttons.
 * Language names are shown in their own language and are not translated.
 */
import type { CSSProperties } from 'react'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { LANGS, type Lang } from './index'

const NATIVE_NAME: Record<Lang, string> = { en: 'English', fr: 'Français' }

export function LanguageToggle({ style }: { style?: CSSProperties }) {
  const { t } = useTranslation()
  const lang = useUIStore(s => s.lang)
  const setLang = useUIStore(s => s.setLang)

  return (
    <div role="group" aria-label={t('Interface language')} className="c2o-seg c2o-lang" style={style}>
      {LANGS.map(code => {
        const active = code === lang
        return (
          <button
            key={code}
            type="button"
            lang={code}
            title={NATIVE_NAME[code]}
            aria-pressed={active}
            className="c2o-seg__item c2o-lang__item"
            onClick={() => { if (!active) setLang(code) }}
          >
            {code.toUpperCase()}
          </button>
        )
      })}
    </div>
  )
}
