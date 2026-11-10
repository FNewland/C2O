"""SpaceCDF — disposal (post-mission decay) model with drag-augmentation devices.

A calibrated, deterministic lifetime model for LEO disposal analysis (W5.02):

* **Density**: NRLMSIS 2.1 global mean (all latitudes, longitudes, local times; four seasons),
  tabulated every 10 km from 150 to 720 km for F10.7 = 65-230 sfu, Ap = 12. Interpolated
  bilinearly in log-density, extrapolated linearly in log-density outside the table.
* **Decay**: circular orbit, da/dt = -rho sqrt(mu a) Cd A/m, Cd = 2.2, one-day steps above 300 km
  and 0.1-day steps below, stopped at 150 km (re-entry follows within days).
* **Solar activity**: the NOAA SWPC cycle-25 prediction (monthly F10.7, 2026-05 to 2030-12) and,
  after it, cycle 26 onward as a Hathaway-shape cycle starting 2030.9 with three amplitudes
  (strong SSN 160, nominal SSN 115, weak SSN 80); F10.7 = 63.7 + 0.728 R + 8.9e-4 R^2.
* **Drag sail**: tumbling/flutter-averaged effective area = 0.38 x the deployed sail area (a
  calibration on the CanX-7 re-entry: 3.75 kg, 4 m^2 sail, 4.97 y) plus 0.05 m^2 for the bus.

It is a screening model for design reviews. A licence application quotes the result of a
standard tool (ESA DRAMA/OSCAR or NASA DAS); the reports carry that result as evidence when the
team imports it (services/licensing.py) and show this model's numbers beside it.
"""
from __future__ import annotations

import math
from functools import lru_cache
from dataclasses import asdict, dataclass, field

MU = 3.986004418e14          # m^3/s^2
RE_M = 6378137.0             # m (equatorial radius; the density table is in geodetic altitude)
CD_DEFAULT = 2.2
SAIL_EFFECTIVE_FRACTION = 0.38   # CanX-7 calibration (see module docstring)
BUS_AREA_WITH_SAIL_M2 = 0.05     # bus contribution added to the sail's effective area
#: tumbling-averaged area of a 3U bus with two deployed wings (research range 0.04-0.12 m^2)
BUS_AREA_BOUNDS_M2 = (0.04, 0.08, 0.12)

#: cycle-26 amplitude scenarios (peak smoothed sunspot number)
SOLAR_SCENARIOS: dict[str, float] = {"strong": 160.0, "nominal": 115.0, "weak": 80.0}

# ISED Decision on space debris mitigation (April 2026) and the N2 space-station conditions.
# The decision number is quoted as SMSE-009-26 by ISED's page and SMSE-005-26 by one secondary
# source: to be confirmed before filing.
ISED_RULES = {
    "disposal_max_years": 5.0,
    "disposal_probability_min": 0.90,
    "collision_probability_max_large": 1e-3,    # objects >= 10 cm, operational life
    "collision_probability_max_small": 1e-2,    # objects < 10 cm
    "apogee_without_propulsion_max_km": 600.0,
    "trackable_min_dimension_cm": 10.0,
    "environment_assessment_km": 30.0,
    "decision": "ISED decision on space debris mitigation, April 2026 (number SMSE-009-26 or SMSE-005-26: to be confirmed)",
    "conditions": "ISED CPC-2-6-02 Issue 7 (April 2026) and the N2 space station licence conditions",
}

