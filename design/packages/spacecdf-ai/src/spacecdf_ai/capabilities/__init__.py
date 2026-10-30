"""GenAI capability modules.

Each module implements one AI-enhanced capability that can be independently
toggled via configs/genai.yaml.  All capabilities follow the same pattern:

1. Load a system prompt from prompts/
2. Serialize design context via context.py
3. Call Claude via client.py
4. Parse the response into structured output
"""
from spacecdf_ai.capabilities import (
    advisor,
    consistency,
    requirements,
    narrative,
    trade,
    cost,
    fmea,
    cad,
    wiring,
    fsw,
    aocs,
    thermal,
    structural,
)

__all__ = [
    "advisor",
    "consistency",
    "requirements",
    "narrative",
    "trade",
    "cost",
    "fmea",
    "cad",
    "wiring",
    "fsw",
    "aocs",
    "thermal",
    "structural",
]
