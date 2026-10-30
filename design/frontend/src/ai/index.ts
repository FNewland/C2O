/**
 * AI module — re-exports for clean imports.
 *
 * Usage:
 *   import { AIProvider, useAI, AIGate, AIStatusIndicator } from './ai'
 */
export { AIProvider, useAI } from './AIContext'
export type { AIState, AICapabilities } from './AIContext'
export { AIGate } from './AIGate'
export { AIStatusIndicator } from './AIStatusIndicator'