_ALTS = [150.0 + 10.0 * i for i in range(58)]
#: log10 density (kg/m^3) by F10.7, NRLMSIS 2.1 global mean, Ap 12
_LOG_RHO: list[tuple[int, tuple[float, ...]]] = [
    (65, (-8.8176, -9.0483, -9.2553, -9.4454, -9.6227, -9.7897, -9.9483, -10.0996, -10.2447, -10.3841, -10.5185, -10.6484, -10.7742, -10.8963, -11.0150, -11.1308, -11.2438, -11.3543, -11.4626, -11.5689, -11.6732, -11.7758, -11.8769, -11.9764, -12.0744, -12.1711, -12.2665, -12.3605, -12.4532, -12.5446, -12.6347, -12.7233, -12.8105, -12.8962, -12.9803, -13.0627, -13.1434, -13.2222, -13.2990, -13.3736, -13.4461, -13.5163, -13.5841, -13.6494, -13.7122, -13.7724, -13.8299, -13.8849, -13.9373, -13.9872, -14.0346, -14.0796, -14.1224, -14.1630, -14.2016, -14.2383, -14.2732, -14.3065)),
    (70, (-8.8152, -9.0439, -9.2486, -9.4361, -9.6105, -9.7746, -9.9301, -10.0785, -10.2205, -10.3571, -10.4887, -10.6158, -10.7390, -10.8585, -10.9748, -11.0881, -11.1987, -11.3069, -11.4129, -11.5168, -11.6190, -11.7194, -11.8182, -11.9156, -12.0115, -12.1062, -12.1995, -12.2916, -12.3825, -12.4721, -12.5605, -12.6476, -12.7334, -12.8179, -12.9009, -12.9825, -13.0624, -13.1407, -13.2173, -13.2920, -13.3648, -13.4356, -13.5042, -13.5706, -13.6347, -13.6964, -13.7558, -13.8127, -13.8672, -13.9193, -13.9690, -14.0163, -14.0614, -14.1043, -14.1451, -14.1840, -14.2210, -14.2562)),
    (80, (-8.8101, -9.0354, -9.2358, -9.4185, -9.5877, -9.7464, -9.8966, -10.0395, -10.1763, -10.3076, -10.4341, -10.5563, -10.6747, -10.7896, -10.9013, -11.0101, -11.1164, -11.2203, -11.3220, -11.4218, -11.5199, -11.6162, -11.7111, -11.8045, -11.8966, -11.9875, -12.0771, -12.1656, -12.2530, -12.3393, -12.4245, -12.5086, -12.5915, -12.6734, -12.7540, -12.8335, -12.9117, -12.9885, -13.0640, -13.1380, -13.2105, -13.2814, -13.3506, -13.4181, -13.4837, -13.5474, -13.6091, -13.6687, -13.7263, -13.7818, -13.8351, -13.8863, -13.9354, -13.9823, -14.0272, -14.0701, -14.1111, -14.1503)),
    (90, (-8.8050, -9.0270, -9.2236, -9.4020, -9.5666, -9.7206, -9.8660, -10.0042, -10.1363, -10.2630, -10.3850, -10.5029, -10.6170, -10.7277, -10.8354, -10.9403, -11.0427, -11.1428, -11.2408, -11.3370, -11.4314, -11.5241, -11.6155, -11.7054, -11.7941, -11.8815, -11.9679, -12.0531, -12.1373, -12.2205, -12.3027, -12.3839, -12.4641, -12.5433, -12.6215, -12.6987, -12.7748, -12.8499, -12.9238, -12.9965, -13.0680, -13.1382, -13.2070, -13.2745, -13.3404, -13.4048, -13.4676, -13.5286, -13.5880, -13.6456, -13.7013, -13.7552, -13.8072, -13.8573, -13.9055, -13.9518, -13.9963, -14.0389)),
    (100, (-8.7999, -9.0188, -9.2118, -9.3863, -9.5469, -9.6967, -9.8378, -9.9718, -10.0997, -10.2223, -10.3404, -10.4543, -10.5646, -10.6717, -10.7758, -10.8771, -10.9761, -11.0728, -11.1675, -11.2604, -11.3515, -11.4411, -11.5293, -11.6162, -11.7017, -11.7862, -11.8695, -11.9518, -12.0331, -12.1135, -12.1929, -12.2714, -12.3490, -12.4258, -12.5016, -12.5765, -12.6506, -12.7236, -12.7958, -12.8669, -12.9370, -13.0060, -13.0740, -13.1407, -13.2063, -13.2705, -13.3335, -13.3950, -13.4552, -13.5138, -13.5710, -13.6265, -13.6804, -13.7327, -13.7833, -13.8322, -13.8794, -13.9249)),
    (120, (-8.7896, -9.0028, -9.1894, -9.3570, -9.5104, -9.6530, -9.7869, -9.9136, -10.0344, -10.1501, -10.2613, -10.3686, -10.4725, -10.5732, -10.6712, -10.7665, -10.8596, -10.9506, -11.0396, -11.1269, -11.2126, -11.2968, -11.3796, -11.4612, -11.5416, -11.6208, -11.6991, -11.7763, -11.8527, -11.9281, -12.0028, -12.0766, -12.1496, -12.2218, -12.2933, -12.3641, -12.4341, -12.5033, -12.5718, -12.6396, -12.7065, -12.7727, -12.8380, -12.9025, -12.9662, -13.0289, -13.0907, -13.1516, -13.2114, -13.2702, -13.3279, -13.3845, -13.4400, -13.4942, -13.5472, -13.5989, -13.6493, -13.6984)),
    (140, (-8.7792, -8.9872, -9.1681, -9.3297, -9.4771, -9.6136, -9.7414, -9.8622, -9.9771, -10.0870, -10.1927, -10.2946, -10.3931, -10.4887, -10.5816, -10.6721, -10.7603, -10.8466, -10.9310, -11.0138, -11.0950, -11.1748, -11.2533, -11.3306, -11.4067, -11.4818, -11.5559, -11.6290, -11.7013, -11.7728, -11.8434, -11.9133, -11.9825, -12.0510, -12.1187, -12.1859, -12.2523, -12.3181, -12.3833, -12.4478, -12.5117, -12.5750, -12.6376, -12.6995, -12.7607, -12.8213, -12.8811, -12.9403, -12.9986, -13.0562, -13.1130, -13.1690, -13.2241, -13.2783, -13.3316, -13.3840, -13.4354, -13.4857)),
    (160, (-8.7689, -8.9719, -9.1477, -9.3041, -9.4462, -9.5774, -9.7001, -9.8158, -9.9258, -10.0310, -10.1319, -10.2293, -10.3234, -10.4147, -10.5034, -10.5898, -10.6741, -10.7565, -10.8371, -10.9162, -10.9937, -11.0699, -11.1448, -11.2185, -11.2912, -11.3628, -11.4335, -11.5033, -11.5722, -11.6404, -11.7078, -11.7744, -11.8404, -11.9057, -11.9704, -12.0344, -12.0979, -12.1607, -12.2230, -12.2847, -12.3459, -12.4065, -12.4665, -12.5259, -12.5848, -12.6431, -12.7009, -12.7580, -12.8146, -12.8705, -12.9258, -12.9804, -13.0344, -13.0877, -13.1403, -13.1922, -13.2433, -13.2936)),
    (180, (-8.7586, -8.9571, -9.1282, -9.2799, -9.4173, -9.5440, -9.6622, -9.7736, -9.8794, -9.9804, -10.0775, -10.1710, -10.2614, -10.3491, -10.4343, -10.5173, -10.5983, -10.6774, -10.7549, -10.8308, -10.9053, -10.9785, -11.0504, -11.1212, -11.1910, -11.2598, -11.3277, -11.3947, -11.4608, -11.5262, -11.5909, -11.6549, -11.7182, -11.7809, -11.8430, -11.9044, -11.9654, -12.0257, -12.0855, -12.1448, -12.2036, -12.2619, -12.3196, -12.3769, -12.4336, -12.4899, -12.5456, -12.6008, -12.6555, -12.7098, -12.7634, -12.8166, -12.8692, -12.9212, -12.9726, -13.0235, -13.0738, -13.1235)),
    (200, (-8.7485, -8.9427, -9.1094, -9.2569, -9.3902, -9.5128, -9.6271, -9.7347, -9.8369, -9.9345, -10.0281, -10.1184, -10.2057, -10.2903, -10.3726, -10.4527, -10.5309, -10.6074, -10.6822, -10.7555, -10.8275, -10.8981, -10.9676, -11.0360, -11.1034, -11.1698, -11.2354, -11.3001, -11.3639, -11.4271, -11.4895, -11.5512, -11.6124, -11.6728, -11.7327, -11.7921, -11.8509, -11.9091, -11.9669, -12.0241, -12.0808, -12.1371, -12.1929, -12.2482, -12.3031, -12.3575, -12.4115, -12.4650, -12.5180, -12.5706, -12.6227, -12.6744, -12.7256, -12.7763, -12.8265, -12.8762, -12.9255, -12.9742)),
    (230, (-8.7337, -8.9219, -9.0827, -9.2244, -9.3522, -9.4696, -9.5790, -9.6819, -9.7795, -9.8727, -9.9623, -10.0485, -10.1320, -10.2129, -10.2917, -10.3683, -10.4432, -10.5164, -10.5880, -10.6582, -10.7271, -10.7948, -10.8614, -10.9269, -10.9915, -11.0551, -11.1178, -11.1798, -11.2409, -11.3014, -11.3611, -11.4202, -11.4787, -11.5366, -11.5939, -11.6506, -11.7069, -11.7626, -11.8178, -11.8726, -11.9269, -11.9807, -12.0341, -12.0871, -12.1397, -12.1918, -12.2435, -12.2948, -12.3457, -12.3962, -12.4463, -12.4959, -12.5452, -12.5941, -12.6425, -12.6906, -12.7382, -12.7854)),
]
_F107S = [f for f, _ in _LOG_RHO]

