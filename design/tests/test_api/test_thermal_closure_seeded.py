"""Thermal closure on an EOSAT-1-like seeded 6U study (Nov 2026 regression).

Before the fix every node's cold margin was about -68 K and the bus structure's -305 K:
the study's ``spacecraft_class`` defaults to "small", so the envelope fell back to a
1.0 x 1.0 x 1.2 m box (6.8 m2 of radiating area for a 0.28 m2 6U), and the structure
subsystem's mass sat in its own node, leaving the chassis node at 0.05 kg with every
absorbed solar watt on it, which the explicit transient step integrated unstably
(-345 .. +200 degC on one node).
"""
from __future__ import annotations

from tests.test_api.diagram_seed import seed_eosat


async def test_thermal_closure_on_seeded_6u_is_physical(client, study_obj, study):
    await seed_eosat(client, study, verification=False)
    from spacecdf_server.services.analysis_context import build_context
    from spacecdf_server.services.physics_closure import run_thermal_closure

    th = run_thermal_closure(await build_context(study))
    env = th.inputs["envelope_m"]
    assert sorted(round(x, 3) for x in env) == [0.1, 0.226, 0.366], th.inputs["envelope_source"]
    assert 0.25 < th.inputs["external_area_m2"] < 0.32
    chassis = next(n for n in th.nodes if n.kind == "structure")
    assert chassis.mass_kg >= 0.69, "the structure subsystem's mass is the chassis' capacity"
    assert not any(n.domain == "structure" and n.kind == "subsystem" for n in th.nodes)
    for n in th.nodes:
        # physical range: nothing colder than -60 degC or hotter than 120 degC for a 6U in LEO
        assert -60.0 < n.t_cold_c < 60.0, (n.name, n.t_cold_c)
        assert -60.0 < n.t_hot_c < 120.0, (n.name, n.t_hot_c)
        assert n.t_transient_max_c - n.t_transient_min_c < 80.0, (n.name, n.t_transient_min_c, n.t_transient_max_c)
    assert th.worst_margin_c is not None and th.worst_margin_c > -50.0


def test_transient_is_stable_for_a_light_node():
    """A node whose time constant is shorter than the output step must not oscillate."""
    from spacecdf_server.services.thermal_network import ThermalConductance, ThermalNode, solve_transient

    nodes = [ThermalNode(id="chassis", name="c", mass_kg=0.05, specific_heat_j_kg_k=900.0, temperature_c=20.0,
                         power_dissipation_w=0.0, emissivity=0.85, area_m2=1.0, is_radiator=True),
             ThermalNode(id="box", name="b", mass_kg=1.0, specific_heat_j_kg_k=900.0, temperature_c=20.0,
                         power_dissipation_w=5.0, emissivity=0.85, area_m2=0.01, is_radiator=True)]
    tr = solve_transient(nodes, [ThermalConductance("chassis", "box", 5.0)], duration_s=5700.0, dt_s=30.0,
                         eclipse_fraction=0.35, solar_absorbed_w=100.0)
    c = tr.temperatures["chassis"]
    assert min(c) > -273.15 and max(c) < 150.0
    # no step-to-step sign flipping (the unstable Euler signature)
    flips = sum(1 for a, b, d in zip(c, c[1:], c[2:]) if (b - a) * (d - b) < 0)
    assert flips <= 4
