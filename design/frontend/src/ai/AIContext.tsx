/**
 * AI Context — provides GenAI availability state to the component tree.
 *
 * Fetches /api/health on mount to detect whether the server has GenAI
 * capabilities installed and enabled.  Components use the useAI() hook
 * to check capability availability without direct API calls.
 */
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

export interface AICapabilities {
  design_advisor: boolean
  requirements_decomposition: boolean
  consistency_checking: boolean
  trade_analysis: boolean
  cost_estimation: boolean
  report_narrative: boolean
  fmea_generation: boolean
  cad_scripting: boolean
  wiring_generation: boolean
  fsw_generation: boolean
  aocs_design: boolean
  thermal_setup: boolean
  structural_setup: boolean
  [key: string]: boolean
}

export interface AIState {
  /** Whether spacecdf-ai package is installed on the server */
  installed: boolean
  /** Whether GenAI is enabled in configs/genai.yaml */
  enabled: boolean
  /** Per-capability availability */
  capabilities: AICapabilities
  /** Loading state (true while fetching /api/health) */
  loading: boolean
  /** Error message if health check failed */
  error: string | null
}

const DEFAULT_CAPABILITIES: AICapabilities = {
  design_advisor: false,
  requirements_decomposition: false,
  consistency_checking: false,
  trade_analysis: false,
  cost_estimation: false,
  report_narrative: false,
  fmea_generation: false,
  cad_scripting: false,
  wiring_generation: false,
  fsw_generation: false,
  aocs_design: false,
  thermal_setup: false,
  structural_setup: false,
}

const DEFAULT_STATE: AIState = {
  installed: false,
  enabled: false,
  capabilities: DEFAULT_CAPABILITIES,
  loading: true,
  error: null,
}

const AIContext = createContext<AIState>(DEFAULT_STATE)

export function AIProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AIState>(DEFAULT_STATE)

  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json())
      .then((data) => {
        const genai = data.genai || {}
        setState({
          installed: genai.installed ?? false,
          enabled: genai.enabled ?? false,
          capabilities: { ...DEFAULT_CAPABILITIES, ...(genai.capabilities || {}) },
          loading: false,
          error: null,
        })
      })
      .catch((err) => {
        setState({
          ...DEFAULT_STATE,
          loading: false,
          error: `Health check failed: ${err.message}`,
        })
      })
  }, [])

  return <AIContext.Provider value={state}>{children}</AIContext.Provider>
}

/**
 * Hook to access AI availability state.
 *
 * @example
 * const { enabled, capabilities } = useAI()
 * if (capabilities.cad_scripting) { ... }
 */
export function useAI(): AIState {
  return useContext(AIContext)
}
