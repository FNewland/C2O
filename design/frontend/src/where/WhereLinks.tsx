/**
 * "Where in SpaceCDF" under a worksheet question or a decision (Nov 2026 audit):
 * buttons that switch the workbench to the screen that answers it, the open-textbook
 * sections, and external reading (safe links only, new window).
 */
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { bookRef, goWhere, type WhereResult, type WhereTarget } from './where'
import { safeExternalUrl, type ExternalLink } from './links'

function resultText(r: WhereResult, t: TFunction): string {
  switch (r) {
    case 'study-open': return t('Set in Mission Definition when the study was created; review it under Traceability › Mission need.')
    case 'no-study': return t('Open or create a study first.')
    case 'later-step': return t('Finish the earlier Mission Definition steps first.')
    case 'not-found': return t('This study has nothing at that level yet: add the spacecraft and its subsystems first.')
    default: return ''
  }
}

export function WhereLinks({ where = [], book = [], links = [], compact = false }: {
  where?: WhereTarget[]; book?: string[]; links?: ExternalLink[]; compact?: boolean
}) {
  const { t } = useTranslation()
  const [msg, setMsg] = useState('')
  const safe = links.map(l => ({ ...l, href: safeExternalUrl(l.url) })).filter(l => l.href)
  if (!where.length && !book.length && !safe.length) return null
  const go = async (w: WhereTarget) => {
    const r = await goWhere(w)
    setMsg(resultText(r, t))
    if (r !== 'ok') window.setTimeout(() => setMsg(''), 6000)
  }
  return (
    <div className={compact ? 'c2o-where c2o-where--compact' : 'c2o-where'} data-testid="where-links">
      {where.length > 0 && (
        <div className="c2o-where__row">
          <span className="c2o-where__h">{t('Where in SpaceCDF')}</span>
          <ul className="c2o-where__list list-reset">
            {where.map(w => (
              <li key={w.id}>
                <button type="button" className="c2o-where__go" onClick={() => void go(w)}
                  title={t('Open this place in SpaceCDF (the logbook stays open)')}>
                  {w.label}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
      {book.length > 0 && (
        <div className="c2o-where__row">
          <span className="c2o-where__h" title={t('Concurrent Spacecraft Design, the open textbook of the course')}>{t('Open textbook')}</span>
          <span className="c2o-where__book">{book.map(b => bookRef(b, t)).join(', ')}</span>
        </div>
      )}
      {safe.length > 0 && (
        <div className="c2o-where__row">
          <span className="c2o-where__h">{t('Read more')}</span>
          <ul className="c2o-where__list list-reset">
            {safe.map(l => (
              <li key={l.id}>
                <a className="c2o-where__ext" href={l.href!} target="_blank" rel="noopener noreferrer">
                  {l.title}<span aria-hidden="true"> ↗</span>
                  <span className="sr-only"> {t('(opens in a new window)')}</span>
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
      {msg && <p className="c2o-where__msg t-12 m-0" role="status">{msg}</p>}
    </div>
  )
}
