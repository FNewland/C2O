/**
 * AIGate — conditionally renders children based on GenAI capability availability.
 *
 * Usage:
 *   <AIGate capability="cad_scripting" fallback={<p>CAD generation requires GenAI</p>}>
 *     <CADGenerateButton />
 *   </AIGate>
 *
 * When the capability is disabled:
 *   - If fallback is provided, renders the fallback
 *   - If showDisabled is true, renders children with reduced opacity + tooltip
 *   - Otherwise renders nothing
 */
import { type ReactNode } from 'react'
import { useAI } from './AIContext'

interface AIGateProps {
  /** Capability name from genai.yaml */
  capability: string
  /** Content to render when AI capability is available */
  children: ReactNode
  /** Content to render when AI capability is unavailable */
  fallback?: ReactNode
  /** If true, show children greyed out instead of hiding them */
  showDisabled?: boolean
  /** Tooltip text when disabled (requires showDisabled) */
  disabledTooltip?: string
}

export function AIGate({
  capability,
  children,
  fallback,
  showDisabled = false,
  disabledTooltip,
}: AIGateProps) {
  const { enabled, capabilities, loading } = useAI()

  // While loading, show nothing (avoids flash)
  if (loading) return null

  const isAvailable = enabled && capabilities[capability]

  if (isAvailable) {
    return <>{children}</>
  }

  if (fallback) {
    return <>{fallback}</>
  }

  if (showDisabled) {
    return (
      <div
        style={{ opacity: 0.4, pointerEvents: 'none', cursor: 'not-allowed' }}
        title={disabledTooltip || `Requires GenAI capability: ${capability}`}
      >
        {children}
      </div>
    )
  }

  return null
}