#: NOAA SWPC predicted F10.7 (monthly, 2026-05 .. 2030-12; prediction issued 2026)
_PRED_START = 2026 + 4.5 / 12.0
_PRED_F107 = [
    130.8, 129.7, 127.1, 124.9, 123.8, 122.9, 123.0, 123.2, 122.9, 122.1, 120.8, 118.7,
    116.3, 113.7, 111.1, 108.5, 106.0, 103.8, 101.7, 99.8, 98.0, 96.2, 94.7, 93.1,
    91.6, 90.1, 88.8, 87.5, 86.2, 85.1, 84.0, 82.9, 81.9, 81.0, 80.2, 79.3,
    78.6, 77.8, 77.1, 76.5, 75.8, 75.3, 74.7, 74.2, 73.8, 73.3, 72.9, 72.6,
    72.2, 71.9, 71.6, 71.3, 71.0, 70.8, 70.5, 70.3,
]
_PRED_END = _PRED_START + (len(_PRED_F107) - 1) / 12.0
_CYCLE26_START = 2030.9


def _interp1(xs: list[float], ys: list[float], x: float) -> float:
    """Linear interpolation, linear extrapolation beyond the ends."""
    if x <= xs[0]:
        i = 0
    elif x >= xs[-1]:
        i = len(xs) - 2
    else:
        lo, hi = 0, len(xs) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if xs[mid] <= x:
                lo = mid
            else:
                hi = mid
        i = lo
    x0, x1 = xs[i], xs[i + 1]
    t = (x - x0) / (x1 - x0)
    return ys[i] + t * (ys[i + 1] - ys[i])


