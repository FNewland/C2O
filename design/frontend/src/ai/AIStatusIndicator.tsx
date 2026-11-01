/**
 * AIStatusIndicator — small topbar badge showing GenAI status.
 *
 * Shows:
 *   - Green dot + "AI" when enabled
 *   - Grey dot + "AI Off" when installed but disabled
 *   - Nothing when not installed (clean v1.0 experience)
 */
import { useTranslation } from 'react-i18next'
import { useAI } from './AIContext'
import { fs } from '../theme/tokens'

export function AIStatusIndicator() {
  const { t } = useTranslation()
  const { installed, enabled, loading } = useAI()

  if (loading || !installed) return null

  const dotColor = enabled ? 'var(--status-ok)' : 'var(--text-3)'
  const label = enabled ? t('AI') : t('AI Off')

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '2px 8px',
        borderRadius: 12,
        fontSize: fs.label,
        fontWeight: 500,
        color: enabled ? 'var(--status-ok)' : 'var(--text-3)',
        backgroundColor: enabled ? 'var(--status-ok-wash)' : 'var(--text)',
        border: `1px solid ${enabled ? 'var(--status-ok-wash)' : 'var(--text)'}`,
      }}
      title={
        enabled
          ? t('GenAI capabilities are active')
          : t('GenAI installed but disabled — enable in configs/genai.yaml')
      }
    >
      <span
        style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          backgroundColor: dotColor,
          display: 'inline-block',
        }}
      />
      {label}
    </div>
  )
}
