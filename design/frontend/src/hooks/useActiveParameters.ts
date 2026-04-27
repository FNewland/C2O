/**
 * useActiveParameters — merges designStore (local single-user) with
 * sessionStore (live WebSocket collaboration) so all UI components see
 * a single consistent parameter set.
 *
 * Priority: when a session is active and has received a state_snapshot,
 * session parameters override design parameters. This ensures that live
 * edits from other positions are immediately visible.
 */
import { useDesignStore, type DesignParam } from '../stores/designStore'
import { useSessionStore } from '../stores/sessionStore'

export function useActiveParameters(): Record<string, DesignParam> {
  const designParams = useDesignStore(s => s.result?.parameters ?? {})
  const sessionParams = useSessionStore(s => s.parameters)
  const sessionId = useSessionStore(s => s.sessionId)

  // When a live session is active and has data, prefer session params
  if (sessionId && Object.keys(sessionParams).length > 0) {
    return { ...designParams, ...sessionParams }
  }
  return designParams
}

export function useHasActiveSession(): boolean {
  return !!useSessionStore(s => s.sessionId)
}

export function useCanEditParameter(paramId: string): boolean {
  const sessionId = useSessionStore(s => s.sessionId)
  const positionIds = useSessionStore(s => s.positionIds)
  const sendEdit = useSessionStore(s => s.sendEdit)

  if (!sessionId || !sendEdit) return false

  // Systems engineer can edit anything
  if (positionIds.includes('systems_engineer')) return true

  // Check if any claimed position owns this parameter (fnmatch-like)
  const domain = paramId.split('.')[0]
  const POSITION_DOMAINS: Record<string, string[]> = {
    power_engineer: ['power'],
    aocs_engineer: ['aocs'],
    thermal_engineer: ['thermal'],
    comms_engineer: ['link', 'data'],
    propulsion_engineer: ['propulsion'],
    structures_engineer: ['structure'],
    mission_analyst: ['orbit', 'mission'],
    payload_lead: ['payload'],
    cost_engineer: ['cost'],
  }

  for (const pos of positionIds) {
    const domains = POSITION_DOMAINS[pos]
    if (domains && domains.includes(domain)) return true
  }

  return false
}