def density_kg_m3(altitude_km: float, f107: float) -> float:
    """NRLMSIS 2.1 global-mean density at ``altitude_km`` for a daily/81-day F10.7 of ``f107``."""
    f = min(max(f107, _F107S[0]), _F107S[-1])
    col = [_interp1(_ALTS, list(row), altitude_km) for _, row in _LOG_RHO]
    return 10.0 ** _interp1([float(v) for v in _F107S], col, f)


def _hathaway(t: float, t0: float, rmax: float) -> float:
    x = (t - t0) * 12.0
    if x <= 0:
        return 0.0
    b, c = 48.0, 0.71
    if (x / b) ** 2 > 600.0:
        return 0.0
    # peak of x^3 / (exp((x/b)^2) - c) on the grid used for the normalisation
    return rmax * (x ** 3 / (math.exp((x / b) ** 2) - c)) / _HATH_PEAK


def _hath_peak() -> float:
    b, c = 48.0, 0.71
    best = 0.0
    for k in range(2000):
        x = 0.1 + k * (140.0 - 0.1) / 1999.0
        best = max(best, x ** 3 / (math.exp((x / b) ** 2) - c))
    return best


_HATH_PEAK = _hath_peak()


def ssn_to_f107(r: float) -> float:
    return 63.7 + 0.728 * r + 8.9e-4 * r * r


