/**
 * PresenceBar — Shows connected users and connection status.
 */
import { useTranslation } from 'react-i18next'
import { useCollaboration } from './useCollaboration'
import { AIStatusIndicator } from '../ai'
import { OptionSwitcher } from '../components/OptionSwitcher'

export function PresenceBar() {
  const { t } = useTranslation()
  const { connected, users, myName } = useCollaboration()

  if (!myName) return null

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '0.4rem',
      padding: '0.15rem 1rem', fontSize: '0.6rem',
      background: connected ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)',
      borderBottom: `1px solid ${connected ? 'var(--success)' : 'var(--danger)'}`,
    }}>
      <span style={{
        width: 6, height: 6, borderRadius: '50%',
        background: connected ? 'var(--success)' : 'var(--danger)',
      }} />
      <span style={{ color: connected ? 'var(--success)' : 'var(--danger)', fontWeight: 600 }}>
        {connected ? t('Connected') : t('Reconnecting...')}
      </span>
      <span style={{ color: 'var(--border)' }}>|</span>
      {users.length > 0 ? (
        users.map((u, i) => (
          <span key={u.name} style={{
            color: u.name === myName ? 'var(--accent)' : 'var(--text-secondary)',
            fontWeight: u.name === myName ? 600 : 400,
          }}>
            {u.name === myName ? t('{{name}} (you)', { name: u.name }) : u.name}
            {i < users.length - 1 ? ' · ' : ''}
          </span>
        ))
      ) : (
        <span style={{ color: 'var(--text-secondary)' }}>{t('{{name}} (you)', { name: myName })}</span>
      )}
      <span style={{ color: 'var(--text-secondary)', marginLeft: '0.3rem' }}>
        {t('— {{count}} connected', { count: users.length || 1 })}
      </span>
      <span style={{ marginLeft: 'auto', display: 'inline-flex', alignItems: 'center', gap: '0.6rem' }}>
        <OptionSwitcher />
        <AIStatusIndicator />
      </span>
    </div>
  )
}
