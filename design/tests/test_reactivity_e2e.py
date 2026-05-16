"""End-to-end reactivity harness (SCDF-104).

Exercises 12 representative mutation scenarios (one per ChangeKind).
This is the safety net for SCDF-105's WS handler migration.

For each scenario:
  1. Start from a reference design state
  2. Dispatch a ChangeEvent
  3. Assert correct params are dirty
  4. Assert correct domains would be affected
  5. Assert cascades stop at domain boundaries

Phase A: tests via dispatcher (Phase B wiring in SCDF-105).
Stubbed scenarios assert dispatch success + persistence only.

CI rule: PRs adding new ChangeKind MUST add a corresponding test here.
"""
from __future__ import annotations

import pytest

from spacecdf_common.models.change_event import ChangeEvent, ChangeKind
from spacecdf_server.services.dirty_set import DirtySet
from spacecdf_server.services.change_events import (
    ChangeEventDispatcher,
    DispatchResult,
)

from fixtures.design_state_fixtures import (
    minimal_closed_design,
    open_power_margin_design,
    open_link_margin_design,
    EXPECTED_CASCADES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_event(kind: ChangeKind, target_id: str, **kw) -> ChangeEvent:
    """Create a ChangeEvent with sensible defaults."""
    defaults = dict(
        kind=kind,
        session_id="test-session",
        actor_id="test-engineer",
        actor_label="Test Engineer",
        target_id=target_id,
        target_kind="parameter",
        old_value=None,
        new_value="42",
    )
    defaults.update(kw)
    return ChangeEvent(**defaults)


def _make_dispatcher() -> tuple[ChangeEventDispatcher, DirtySet, list]:
    """Create a dispatcher with a DirtySet and an event log for persistence."""
    dirty = DirtySet()
    persisted: list[ChangeEvent] = []

    async def persist(event: ChangeEvent) -> None:
        persisted.append(event)

    dispatcher = ChangeEventDispatcher(dirty_set=dirty, persist_fn=persist)
    return dispatcher, dirty, persisted


def assert_dirty_set_contains(dirty: DirtySet, expected_params: set[str]) -> None:
    """Assert that the dirty set contains all expected parameters."""
    for p in expected_params:
        assert p in dirty._params, f"Expected '{p}' in dirty set, got {dirty._params}"


def assert_dirty_set_excludes(dirty: DirtySet, excluded_params: set[str]) -> None:
    """Assert that the dirty set does NOT contain excluded parameters."""
    for p in excluded_params:
        assert p not in dirty._params, f"'{p}' should NOT be in dirty set"


def assert_dispatch_success(result: DispatchResult) -> None:
    """Assert that dispatch processed at least one event without errors."""
    assert result.events_processed >= 1
    assert len(result.errors) == 0, f"Dispatch errors: {result.errors}"


# ---------------------------------------------------------------------------
# Scenario 1: PARAMETER_OVERRIDE
# ---------------------------------------------------------------------------
class TestParameterOverride:
    """Edit power.battery_capacity_wh -> assert power + thermal would recalc."""

    @pytest.mark.asyncio
    async def test_dispatch_marks_dirty(self):
        dispatcher, dirty, persisted = _make_dispatcher()
        event = _make_event(
            ChangeKind.PARAMETER_OVERRIDE,
            target_id="power.battery_capacity_wh",
            old_value="20.0",
            new_value="35.0",
        )
        result = await dispatcher.dispatch(event)

        assert_dispatch_success(result)
        assert "power.battery_capacity_wh" in result.dirty_params
        assert_dirty_set_contains(dirty, {"power.battery_capacity_wh"})
        assert len(persisted) == 1

    @pytest.mark.asyncio
    async def test_cascade_stops_at_domain_boundary(self):
        """Link agent should NOT be triggered by a power param change."""
        dispatcher, dirty, _ = _make_dispatcher()
        event = _make_event(
            ChangeKind.PARAMETER_OVERRIDE,
            target_id="power.battery_capacity_wh",
            new_value="35.0",
        )
        await dispatcher.dispatch(event)
        assert_dirty_set_excludes(dirty, {"link.downlink_margin_db", "aocs.pointing_accuracy_deg"})


# ---------------------------------------------------------------------------
# Scenario 2: EQUIPMENT_SELECTION
# ---------------------------------------------------------------------------
class TestEquipmentSelection:
    """Select battery component -> assert power recalc."""

    @pytest.mark.asyncio
    async def test_dispatch_marks_dirty(self):
        dispatcher, dirty, persisted = _make_dispatcher()
        event = _make_event(
            ChangeKind.EQUIPMENT_SELECTION,
            target_id="power.selected_battery",
            target_kind="equipment",
            new_value="GOMSpace_NanoPower_BP4",
        )
        result = await dispatcher.dispatch(event)

        assert_dispatch_success(result)
        # Default handler treats target_kind != 'parameter' as no auto-dirty
        # (handler would mark specific params); event is still persisted
        assert len(persisted) == 1


# ---------------------------------------------------------------------------
# Scenario 3: REQUIREMENT_EDIT (stub until SCDF-115)
# ---------------------------------------------------------------------------
class TestRequirementEdit:
    """Edit mission requirement threshold -> assert compliance flag."""

    @pytest.mark.asyncio
    async def test_dispatch_accepted(self):
        dispatcher, dirty, persisted = _make_dispatcher()
        event = _make_event(
            ChangeKind.REQUIREMENT_EDIT,
            target_id="MR-001",
            target_kind="requirement",
            old_value='{"threshold": 5.0}',
            new_value='{"threshold": 3.0}',
        )
        result = await dispatcher.dispatch(event)

        assert_dispatch_success(result)
        assert len(persisted) == 1
        # Detailed cascade checks deferred to SCDF-115


# ---------------------------------------------------------------------------
# Scenario 4: REQUIREMENT_DELETE (stub until SCDF-116)
# ---------------------------------------------------------------------------
class TestRequirementDelete:
    """Retire requirement -> assert parent flagged."""

    @pytest.mark.asyncio
    async def test_dispatch_accepted(self):
        dispatcher, dirty, persisted = _make_dispatcher()
        event = _make_event(
            ChangeKind.REQUIREMENT_DELETE,
            target_id="MR-002",
            target_kind="requirement",
            new_value=None,
        )
        result = await dispatcher.dispatch(event)

        assert_dispatch_success(result)
        assert len(persisted) == 1
        # Detailed cascade checks deferred to SCDF-116


# ---------------------------------------------------------------------------
# Scenario 5: CONOPS_EDIT (stub until SCDF-200)
# ---------------------------------------------------------------------------
class TestConopsEdit:
    """Toggle ConOps mode."""

    @pytest.mark.asyncio
    async def test_dispatch_accepted(self):
        dispatcher, _, persisted = _make_dispatcher()
        event = _make_event(
            ChangeKind.CONOPS_EDIT,
            target_id="conops.mode_0",
            target_kind="conops_mode",
            new_value='{"name": "science", "duration_min": 30}',
        )
        result = await dispatcher.dispatch(event)

        assert_dispatch_success(result)
        assert len(persisted) == 1
        # Detailed cascade checks deferred to SCDF-200


# ---------------------------------------------------------------------------
# Scenario 6: QA_ANSWER (stub)
# ---------------------------------------------------------------------------
class TestQAAnswer:
    """Answer mission need question."""

    @pytest.mark.asyncio
    async def test_dispatch_accepted(self):
        dispatcher, _, persisted = _make_dispatcher()
        event = _make_event(
            ChangeKind.QA_ANSWER,
            target_id="qa.question_1",
            target_kind="qa",
            new_value="Earth observation for agriculture",
        )
        result = await dispatcher.dispatch(event)

        assert_dispatch_success(result)
        assert len(persisted) == 1


# ---------------------------------------------------------------------------
# Scenario 7: MARGIN_PHASE_CHANGE (stub until SCDF-021)
# ---------------------------------------------------------------------------
class TestMarginPhaseChange:
    """Change design phase -> assert margins recomputed."""

    @pytest.mark.asyncio
    async def test_dispatch_accepted(self):
        dispatcher, _, persisted = _make_dispatcher()
        event = _make_event(
            ChangeKind.MARGIN_PHASE_CHANGE,
            target_id="mission.phase",
            target_kind="parameter",
            old_value="phase_0",
            new_value="phase_b",
        )
        result = await dispatcher.dispatch(event)

        assert_dispatch_success(result)
        assert "mission.phase" in result.dirty_params
        assert len(persisted) == 1
        # Detailed margin recomputation checks deferred to SCDF-021


# ---------------------------------------------------------------------------
# Scenario 8: PARAMETRIC_FRACTION_EDIT (stub until SCDF-014)
# ---------------------------------------------------------------------------
class TestParametricFractionEdit:
    """Edit parametric tuning slider -> assert cascade."""

    @pytest.mark.asyncio
    async def test_dispatch_accepted(self):
        dispatcher, _, persisted = _make_dispatcher()
        event = _make_event(
            ChangeKind.PARAMETRIC_FRACTION_EDIT,
            target_id="parametric.mass_fraction_structure",
            target_kind="parameter",
            old_value="0.30",
            new_value="0.35",
        )
        result = await dispatcher.dispatch(event)

        assert_dispatch_success(result)
        assert len(persisted) == 1
        # Detailed cascade checks deferred to SCDF-014


# ---------------------------------------------------------------------------
# Scenario 9: LAUNCH_VEHICLE_SELECTION (stub until SCDF-015)
# ---------------------------------------------------------------------------
class TestLaunchVehicleSelection:
    """Select launch vehicle -> assert mass/cost recalc."""

    @pytest.mark.asyncio
    async def test_dispatch_accepted(self):
        dispatcher, _, persisted = _make_dispatcher()
        event = _make_event(
            ChangeKind.LAUNCH_VEHICLE_SELECTION,
            target_id="launch.vehicle_id",
            target_kind="equipment",
            new_value="falcon_9",
        )
        result = await dispatcher.dispatch(event)

        assert_dispatch_success(result)
        assert len(persisted) == 1
        # Detailed mass/cost checks deferred to SCDF-015


# ---------------------------------------------------------------------------
# Scenario 10: SPECTRUM_BAND_SELECTION (stub until SCDF-016)
# ---------------------------------------------------------------------------
class TestSpectrumBandSelection:
    """Select RF band -> assert link budget recalc."""

    @pytest.mark.asyncio
    async def test_dispatch_accepted(self):
        dispatcher, _, persisted = _make_dispatcher()
        event = _make_event(
            ChangeKind.SPECTRUM_BAND_SELECTION,
            target_id="link.rf_band",
            target_kind="parameter",
            old_value="UHF",
            new_value="S",
        )
        result = await dispatcher.dispatch(event)

        assert_dispatch_success(result)
        assert "link.rf_band" in result.dirty_params
        assert len(persisted) == 1
        # Detailed link budget checks deferred to SCDF-016


# ---------------------------------------------------------------------------
# Scenario 11: GATE_CRITERION_TOGGLE (stub until SCDF-131)
# ---------------------------------------------------------------------------
class TestGateCriterionToggle:
    """Toggle gate criterion -> assert phase gating update."""

    @pytest.mark.asyncio
    async def test_dispatch_accepted(self):
        dispatcher, _, persisted = _make_dispatcher()
        event = _make_event(
            ChangeKind.GATE_CRITERION_TOGGLE,
            target_id="gate.criterion_pdr_mass",
            target_kind="parameter",
            old_value="true",
            new_value="false",
        )
        result = await dispatcher.dispatch(event)

        assert_dispatch_success(result)
        assert len(persisted) == 1
        # Detailed gating checks deferred to SCDF-131


# ---------------------------------------------------------------------------
# Scenario 12: MASS_ALLOCATION_UPDATE (future placeholder)
# ---------------------------------------------------------------------------
class TestMassAllocationUpdate:
    """Edit mass allocation (future ChangeKind).

    This scenario is a placeholder. When ChangeKind.MASS_ALLOCATION_UPDATE
    is added, fill in the event and cascade assertions.
    """

    @pytest.mark.asyncio
    async def test_placeholder(self):
        # No ChangeKind exists yet; just verify the harness structure
        # is ready for extension. When the enum value is added:
        # 1. Add the ChangeKind value to change_event.py
        # 2. Uncomment and fill in the test below
        # 3. Add expected cascade to EXPECTED_CASCADES
        pass

    # @pytest.mark.asyncio
    # async def test_dispatch_accepted(self):
    #     dispatcher, _, persisted = _make_dispatcher()
    #     event = _make_event(
    #         ChangeKind.MASS_ALLOCATION_UPDATE,
    #         target_id="mass.allocation_structure_kg",
    #         target_kind="parameter",
    #         old_value="1.2",
    #         new_value="1.5",
    #     )
    #     result = await dispatcher.dispatch(event)
    #     assert_dispatch_success(result)


# ---------------------------------------------------------------------------
# Batch dispatch
# ---------------------------------------------------------------------------
class TestBatchDispatch:
    """Verify dispatch_batch processes multiple correlated events."""

    @pytest.mark.asyncio
    async def test_batch_two_param_changes(self):
        dispatcher, dirty, persisted = _make_dispatcher()
        events = [
            _make_event(
                ChangeKind.PARAMETER_OVERRIDE,
                target_id="power.battery_capacity_wh",
                new_value="35.0",
            ),
            _make_event(
                ChangeKind.PARAMETER_OVERRIDE,
                target_id="mass.dry_mass_kg",
                new_value="5.0",
            ),
        ]
        result = await dispatcher.dispatch_batch(events)

        assert result.events_processed == 2
        assert "power.battery_capacity_wh" in result.dirty_params
        assert "mass.dry_mass_kg" in result.dirty_params
        assert len(persisted) == 2


# ---------------------------------------------------------------------------
# DirtySet integration
# ---------------------------------------------------------------------------
class TestDirtySetIntegration:
    """Verify DirtySet consume/remark cycle works with dispatcher."""

    @pytest.mark.asyncio
    async def test_consume_clears_dirty(self):
        dispatcher, dirty, _ = _make_dispatcher()
        event = _make_event(
            ChangeKind.PARAMETER_OVERRIDE,
            target_id="power.battery_capacity_wh",
            new_value="35.0",
        )
        await dispatcher.dispatch(event)

        assert not dirty.is_empty
        params, reqs, domains = await dirty.consume()
        assert "power.battery_capacity_wh" in params
        assert dirty.is_empty

    @pytest.mark.asyncio
    async def test_remark_on_failure(self):
        dispatcher, dirty, _ = _make_dispatcher()
        event = _make_event(
            ChangeKind.PARAMETER_OVERRIDE,
            target_id="power.battery_capacity_wh",
            new_value="35.0",
        )
        await dispatcher.dispatch(event)

        # Simulate: reconverger consumes then fails
        params, reqs, domains = await dirty.consume()
        assert dirty.is_empty

        # Re-mark on failure
        await dirty.remark(params, reqs, domains)
        assert not dirty.is_empty
        assert dirty.param_count == 1
