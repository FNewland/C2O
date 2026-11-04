"""aocs.yaml ``control:`` (2026-11): per-mode gains / dwell / power / pointing
sigma and the transition guards are configuration; the EOSAT-1 values are the
former code defaults, so behaviour is unchanged."""
from pathlib import Path

import pytest
import yaml

from smo_common.config.schemas import AOCSConfig
from smo_simulator.models import aocs_basic as ab
from smo_simulator.models.aocs_basic import AOCSBasicModel

CFG = Path(__file__).resolve().parents[2] / "configs" / "eosat1" / "subsystems" / "aocs.yaml"


def _model(cfg: dict) -> AOCSBasicModel:
    m = AOCSBasicModel()
    m.configure(AOCSConfig.model_validate(cfg).model_dump())
    return m


def test_eosat1_control_block_equals_the_code_defaults():
    m = _model(yaml.safe_load(CFG.read_text()))
    bare = AOCSBasicModel()
    assert m._mode_ctrl == bare._mode_ctrl == ab._MODE_CTRL
    assert m._min_dwell == bare._min_dwell == ab._MIN_DWELL
    assert m._mode_power_w == ab._MODE_POWER_W
    assert m._mode_err_sigma == ab._MODE_ERR_SIGMA_DEG
    assert m._guards == AOCSBasicModel.TRANSITION_DEFAULTS


def test_control_overrides_reach_the_model():
    cfg = yaml.safe_load(CFG.read_text())
    cfg["control"] = {"modes": {"NOMINAL": {"omega_n_rad_s": 0.05, "power_w": 7.5}},
                      "transitions": {"detumble_exit_rate_dps": 0.8}}
    m = _model(cfg)
    assert m._mode_ctrl[ab.MODE_NOMINAL] == (0.05, 0.70)
    assert m._mode_power_w[ab.MODE_NOMINAL] == 7.5
    assert m._guards["detumble_exit_rate_dps"] == 0.8
    assert m._mode_gains(ab.MODE_NOMINAL)[0] == 0.05


def test_unknown_mode_or_guard_is_a_load_error():
    with pytest.raises(Exception):
        AOCSConfig.model_validate({"control": {"modes": {"HOVER": {"zeta": 1.0}}}})
    with pytest.raises(Exception):
        AOCSConfig.model_validate({"control": {"transitions": {"detumble_rate": 1.0}}})
