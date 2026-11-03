/**
 * PresenceBar — connection status, who is in the study, the active design
 * option and the GenAI status. Rendered inline in the app bar (no band of
 * its own): grey when connected (calm), alarm glyph + text when the session
 * socket is reconnecting.
 */
import { useTranslation } from 'react-i18next'
import { useCollaboration } from './useCollaboration'
import { AIStatusIndicator } from '../ai'
import { OptionSwitcher } from '../components/OptionSwitcher'
import { StatusBadge } from '../components/ui/StatusBadge'

export function PresenceBar() {
  const { t } = useTranslation()
  const { connected, users, myName, me } = useCollaboration()
  if (!myName) return null
  // Users are distinct identities (WP0): someone else with my display name still counts.
  const others = users.filter(u => (u.id && me ? u.id !== me : u.name !== myName)).map(u => u.name)
  const count = users.length || 1
  const who = [t('{{name}} (you)', { name: myName }), ...others].join(', ')
  return (
    <div className="c2o-presence">
      <span className="iflex ai-c gap-2 t-12" title={who}>
        {connected
          ? <StatusBadge status="neutral">{t('{{count}} connected', { count, defaultValue_one: '{{count}} connected' })}</StatusBadge>
          : <StatusBadge status="alarm">{t('Reconnecting...')}</StatusBadge>}
        <span className="c2o-presence__names c-2 ellipsis">{who}</span>
      </span>
      <OptionSwitcher />
      <AIStatusIndicator />
    </div>
  )
}
