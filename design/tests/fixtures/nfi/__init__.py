"""Shared test fixture of the Northern Fire and Ice teaching mission (W0.4; prefix ``nfi``).

Files (copied unchanged from the frozen teaching baseline, 2026-11-10):

``NUMBERS.yaml``          key numbers, the single source of truth (wins over every other file)
``mission.yaml``          wizard inputs and the mission definition / mission need
``equipment.yaml``        product tree and equipment selections (mass, ON power, qty, TRL, maturity)
``modes.yaml``            mode set, shares of orbit, mode x unit power matrix, extra transitions
``requirements.yaml``     216 requirements (stakeholder needs, objectives, import order)
``hk_sids.yaml``          housekeeping SIDs (loaded by W3, not by the seed yet)
``risks.yaml``            risk register
``trades.yaml``           trade studies T-01... (loaded by W6, not by the seed yet)
``ground_stations.yaml``  four generic Canadian sites with contact statistics
``logbook.yaml``          decision records of the baseline
``roundtrip_checklist.yaml``  Save/Load checks used by the dry run (W13)

``seed.py`` builds the study through the API in stages S0..S4 (``seed_nfi(client, stage)``);
``load(name)`` parses one file. See design/docs/dev/W0_SEAMS.md, section "Fixture".

Refreshing: copy the newer baseline files over these (same names) and run
``pytest tests/fixtures/nfi``; ``test_seed.py`` pins the key numbers against ``NUMBERS.yaml``.
"""
from .seed import STAGES, NfiSeed, SeedError, load, seed_nfi  # noqa: F401
