#!/usr/bin/env python3
"""Breakpoint library: the simulator state at the start of every LEOP and
commissioning card.

Flies the definitive card sequence headless, exactly as the acceptance
fly-through does (tests/test_acceptance/test_leop_commissioning_flythrough.py:
cold boot, every telecommand a real packet through the TC path), and saves a
breakpoint just before each card runs: ``card-LEOP-001``, ``card-LEOP-002`` …
``card-COM-013``, plus ``card-END`` (commissioned, NOMINAL hold).

The files go to ``workspace/breakpoints/``, which the simulator loads at
start-up (they appear in the instructor's breakpoint list), so an instructor,
a course video or a walkthrough can start any card from its real entry state
with ``load_breakpoint``. They are generated, not committed: ~0.6 MB each,
mostly the on-board packet stores, and ~30 s to fly the whole sequence.

    python tools/card_breakpoints.py            # (re)generate, from sim/
    python tools/card_breakpoints.py --check    # same states as on disk?

Regenerate after any change to the cards, the models or the fly-through, and
restart the simulator (or load by name: breakpoints on disk are read at start).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import os
import sys
import tempfile
from pathlib import Path

SIM = Path(__file__).resolve().parents[1]
CONFIG_DIR = SIM / "configs" / "eosat1"
LIBRARY = SIM / "workspace" / "breakpoints"
FLY = SIM / "tests" / "test_acceptance" / "test_leop_commissioning_flythrough.py"


def _card_id(method_name: str) -> str:
    # test_leop_001_first_acquisition_and_boot -> LEOP-001
    parts = method_name.split("_")
    return f"{parts[1].upper()}-{parts[2]}"


def _pytest_stub() -> None:
    """The fly-through module imports pytest for its decorators only; a laptop
    venv without the test tools still has to be able to fly it."""
    try:
        import pytest  # noqa: F401
        return
    except ImportError:
        pass
    import types

    def _passthrough(*a, **kw):
        if len(a) == 1 and callable(a[0]) and not kw:
            return a[0]
        return lambda f: f

    class _Mark:
        def __getattr__(self, _name):
            return _passthrough

    stub = types.ModuleType("pytest")
    stub.fixture = _passthrough
    stub.mark = _Mark()
    stub.skip = lambda *a, **kw: (_ for _ in ()).throw(RuntimeError(a[0] if a else "skip"))
    sys.modules["pytest"] = stub


def _flythrough():
    _pytest_stub()
    spec = importlib.util.spec_from_file_location("_card_flythrough", FLY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _strip(state: dict) -> dict:
    """Drop what changes between identical runs (wall-clock stamps)."""
    s = dict(state)
    for k in ("saved_at", "wall_time", "created", "timestamp"):
        s.pop(k, None)
    return s


def build(out: Path) -> list[str]:
    os.environ.setdefault("SMO_DUMP_DIR", tempfile.mkdtemp(prefix="card-bp-dumps-"))
    mod = _flythrough()
    from smo_simulator.breakpoints import BreakpointManager
    from smo_simulator.engine import SimulationEngine

    eng = SimulationEngine(CONFIG_DIR, speed=1.0)
    fly = mod.Flight(eng)
    # Same instructor stand-in as the fly-through: a station always in view.
    eng._override_passes = True
    eng.params[0x05FF] = 1
    cls = mod.TestLeopCommissioningFlyThrough
    methods = [(n, f) for n, f in inspect.getmembers(cls, inspect.isfunction) if n.startswith("test_")]
    methods.sort(key=lambda nf: inspect.getsourcelines(nf[1])[1])     # file order = card order
    out.mkdir(parents=True, exist_ok=True)
    written = []
    inst = cls()

    def save(name: str, label: str) -> None:
        state = BreakpointManager(eng).save(name=name)
        state = _strip(state)
        state["name"] = name
        state["description"] = label
        state["library"] = True
        f = out / f"{name}.json"
        f.write_text(json.dumps(state, sort_keys=True, separators=(",", ":"), default=str), encoding="utf-8")
        written.append(f.name)

    aocs = eng.subsystems["aocs"]

    def settle(limit_s: int = 900) -> None:
        """Let a wheel-controlled attitude finish converging before the save.

        The previous card's last command (a mode change, a slew back to nadir)
        can leave the spacecraft mid-transient; COM-007's entry state was saved
        at 33° error and 0.3 °/s, so every load of it raised attitude alarms
        that had nothing to do with the card. Only NOMINAL / FINE_POINT /
        INERTIAL are settled; DETUMBLE and COARSE_SUN are left as found."""
        for _ in range(limit_s):
            st = aocs._state
            if st.mode not in (4, 5, 9) or aocs.get_telemetry().get(0x0217, 0.0) < 0.2:
                return
            fly.run(1)

    for name, fn in methods:
        card = _card_id(name)
        doc = (fn.__doc__ or "").strip().splitlines()
        settle()
        save(f"card-{card}", f"Entry state of {card} (fly-through, {name})" + (f": {doc[0]}" if doc else ""))
        print(f"  {card:9s} saved, flying …", flush=True)
        fn(inst, fly)
    settle()
    save("card-END", "Commissioning complete: NOMINAL hold after COM-013")
    return written


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if the library differs from a fresh build")
    ap.add_argument("--out", default=str(LIBRARY))
    a = ap.parse_args(argv)
    if a.check:
        with tempfile.TemporaryDirectory() as td:
            names = build(Path(td))
            bad = []
            for n in names:
                new = (Path(td) / n).read_bytes()
                old = (Path(a.out) / n).read_bytes() if (Path(a.out) / n).exists() else b""
                if hashlib.sha256(new).digest() != hashlib.sha256(old).digest():
                    bad.append(n)
            if bad:
                print("stale card breakpoints (run tools/card_breakpoints.py):", ", ".join(bad))
                return 1
            print(f"card breakpoints current: {len(names)}")
            return 0
    names = build(Path(a.out))
    print(f"wrote {len(names)} breakpoints to {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