def f107_at(year: float, scenario: str = "nominal") -> float:
    """Monthly-smoothed F10.7 at decimal ``year`` for a cycle-26 amplitude ``scenario``."""
    rmax = SOLAR_SCENARIOS.get(scenario, SOLAR_SCENARIOS["nominal"])
    if year <= _PRED_END:
        if year >= _PRED_START:
            return _interp1([_PRED_START + i / 12.0 for i in range(len(_PRED_F107))], _PRED_F107, year)
        # before the prediction: cycle 25 (peak SSN ~160, start 2019.9)
        return max(ssn_to_f107(_hathaway(year, 2019.9, 160.0) + _hathaway(year, 2008.9, 115.0)), 66.0)
    k0 = max(0, int((year - _CYCLE26_START) / 11.0) - 2)
    r = sum(_hathaway(year, _CYCLE26_START + 11.0 * k, rmax) for k in range(k0, k0 + 4))
    return max(ssn_to_f107(r), 66.0)


@lru_cache(maxsize=4096)
def decay_lifetime_years(altitude_km: float, start_year: float, mass_kg: float, area_m2: float,
                         scenario: str = "nominal", cd: float = CD_DEFAULT, stop_km: float = 150.0,
                         max_years: float = 200.0) -> float:
    """Years from ``start_year`` until a circular orbit at ``altitude_km`` decays to ``stop_km``."""
    if mass_kg <= 0 or area_m2 <= 0:
        return max_years
    a = RE_M + altitude_km * 1e3
    t = start_year
    bc = cd * area_m2 / mass_kg
    while True:
        h = (a - RE_M) / 1e3
        if h < stop_km:
            break
        rho = density_kg_m3(h, f107_at(t, scenario))
        step_d = 1.0 if h > 300.0 else 0.1
        a -= rho * math.sqrt(MU * a) * bc * step_d * 86400.0
        t += step_d / 365.25
        if t - start_year > max_years:
            return max_years
    return t - start_year


def start_altitude_for(years: float, start_year: float, mass_kg: float, area_m2: float,
                       scenario: str = "weak", lo_km: float = 450.0, hi_km: float = 800.0) -> float:
    """Highest circular start altitude that still decays within ``years`` (bisection, 1 km)."""
    if decay_lifetime_years(lo_km, start_year, mass_kg, area_m2, scenario) > years:
        return lo_km
    for _ in range(12):
        mid = 0.5 * (lo_km + hi_km)
        if decay_lifetime_years(mid, start_year, mass_kg, area_m2, scenario, max_years=years * 2) <= years:
            lo_km = mid
        else:
            hi_km = mid
    return round(lo_km, 0)


def year_of(date: str | None, default: float = 2030.5) -> float:
    """'2030-06' / '2030-06-15' / '2030' -> decimal year (month midpoint)."""
    if not date:
        return default
    try:
        parts = str(date).strip().split("-")
        y = int(parts[0])
        if len(parts) == 1:
            return y + 0.5
        m = int(parts[1])
        d = int(parts[2][:2]) if len(parts) > 2 and parts[2][:2].isdigit() else 15
        return y + (m - 1) / 12.0 + (d - 0.5) / 365.25
    except (ValueError, IndexError):
        return default


