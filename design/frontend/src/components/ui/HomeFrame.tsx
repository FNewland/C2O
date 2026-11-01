/**
 * Frame for the entry screens (name prompt, home). A slim app bar with the
 * wordmark, then a left-aligned working column: no hero, no centred tiles.
 * The language toggle is fixed top-right by App.tsx and sits inside the bar.
 */
import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { fs } from '../../theme/tokens'

export function HomeFrame({ title, lead, children }: { title: string; lead?: string; children: ReactNode }) {
  const { t } = useTranslation()
  return (
    <div style={{ minHeight: '100vh', background: 'var(--surface-0)', color: 'var(--text)' }}>
      <header style={{
        display: 'flex', alignItems: 'baseline', gap: 'var(--sp-3)', flexWrap: 'wrap',
        minHeight: 48, padding: 'var(--sp-3) 7rem var(--sp-3) var(--sp-4)',
        background: 'var(--surface-1)', borderBottom: '1px solid var(--line)',
      }}>
        <span style={{ fontSize: fs.value, fontWeight: 600, color: 'var(--brand)', letterSpacing: '0.01em' }}>SpaceCDF</span>
        <span style={{ fontSize: fs.body, color: 'var(--text-2)' }}>{t('Concurrent Design Facility')}</span>
        <span className="c2o-hide-narrow" style={{ fontSize: fs.label, color: 'var(--text-3)', paddingLeft: 'var(--sp-3)', borderLeft: '1px solid var(--line)' }}>
          {t('University of Ottawa — SEDTI')}
        </span>
      </header>
      <main style={{
        width: '100%', maxWidth: 1040, margin: '0 auto',
        padding: 'clamp(24px, 8vh, 72px) var(--sp-4) var(--sp-6)',
      }}>
        <h1 style={{ fontSize: fs.title, fontWeight: 600, lineHeight: 'var(--lh-value)', margin: 0 }}>{title}</h1>
        {lead && <p style={{ fontSize: fs.body, color: 'var(--text-2)', margin: 'var(--sp-2) 0 0', maxWidth: '62ch' }}>{lead}</p>}
        <div style={{ marginTop: 'var(--sp-5)' }}>{children}</div>
      </main>
    </div>
  )
}
