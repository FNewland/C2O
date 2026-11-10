"""SpaceCDF — link-budget cases: band presets and the link equation (W1.04 / W4.04, Nov 2026).

A link case is one direction (downlink or uplink) to one ground station at one elevation and one
rate tier. ``compute(case, altitude_km)`` runs the cascade the Link Budget tool shows
(ECSS-E-ST-50-05C terms)::

    EIRP   = 10 log10(P_tx) + G_tx - L_tx
    FSPL   = 32.45 + 20 log10(d_km) + 20 log10(f_MHz)       d from altitude and elevation
    G/T    = G_rx - L_rx - 10 log10(T_sys)
    C/N0   = EIRP - FSPL - L_pol - L_atm - L_point - L_other + G/T + 228.6
    Eb/N0  = C/N0 - 10 log10(R)
    margin = Eb/N0 - (Eb/N0)_req - L_impl

``PRESETS`` are starting points per band and direction, so a UHF mission's uplink starts at
450 MHz and 9.6 kbit/s instead of the S-band telecommand values (VIDEO_REVIEW §1.2). The
spacecraft antenna gain carries the 3 dB pattern allowance of a body-mounted dipole at low
elevation. Pure functions.
"""
from __future__ import annotations

import math
from typing import Any

R_EARTH_KM = 6378.137
BOLTZMANN_DBW = -228.6
DIRECTIONS = ("downlink", "uplink")

#: Input fields of a case (the columns of ``link_budgets``) with their defaults.
INPUTS: dict[str, Any] = {
    "frequency_mhz": 401.5, "data_rate_bps": 9600.0, "tx_power_w": 1.0, "tx_antenna_gain_dbi": 0.0,
    "tx_losses_db": 0.0, "elevation_deg": 10.0, "slant_range_km": 0.0, "polarisation_loss_db": 0.0,
    "atmospheric_loss_db": 0.0, "pointing_loss_db": 0.0, "other_losses_db": 0.0, "rx_antenna_gain_dbi": 0.0,
    "rx_losses_db": 0.0, "system_noise_temp_k": 290.0, "required_ebn0_db": 0.0, "implementation_loss_db": 0.0,
}

_UHF_DOWN = {"frequency_mhz": 401.5, "data_rate_bps": 9600.0, "tx_power_w": 1.0, "tx_antenna_gain_dbi": -3.0,
             "tx_losses_db": 1.0, "polarisation_loss_db": 3.0, "atmospheric_loss_db": 1.0, "pointing_loss_db": 0.5,
             "rx_antenna_gain_dbi": 15.0, "rx_losses_db": 0.3, "system_noise_temp_k": 300.0,
             "required_ebn0_db": 6.0, "implementation_loss_db": 2.0,
             "modulation": "GMSK or BPSK", "coding": "RS(255,223)"}
_UHF_UP = {"frequency_mhz": 450.0, "data_rate_bps": 9600.0, "tx_power_w": 25.0, "tx_antenna_gain_dbi": 15.0,
           "tx_losses_db": 1.5, "polarisation_loss_db": 3.0, "atmospheric_loss_db": 1.0, "pointing_loss_db": 0.5,
           "rx_antenna_gain_dbi": -3.0, "rx_losses_db": 1.0, "system_noise_temp_k": 600.0,
           "required_ebn0_db": 10.6, "implementation_loss_db": 2.0, "modulation": "GMSK", "coding": "uncoded"}

