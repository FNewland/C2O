"""Shared test fixtures."""
import os
import sys
import struct
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add package source directories to path for testing
for pkg in ["smo-common", "smo-simulator", "smo-gateway", "smo-mcs", "smo-planner",
            "smo-link"]:
    src = Path(__file__).parent.parent / "packages" / pkg / "src"
    if src.exists() and str(src) not in sys.path:
        sys.path.insert(0, str(src))


CONFIG_DIR = str(Path(__file__).parent.parent / "configs" / "eosat1")

# Auto snapshots before injected faults are written to disk
# (smo_simulator/auto_snapshots.py). Keep the test run's out of the
# working tree's workspace/ (one private folder per test process).
os.environ.setdefault("SMO_AUTO_SNAPSHOT_DIR",
                      tempfile.mkdtemp(prefix="smo-auto-snapshots-"))


# ── Test tiers (R4 §6; docs/TESTING.md) ─────────────────────────────
#
# fast    -m "not slow and not e2e"   every push / PR, run with -n auto
# slow    -m "slow"                   nightly: RF DSP, full-system flythroughs,
#                                     engine-boot-heavy modules, smo-link e2e
# e2e     SMO_E2E=1 -m e2e            nightly: Playwright against a live stack
#
# Individual tests may still carry @pytest.mark.slow; whole modules that are
# heavy are marked here by path so the list lives in one place. Paths are
# relative to tests/. A directory entry ends with "/".
_TIER_BY_PATH = {
    # RF DSP: blind receiver alone is ~150 s serial; impairments EVM ~14 s.
    "test_rfsim/test_blind_receiver.py": ("slow", "rf_dsp"),
    "test_rfsim/test_rf_impairments.py": ("slow", "rf_dsp"),
    # Full-system flythroughs and RF-pipeline acceptance runs.
    "test_acceptance/": ("slow",),
    "test_integration/test_commissioning_rf.py": ("slow",),
    "test_integration/test_packet_loss_diagnostics.py": ("slow",),
    "test_integration/test_leop_end_to_end.py": ("slow",),
    "test_planner/test_fly_a_plan.py": ("slow",),
    # smo-link end to end (already marked link_e2e in the module).
    "test_link/test_e2e.py": ("slow",),
}
_TESTS_ROOT = Path(__file__).resolve().parent


def _slow_node_ids() -> set[str]:
    """Node ids listed in tests/slow_tests.txt (individually slow tests)."""
    path = _TESTS_ROOT / "slow_tests.txt"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return set()
    return {ln.split("#", 1)[0].strip() for ln in lines} - {""}


def pytest_collection_modifyitems(config, items):
    """Apply the tier markers: by path (above), by node id (slow_tests.txt),
    and slow to every link_e2e test."""
    slow_ids = _slow_node_ids()
    for item in items:
        if item.nodeid in slow_ids:
            item.add_marker(pytest.mark.slow)
        try:
            rel = Path(str(item.fspath)).resolve().relative_to(_TESTS_ROOT).as_posix()
        except ValueError:
            continue
        for key, marks in _TIER_BY_PATH.items():
            if rel == key or (key.endswith("/") and rel.startswith(key)):
                for m in marks:
                    item.add_marker(getattr(pytest.mark, m))
        if item.get_closest_marker("link_e2e") and not item.get_closest_marker("slow"):
            item.add_marker(pytest.mark.slow)


@pytest.fixture
def config_dir():
    """Return path to eosat1 config directory."""
    return CONFIG_DIR


@pytest.fixture
def mock_engine():
    """Create a mock engine suitable for ServiceDispatcher testing."""
    engine = MagicMock()
    engine.params = {}
    engine._hk_structures = {}
    engine._hk_enabled = {}
    engine._hk_intervals = {}
    engine._get_cuc_time = MagicMock(return_value=1000)
    engine.tm_builder = MagicMock()
    engine.tm_builder._pack_tm = MagicMock(return_value=b'\x00' * 20)
    engine.tm_builder.build_hk_packet = MagicMock(return_value=b'\x00' * 20)
    engine.tm_builder.build_connection_test_report = MagicMock(return_value=b'\x00' * 20)
    engine.tm_builder.build_param_value_report = MagicMock(return_value=b'\x00' * 20)
    engine.tm_builder.build_time_report = MagicMock(return_value=b'\x00' * 20)
    engine.subsystems = {
        "aocs": MagicMock(), "eps": MagicMock(), "payload": MagicMock(),
        "tcs": MagicMock(), "obdh": MagicMock(), "ttc": MagicMock(),
        "prop": MagicMock(),  # Phase D propulsion
    }
    engine._tc_scheduler = MagicMock()
    engine._tm_storage = MagicMock()
    engine.event_types_enabled = set(range(256))

    # Setup eps subsystem mock for power gating tests
    eps_mock = engine.subsystems["eps"]
    eps_mock._state = MagicMock()
    eps_mock._state.power_lines = {}
    eps_mock.handle_command = MagicMock(return_value={"success": True})

    from tests.engine_doubles import wire_mock_engine
    return wire_mock_engine(engine)


@pytest.fixture
def service_dispatcher(mock_engine):
    """Create a ServiceDispatcher with a mock engine."""
    from smo_simulator.service_dispatch import ServiceDispatcher
    return ServiceDispatcher(mock_engine)
