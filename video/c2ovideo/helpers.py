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