PRESETS: dict[str, dict[str, dict[str, Any]]] = {
    "UHF": {"downlink": _UHF_DOWN, "uplink": _UHF_UP},
    "VHF": {
        "downlink": {**_UHF_DOWN, "frequency_mhz": 137.5, "rx_antenna_gain_dbi": 12.0, "system_noise_temp_k": 1000.0,
                     "atmospheric_loss_db": 1.5},
        "uplink": {**_UHF_UP, "frequency_mhz": 149.0, "tx_antenna_gain_dbi": 12.0, "system_noise_temp_k": 1500.0,
                   "atmospheric_loss_db": 1.5},
    },
    "S": {
        "downlink": {"frequency_mhz": 2250.0, "data_rate_bps": 1e6, "tx_power_w": 2.0, "tx_antenna_gain_dbi": 6.0,
                     "tx_losses_db": 1.5, "polarisation_loss_db": 0.3, "atmospheric_loss_db": 0.5,
                     "pointing_loss_db": 1.0, "rx_antenna_gain_dbi": 35.0, "rx_losses_db": 0.0,
                     "system_noise_temp_k": 150.0, "required_ebn0_db": 4.0, "implementation_loss_db": 2.0,
                     "modulation": "BPSK", "coding": "convolutional r1/2"},
        "uplink": {"frequency_mhz": 2050.0, "data_rate_bps": 4000.0, "tx_power_w": 20.0, "tx_antenna_gain_dbi": 35.0,
                   "tx_losses_db": 1.5, "polarisation_loss_db": 0.3, "atmospheric_loss_db": 0.5,
                   "pointing_loss_db": 1.0, "rx_antenna_gain_dbi": 6.0, "rx_losses_db": 0.0,
                   "system_noise_temp_k": 600.0, "required_ebn0_db": 9.6, "implementation_loss_db": 2.0,
                   "modulation": "BPSK", "coding": "uncoded"},
    },
    "X": {
        "downlink": {"frequency_mhz": 8200.0, "data_rate_bps": 50e6, "tx_power_w": 2.0, "tx_antenna_gain_dbi": 10.0,
                     "tx_losses_db": 1.0, "polarisation_loss_db": 0.3, "atmospheric_loss_db": 1.0,
                     "pointing_loss_db": 1.0, "rx_antenna_gain_dbi": 42.0, "rx_losses_db": 0.0,
                     "system_noise_temp_k": 200.0, "required_ebn0_db": 4.5, "implementation_loss_db": 2.0,
                     "modulation": "QPSK", "coding": "LDPC"},
        "uplink": {"frequency_mhz": 7190.0, "data_rate_bps": 64000.0, "tx_power_w": 50.0, "tx_antenna_gain_dbi": 42.0,
                   "tx_losses_db": 1.5, "polarisation_loss_db": 0.3, "atmospheric_loss_db": 1.0,
                   "pointing_loss_db": 1.0, "rx_antenna_gain_dbi": 6.0, "rx_losses_db": 0.0,
                   "system_noise_temp_k": 600.0, "required_ebn0_db": 9.6, "implementation_loss_db": 2.0,
                   "modulation": "BPSK", "coding": "uncoded"},
    },
}

#: Frequency ranges (MHz) per band, to name the band of a study link that has only frequencies.
BAND_RANGES = (("VHF", 30.0, 300.0), ("UHF", 300.0, 1000.0), ("L", 1000.0, 2000.0), ("S", 2000.0, 4000.0),
               ("C", 4000.0, 8000.0), ("X", 8000.0, 12000.0), ("Ku", 12000.0, 18000.0), ("Ka", 26500.0, 40000.0))


def band_of(freq_mhz: float | None) -> str | None:
    if not freq_mhz:
        return None
    for name, lo, hi in BAND_RANGES:
        if lo <= freq_mhz < hi:
            return name
    return None


def preset(band: str | None, direction: str) -> dict[str, Any]:
    """The preset of ``band`` (UHF when unknown) for ``direction``."""
    b = (band or "").upper()
    b = {"KA": "Ka", "KU": "Ku"}.get(b, b)
    table = PRESETS.get(b) or PRESETS["UHF"]
    return {"band": b if b in PRESETS else "UHF", "direction": direction,
            **dict(table["uplink" if direction == "uplink" else "downlink"])}


