"""SpaceCDF — Agent Information API."""
from __future__ import annotations

from fastapi import APIRouter

from spacecdf_agents.registry import discover_agents

router = APIRouter()


@router.get("/")
async def list_agents() -> list[dict]:
    """List all available design agents."""
    agents = discover_agents()
    result = []
    for name, cls in agents.items():
        instance = cls()
        result.append({
            "name": name,
            "domain": instance.domain,
            "tier": instance.tier,
            "inputs": instance.input_parameters(),
            "outputs": instance.output_parameters(),
            "dependencies": instance.dependencies(),
        })
    return result
