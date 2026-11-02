/**
 * Frame for the entry screens (name prompt, home). A slim app bar with the
 * wordmark and the language and theme switches, then a left-aligned working
 * column: no hero, no centred tiles.
 */
import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { LanguageToggle } from '../../i18n/LanguageToggle'
import { ThemeToggle } from './ThemeToggle'

export function HomeFrame({ title, lead, children }: { title: string; lead?: string; children: ReactNode }) {
  const { t } = useTranslation()
  return (
    <div className="c2o-home-frame">
      <header className="c2o-home-frame__bar">
        <span className="c2o-appbar__mark">SpaceCDF</span>
        <span className="t-13 c-2">{t('Concurrent Design Facility')}</span>
        <span className="c2o-hide-narrow t-12 c-3">{t('University of Ottawa — SEDTI')}</span>
        <span className="ml-auto row gap-2">
          <LanguageToggle />
          <ThemeToggle />
        </span>
      </header>
      <main className="c2o-home-frame__main">
        <h1 className="t-20 w-600 m-0">{title}</h1>
        {lead && <p className="c2o-home-frame__lead">{lead}</p>}
        <div className="mt-5">{children}</div>
      </main>
    </div>
  )
}
