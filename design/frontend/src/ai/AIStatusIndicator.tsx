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
import { StatusBadge } from '../components/ui/StatusBadge'

export function AIStatusIndicator() {
  const { t } = useTranslation()
  const { installed, enabled, loading } = useAI()

  if (loading || !installed) return null

  const label = enabled ? t('AI') : t('AI Off')

  return (
    <span
      className="t-12"
      title={enabled ? t('GenAI capabilities are active') : t('GenAI installed but disabled — enable in configs/genai.yaml')}
    >
      <StatusBadge status={enabled ? 'ok' : 'nodata'}>{label}</StatusBadge>
    </span>
  )
}
