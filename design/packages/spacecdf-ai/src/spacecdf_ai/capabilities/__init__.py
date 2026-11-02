"""GenAI capability modules.

Only three LLM capabilities remain (docs/RULES_AND_AI.md): free-text Q&A and
stakeholder-statement critique (advisor), polishing objectives into shall
statements (requirements) and narrative prose for documents (narrative).
Every other former capability is now done by a deterministic engine in
spacecdf-server. Each module follows the same pattern:

1. Load a system prompt from prompts/
2. Serialize design context via context.py
3. Call Claude via client.py
4. Parse the response into structured output (the server then runs the
   deterministic rule checks on it before showing it)
"""
from spacecdf_ai.capabilities import advisor, narrative, requirements

__all__ = ["advisor", "narrative", "requirements"]