def study_preset(link: dict[str, Any] | None, direction: str) -> dict[str, Any]:
    """The starting values of the Link Budget tool for a study: the band preset of the study's
    link (``requirements.link``), overlaid with what the study has chosen for that direction."""
    link = dict(link or {})
    band = link.get("band") or band_of(link.get("downlink_frequency_mhz")) or band_of(link.get("uplink_frequency_mhz"))
    p = preset(band, direction)
    if direction == "downlink":
        for src, dst in (("downlink_frequency_mhz", "frequency_mhz"), ("downlink_rate_bps", "data_rate_bps"),
                         ("tx_power_w", "tx_power_w"), ("tx_antenna_gain_dbi", "tx_antenna_gain_dbi"),
                         ("tx_losses_db", "tx_losses_db"), ("rx_antenna_gain_dbi", "rx_antenna_gain_dbi"),
                         ("system_noise_temp_k", "system_noise_temp_k"), ("slant_range_km", "slant_range_km"),
                         ("required_ebn0_db", "required_ebn0_db")):
            if isinstance(link.get(src), (int, float)):
                p[dst] = float(link[src])
    else:
        for src, dst in (("uplink_frequency_mhz", "frequency_mhz"), ("uplink_rate_bps", "data_rate_bps")):
            if isinstance(link.get(src), (int, float)):
                p[dst] = float(link[src])
    return p


def slant_range_km(altitude_km: float, elevation_deg: float) -> float:
    e = math.radians(elevation_deg)
    return math.sqrt((R_EARTH_KM + altitude_km) ** 2 - (R_EARTH_KM * math.cos(e)) ** 2) - R_EARTH_KM * math.sin(e)


def fspl_db(d_km: float, f_mhz: float) -> float:
    return 32.45 + 20 * math.log10(d_km) + 20 * math.log10(f_mhz)


def _f(case: dict[str, Any], k: str) -> float:
    v = case.get(k)
    try:
        return float(v) if v is not None else float(INPUTS[k])
    except (TypeError, ValueError):
        return float(INPUTS[k])


def compute(case: dict[str, Any], altitude_km: float | None = None) -> dict[str, Any]:
    """The cascade of a case. The slant range is the case's, else the one at its elevation
    from ``altitude_km``. Raises ValueError on a non-positive power, rate, frequency or range."""
    p, r, f, t = _f(case, "tx_power_w"), _f(case, "data_rate_bps"), _f(case, "frequency_mhz"), _f(case, "system_noise_temp_k")
    if min(p, r, f, t) <= 0:
        raise ValueError("transmit power, data rate, frequency and noise temperature must be positive")
    d = _f(case, "slant_range_km")
    if d <= 0:
        if not altitude_km or altitude_km <= 0:
            raise ValueError("give a slant range or the orbit altitude")
        d = slant_range_km(float(altitude_km), _f(case, "elevation_deg"))
    eirp = 10 * math.log10(p) + _f(case, "tx_antenna_gain_dbi") - _f(case, "tx_losses_db")
    fspl = fspl_db(d, f)
    path = (_f(case, "polarisation_loss_db") + _f(case, "atmospheric_loss_db") + _f(case, "pointing_loss_db")
            + _f(case, "other_losses_db"))
    gt = _f(case, "rx_antenna_gain_dbi") - _f(case, "rx_losses_db") - 10 * math.log10(t)
    cn0 = eirp - fspl - path + gt - BOLTZMANN_DBW
    ebn0 = cn0 - 10 * math.log10(r)
    margin = ebn0 - _f(case, "required_ebn0_db") - _f(case, "implementation_loss_db")
    return {"slant_range_km": round(d, 1), "eirp_dbw": round(eirp, 2), "fspl_db": round(fspl, 2),
            "path_losses_db": round(path, 2), "g_over_t_dbk": round(gt, 2), "cn0_dbhz": round(cn0, 2),
            "ebn0_db": round(ebn0, 2), "margin_db": round(margin, 2),
            "closes": margin >= 0, "meets_3db": margin >= 3.0}
