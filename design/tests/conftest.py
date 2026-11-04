"""Suite-wide test settings.

The rule-based interface proposer runs automatically after every element
create/update/delete (routers/elements.py ``_auto_propose``). Most tests pin the
exact links they create themselves, so the automatic run is off by default in
the suite; the proposer's own tests (tests/test_api/test_interface_proposer_api.py)
switch it back on with ``monkeypatch.setenv("SPACECDF_AUTO_PROPOSE", "1")``.
populate-subsystems and POST /interfaces/propose always run the proposer.
"""
from __future__ import annotations

import os

os.environ.setdefault("SPACECDF_AUTO_PROPOSE", "0")
# Interface requirements generated from accepted links (services/interface_requirements.py):
# off by default for the same reason; tests/test_api/test_electrical_api.py switches it on.
os.environ.setdefault("SPACECDF_AUTO_IRD", "0")
