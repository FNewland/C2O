"""Setup helpers that storyboards call (``python: {call: "video/c2ovideo/helpers.py:ff_to_pass"}``).

They make a capture repeatable: the same pass, the same point in it, whatever
time the simulator happened to be at when the take started.
"""

from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime


def _ts(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def _sim_time(client) -> float:
    return _ts(client.get("/api/state").json()["sim_time"])


def ff_to_pass(client, planner: str = "http://127.0.0.1:9091", min_duration: float = 420,
               min_elevation: float = 15, after_aos: float = 25, station: str | None = None) -> str:
    """Run the simulator fast to ``after_aos`` seconds into the next long pass, then real time.

    ``client`` is the instructor (simulator) API. Returns the station name.
    """
    with urllib.request.urlopen(planner.rstrip("/") + "/api/contacts", timeout=20) as r:
        contacts = json.loads(r.read())["contacts"]
    now = _sim_time(client)
    cands = [c for c in contacts if _ts(c["aos"]) > now + 5 and c["duration_s"] >= min_duration
             and c.get("max_elevation_deg", 90) >= min_elevation and (station is None or c["gs_name"] == station)]
    if not cands:
        raise RuntimeError("no suitable pass in the planner's window")
    c = min(cands, key=lambda x: _ts(x["aos"]))
    target = _ts(c["aos"]) + after_aos

    def speed(v: float) -> None:
        client.post("/api/command", json={"type": "set_speed", "value": v})

    try:
        while True:
            left = target - _sim_time(client)
            if left <= 0.5:
                break
            # coarse then fine: never overshoot by more than a second or two of sim time
            v = 200 if left > 900 else 40 if left > 120 else 8 if left > 15 else 1
            speed(v)
            time.sleep(min(0.5, max(0.05, left / v / 3)))
    finally:
        speed(1)
    return c["gs_name"]



async def fast_until_aocs_error(client, below: float = 5.0, speed: float = 10, timeout_s: float = 90) -> float:
    """Run the simulator at ``speed`` until the TRUE attitude error is under ``below`` deg.

    A fixed wall-clock wait is not a fixed amount of sim time while a capture
    is running (the simulator does not keep up with 10x), so a slew filmed with
    one stalled mid-way. Async, so the capture keeps recording while it waits.
    Returns the error reached; always ends at real time.
    """
    import asyncio

    async def err() -> float:
        r = await client.get("/api/state")
        return float(r.json().get("aocs", {}).get("att_error_deg", 999.0))

    t0 = time.time()
    try:
        await client.post("/api/command", json={"type": "set_speed", "value": speed})
        while time.time() - t0 < timeout_s and await err() >= below:
            await asyncio.sleep(0.5)
    finally:
        await client.post("/api/command", json={"type": "set_speed", "value": 1})
    return await err()


async def seed_spacecdf_eosat(client, name: str = "EOSAT-1") -> str:
    """A new SpaceCDF study seeded with the EOSAT-1-like design used in the API tests
    (design/tests/test_api/diagram_seed.py): product tree, modes, power lines,
    interfaces, requirements. Returns the study id."""
    import importlib.util
    from pathlib import Path
    REPO = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("c2o_diagram_seed", REPO / "design/tests/test_api/diagram_seed.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    req = {"name": name, "mission_type": "earth_observation", "spacecraft_class": "nano",
           "orbit": {"orbit_type": "sso", "altitude_km": 510, "inclination_deg": 97.4}, "payloads": []}
    r = await client.post("/api/studies/", json={"requirements": req,
                                                 "mission_need": {"problem_statement": "Ocean-colour imaging of Canadian waters"}})
    sid = r.json()["id"]
    await mod.seed_eosat(client, sid)
    return sid