@dataclass
class DragDevice:
    """A drag-augmentation device (drag sail) as the disposal analysis needs it."""
    name: str = "Drag sail"
    deployed_area_m2: float = 0.0
    effective_area_m2: float | None = None    # tumbling-averaged; None -> SAIL_EFFECTIVE_FRACTION x area
    mass_kg: float = 0.0
    trigger: list[str] = field(default_factory=lambda: ["ground command"])
    deployment_time_s: float | None = None
    mechanism_reliability: float = 0.97       # booms, membrane, release (assumed until tested)
    circuit_reliability: float = 0.90         # one release circuit incl. its trigger and power
    independent_circuits: int = 1
    independent_timer_days: float | None = None
    stowed_life_years: float | None = None
    source: str = ""

    @property
    def area_effective(self) -> float:
        if self.effective_area_m2:
            return float(self.effective_area_m2)
        return SAIL_EFFECTIVE_FRACTION * self.deployed_area_m2

    @property
    def deployment_reliability(self) -> float:
        n = max(int(self.independent_circuits or 1), 1)
        return self.mechanism_reliability * (1.0 - (1.0 - self.circuit_reliability) ** n)


def _flux_large_per_m2_yr(alt_km: float) -> float:
    """Screening flux of catalogued objects (>= 10 cm), per m^2 per year, by altitude.

    Spatial density (objects/km^3) after the public catalogue distribution (peak ~1e-7 near
    800 km), times a mean relative velocity of 10 km/s. Replace with DRAMA/ARES or ORDEM."""
    pts = [(300, 2e-9), (400, 6e-9), (500, 1.5e-8), (600, 3e-8), (700, 6e-8), (800, 1e-7), (900, 8e-8)]
    xs = [float(p[0]) for p in pts]
    ys = [math.log10(p[1]) for p in pts]
    dens = 10 ** _interp1(xs, ys, alt_km)
    return dens * 10.0 * 3.15576e7 * 1e-6     # /km^3 * km/s * s/yr -> /km^2/yr -> /m^2/yr


def _flux_small_ratio() -> float:
    """Objects 1-10 cm outnumber the catalogued ones by about 50:1 in LEO (screening value)."""
    return 50.0


@dataclass
class DisposalAssessment:
    altitude_km: float
    apogee_km: float
    mass_kg: float
    mass_basis: str
    start_year: float
    end_of_ops_year: float
    sail: dict | None
    area_stowed_m2: float
    area_deployed_effective_m2: float | None
    scenarios: list[dict]                    # one row per (case, scenario)
    lifetime_with_sail_y: dict[str, float]   # scenario -> years (worst-case start)
    lifetime_without_sail_y: dict[str, float]
    without_sail_range_y: list[float]
    highest_start_altitude_5y_km: dict[str, float]
    disposal_reliability: float | None
    collision_probability_large: float
    collision_probability_small: float
    collision_probability_disposal_large: float
    casualty_risk: float
    smallest_dimension_cm: float | None
    checks: list[dict]
    compliant: bool
    rules: dict
    model: str
    notes: list[str]

    def as_dict(self) -> dict:
        return asdict(self)


def _round(v: float, n: int = 2) -> float:
    return round(float(v), n)


