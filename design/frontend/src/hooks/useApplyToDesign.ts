/**
 * useApplyToDesign — shared hook for pushing calculator values to the design loop.
 *
 * Per SPINE_SPEC §10.2. ALWAYS writes to designStore.parameterOverrides so values
 * persist and survive page refreshes. If a WebSocket session is active, also
 * dispatches via sendEdit for live collaboration.
 *
 * Usage:
 *   const apply = useApplyToDesign({
 *     events: [
 *       { kind: "parameter_override", target_id: "link.tx_power_w", new_value: 2.0 },
 *       { kind: "parameter_override", target_id: "link.frequency_ghz", new_value: 2.25 },
 *     ],
 *     correlation_id: "linkbudget-tool",
 *     rationale: "manual link-budget tuning",
 *   })
 *   // Then: <button onClick={apply}>Apply to Design</button>
 */
import { useCallback } from 'react'
import { useSessionStore } from '../stores/sessionStore'
import { useDesignStore } from '../stores/designStore'
import type { ChangeKind } from '../types/changeEvent'

interface PartialEvent {
  kind: ChangeKind
  target_id: string
  target_kind?: string
  old_value?: unknown
  new_value: unknown
}

interface ApplyOptions {
  events: PartialEvent[]
  correlation_id?: string
  rationale?: string
}

let _counter = 0
function generateCorrelationId(): string {
  return `corr-${Date.now()}-${++_counter}`
}

export function useApplyToDesign(options: ApplyOptions) {
  const sendEdit = useSessionStore(s => s.sendEdit)

  return useCallback(async () => {
    const { setParameter } = useDesignStore.getState()

    // ALWAYS write to parameterOverrides — this is the source of truth
    for (const evt of options.events) {
      if (evt.target_id && evt.new_value !== undefined) {
        setParameter(
          evt.target_id,
          evt.new_value as number | string | boolean,
          options.correlation_id || 'apply-to-design',
        )
      }
    }

    // If session active, ALSO dispatch via WebSocket for live collaboration
    if (sendEdit) {
      for (const evt of options.events) {
        if (evt.kind === 'parameter_override') {
          sendEdit(evt.target_id, evt.new_value as number | string | boolean, {
            rationale: options.rationale,
          })
        } else {
          sendEdit(evt.target_id, evt.new_value as number | string | boolean, {
            rationale: options.rationale,
            editType: evt.kind,
          })
        }
      }
    }
  }, [sendEdit, options.events, options.correlation_id, options.rationale])
}
