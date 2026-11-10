"""Shared test fixture of the Northern Fire and Ice teaching mission (W0.4; prefix ``nfi``).

Files (copied unchanged from the frozen teaching baseline, 2026-11-10; wave 3 step 0 switched
``NUMBERS``, ``requirements``, ``risks`` and ``trades`` to the v2 baseline and added ``functions``,
``budgets``, ``stakeholders`` and ``vv_plan``; v2 has no copy of the other files):

``NUMBERS.yaml``          key numbers, the single source of truth (wins over every other file)
``mission.yaml``          wizard inputs and the mission definition / mission need
``equipment.yaml``        product tree and equipment selections (mass, ON power, qty, TRL, maturity)
``modes.yaml``            mode set, shares of orbit, mode x unit power matrix, extra transitions
``requirements.yaml``     v2: 302 requirements with the v2 fields (stakeholder needs, objectives, import order)
``hk_sids.yaml``          housekeeping SIDs (loaded at S4)
``risks.yaml``            v2: 37 risks with residual L/C, change records, readiness (TRL)
``trades.yaml``           v2: system and architecture trades plus the subsystem trades T-01 … T-08
``functions.yaml``        v2: elements, functions, enabling processes, allocations, exchanges, N² (3.R1)
``budgets.yaml``          v2: margin policy, mass / power / data / performance budgets and allocations
``stakeholders.yaml``     v2: stakeholders, needs, MOEs, need validation, validation events (3.S3, 3.S5)
``vv_plan.yaml``          v2: V levels, model philosophy, events, matrix, validation plan, ConOps scenarios
``ground_stations.yaml``  four generic Canadian sites with contact statistics
``logbook.yaml``          decision records of the baseline
``roundtrip_checklist.yaml``  Save/Load checks used by the dry run (W13)

``seed.py`` builds the study through the API in stages S0..S4 (``seed_nfi(client, stage,
recording=False)``; ``recording=True`` is the walkthrough's seed);
``load(name)`` parses one file. See design/docs/dev/W0_SEAMS.md, section "Fixture".

Refreshing: copy the newer baseline files over these (same names) and run
``pytest tests/fixtures/nfi``; ``test_seed.py`` pins the key numbers against ``NUMBERS.yaml``.
"""
from .seed import ELEMENT_IDS, STAGES, NfiSeed, SeedError, load, seed_nfi  # noqa: F401