def assess_disposal(*, altitude_km: float, eccentricity: float = 0.0, mass_kg: float,
                    mass_basis: str = "", launch_year: float = 2030.5, operations_years: float = 3.0,
                    device: DragDevice | None = None, has_propulsion: bool = False,
                    bus_area_m2: float | None = None, smallest_dimension_cm: float | None = None,
                    scenarios: tuple[str, ...] = ("strong", "nominal", "weak")) -> DisposalAssessment:
    """Disposal analysis against the ISED conditions, with and without the drag device.

    The worst case starts the decay at launch (an early unrecoverable failure: the independent
    timer deploys the sail, and the 5-year limit runs from the end of operational life, which
    includes an unrecoverable anomaly); the planned case starts it at launch + ``operations_years``.
    """
    a_m = (6371.0 + altitude_km)
    apogee = a_m * (1 + eccentricity) - 6371.0
    stowed = float(bus_area_m2 or BUS_AREA_BOUNDS_M2[1])
    eff = None
    if device is not None and device.deployed_area_m2 > 0:
        eff = device.area_effective + BUS_AREA_WITH_SAIL_M2
    eoo = launch_year + operations_years
    rows: list[dict] = []
    with_sail: dict[str, float] = {}
    without: dict[str, float] = {}
    for sc in scenarios:
        lt_no = decay_lifetime_years(altitude_km, launch_year, mass_kg, stowed, sc)
        without[sc] = _round(lt_no, 1)
        rows.append({"case": "no_device", "scenario": sc, "start_year": _round(launch_year, 2),
                      "area_m2": _round(stowed, 3), "lifetime_years": _round(lt_no, 1)})
        if eff:
            lt = decay_lifetime_years(altitude_km, launch_year, mass_kg, eff, sc)
            with_sail[sc] = _round(lt, 1)
            rows.append({"case": "device_at_launch", "scenario": sc, "start_year": _round(launch_year, 2),
                          "area_m2": _round(eff, 3), "lifetime_years": _round(lt, 1)})
            lt_eol = decay_lifetime_years(altitude_km, eoo, mass_kg, eff, sc)   # pre-disposal decay ignored (conservative)
            rows.append({"case": "device_at_end_of_operations", "scenario": sc, "start_year": _round(eoo, 2),
                          "area_m2": _round(eff, 3), "lifetime_years": _round(lt_eol, 1)})
    bounds = []
    # typical range: nominal and weak cycles, tumbling area between the lower bound and the stowed value
    for a in (BUS_AREA_BOUNDS_M2[0], stowed):
        for sc in ("nominal", "weak"):
            bounds.append(decay_lifetime_years(altitude_km, launch_year, mass_kg, a, sc))
    rng = [_round(min(bounds), 1), _round(max(bounds), 1)]
    hmax: dict[str, float] = {}
    if eff:
        for sc in ("nominal", "weak"):
            hmax[sc] = start_altitude_for(5.0, launch_year, mass_kg, eff, sc)

    # collision probability: operational life at the stowed area; disposal phase with the sail
    flux = _flux_large_per_m2_yr(altitude_km)
    pc_large = 1.0 - math.exp(-flux * stowed * operations_years)
    pc_small = 1.0 - math.exp(-flux * _flux_small_ratio() * stowed * operations_years)
    worst = max(with_sail.values()) if with_sail else max(without.values())
    disp_area = eff or stowed
    pc_disp = 1.0 - math.exp(-_flux_large_per_m2_yr(altitude_km * 0.85) * disp_area * worst)
    casualty = 0.0 if mass_kg < 10 else 1e-5   # small all-aluminium CubeSats demise completely (DAS to confirm)

    rel = device.deployment_reliability if (device is not None and eff) else None
    lim = ISED_RULES
    worst_with = max(with_sail.values()) if with_sail else None
    checks = [
        {"id": "ISED-DM-01", "rule": "Disposal within 5 years of the end of operational life",
          "value": worst_with if worst_with is not None else max(without.values()), "limit": lim["disposal_max_years"],
          "unit": "y", "pass": (worst_with if worst_with is not None else max(without.values())) <= lim["disposal_max_years"],
          "basis": "worst solar scenario, decay from launch (early-failure case)"},
        {"id": "ISED-DM-02", "rule": "Probability of successful disposal >= 90 %",
          "value": _round(rel, 3) if rel is not None else (1.0 if max(without.values()) <= 5 else 0.0),
          "limit": lim["disposal_probability_min"], "unit": "",
          "pass": (rel if rel is not None else (1.0 if max(without.values()) <= 5 else 0.0)) >= lim["disposal_probability_min"],
          "basis": "mechanism x (1 - (1 - circuit)^n) for n independent release circuits" if rel is not None
          else "natural decay"},
        {"id": "ISED-DM-03", "rule": "Collision probability with objects >= 10 cm < 0.001 (operational life)",
          "value": float(f"{pc_large:.2e}"), "limit": lim["collision_probability_max_large"], "unit": "",
          "pass": pc_large < lim["collision_probability_max_large"], "basis": "screening flux; DRAMA/ARES or DAS to confirm"},
        {"id": "ISED-DM-04", "rule": "Collision probability with objects < 10 cm < 0.01 (operational life)",
          "value": float(f"{pc_small:.2e}"), "limit": lim["collision_probability_max_small"], "unit": "",
          "pass": pc_small < lim["collision_probability_max_small"], "basis": "screening flux; DRAMA/MASTER to confirm"},
        {"id": "ISED-DM-05", "rule": "Active propulsion if the apogee is above 600 km",
          "value": _round(apogee, 1), "limit": lim["apogee_without_propulsion_max_km"], "unit": "km",
          "pass": has_propulsion or apogee <= lim["apogee_without_propulsion_max_km"], "basis": "orbit definition"},
        {"id": "ISED-DM-06", "rule": "Trackable: smallest dimension >= 10 cm (deployables excluded)",
          "value": smallest_dimension_cm, "limit": lim["trackable_min_dimension_cm"], "unit": "cm",
          "pass": None if smallest_dimension_cm is None else smallest_dimension_cm >= lim["trackable_min_dimension_cm"],
          "basis": "form factor"},
    ]
    notes = [
        "Screening model (NRLMSIS 2.1 table, SWPC cycle-25 prediction, Hathaway cycle 26); quote a "
        "DRAMA/OSCAR or DAS result in the licence application.",
        f"Mass for decay: {mass_kg:.2f} kg ({mass_basis or 'as given'}). A higher mass gives a longer lifetime.",
    ]
    if device is not None and device.stowed_life_years is not None and device.stowed_life_years < operations_years + 0.5:
        notes.append(f"The device's rated stowed life ({device.stowed_life_years} y) is shorter than launch + "
                     f"operations ({operations_years} y): confirm with the supplier.")
    return DisposalAssessment(
        altitude_km=altitude_km, apogee_km=_round(apogee, 1), mass_kg=_round(mass_kg, 3), mass_basis=mass_basis,
        start_year=_round(launch_year, 2), end_of_ops_year=_round(eoo, 2),
        sail=(asdict(device) | {"effective_area_m2_used": _round(device.area_effective, 3),
                               "deployment_reliability": _round(device.deployment_reliability, 4)})
        if (device is not None and eff) else None,
        area_stowed_m2=_round(stowed, 3), area_deployed_effective_m2=_round(eff, 3) if eff else None,
        scenarios=rows, lifetime_with_sail_y=with_sail, lifetime_without_sail_y=without,
        without_sail_range_y=rng, highest_start_altitude_5y_km=hmax,
        disposal_reliability=_round(rel, 4) if rel is not None else None,
        collision_probability_large=float(f"{pc_large:.3e}"), collision_probability_small=float(f"{pc_small:.3e}"),
        collision_probability_disposal_large=float(f"{pc_disp:.3e}"), casualty_risk=casualty,
        smallest_dimension_cm=smallest_dimension_cm, checks=checks,
        compliant=all(c["pass"] is not False for c in checks), rules=dict(ISED_RULES),
        model="NRLMSIS 2.1 global mean table; SWPC cycle-25 prediction; Hathaway cycle 26 (SSN 160/115/80); "
              "Cd 2.2; sail effective area 0.38 x deployed (CanX-7 calibration) + 0.05 m2 bus",
        notes=notes,
    )
