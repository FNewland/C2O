/**
 * AIStatusIndicator — small topbar badge showing GenAI status.
 *
 * Shows:
 *   - Green dot + "AI" when enabled
 *   - Grey dot + "AI Off" when installed but disabled
 *   - Nothing when not installed (clean v1.0 experience)
 */
import { useAI } from './AIContext'

export function AIStatusIndicator() {
  const { installed, enabled, loading } = useAI()

  if (loading || !installed) return null

  const dotColor = enabled ? '#22c55e' : '#94a3b8'
  const label = enabled ? 'AI' : 'AI Off'

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '2px 8px',
        borderRadius: 12,
        fontSize: 12,
        fontWeight: 500,
        color: enabled ? '#166534' : '#64748b',
        backgroundColor: enabled ? '#dcfce7' : '#f1f5f9',
        border: `1px solid ${enabled ? '#bbf7d0' : '#e2e8f0'}`,
      }}
      title={
        enabled
          ? 'GenAI capabilities are active'
          : 'GenAI installed but disabled — enable in configs/genai.yaml'
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
