"""Author ruling Q7 (2026-10-30): the transponder auto-switch is a 24 h
command-loss timer, and its value plus one RSSI threshold live in ttc.yaml.

The switch itself is documented on-board behaviour that the simulator does
not perform yet; these tests pin that the keys exist, carry the ruled values
and pass the strict (extra="forbid") TTC schema.
"""
from pathlib import Path

import pytest
from pydantic import ValidationError

from smo_common.config.loader import load_subsystem_config
from smo_common.config.schemas import TTCConfig

CONFIG = Path(__file__).resolve().parents[2] / "configs" / "eosat1"


def test_ttc_yaml_carries_the_24h_command_loss_timer():
    cfg = load_subsystem_config(CONFIG, "ttc", TTCConfig)
    assert cfg.cmd_loss_switch_timeout_s == 86400
    assert cfg.cmd_loss_rssi_threshold_dbm == -105.0


def test_schema_defaults_match_the_ruling():
    cfg = TTCConfig()
    assert cfg.cmd_loss_switch_timeout_s == 86400
    assert cfg.cmd_loss_rssi_threshold_dbm == -105.0


def test_timer_must_be_positive():
    with pytest.raises(ValidationError):
        TTCConfig(cmd_loss_switch_timeout_s=0)
