"""Shared MagicMock engine doubles for ServiceDispatcher tests (R4 G3).

A bare ``MagicMock`` engine silently breaks two pieces of the dispatcher API:

* ``engine.param_visibility(pid)`` — S20.3 refuses any parameter whose
  visibility is not ``"real"`` (ground-derived / instructor-only values the
  spacecraft could not report). On a MagicMock the call returns a mock, which
  is never ``"real"``, so every S20.3 read is refused.
* ``engine.tm_builder.pack_tm_segmented(...)`` — the "report all" services
  (TM(11,18), TM(12,13), TM(19,128)) segment on the CCSDS grouping flags. On
  a mock builder the call returns a MagicMock of length 0, so every report is
  silently empty and negative tests pass without testing anything.

``wire_mock_engine`` fixes both on an existing double: visibility comes from
the real parameter catalogue (so tests see the same refusals the engine
makes), and ``pack_tm_segmented`` is the REAL method bound to the mock
builder, so it calls the mock's ``_pack_tm`` once per segment.
"""

from __future__ import annotations

import functools
from pathlib import Path
from unittest.mock import MagicMock

from smo_common.telemetry.tm_builder import TMBuilder

CONFIG_DIR = Path(__file__).resolve().parent.parent / "configs" / "eosat1"


@functools.lru_cache(maxsize=1)
def catalogue_visibility() -> dict[int, str]:
    """param_id -> visibility class from configs/eosat1/telemetry/parameters.yaml."""
    import yaml

    path = CONFIG_DIR / "telemetry" / "parameters.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rows = data.get("parameters", data) if isinstance(data, dict) else data
    out: dict[int, str] = {}
    for row in rows or []:
        if not isinstance(row, dict) or "id" not in row:
            continue
        pid = row["id"]
        pid = int(pid, 0) if isinstance(pid, str) else int(pid)
        out[pid] = str(row.get("visibility", "real"))
    return out


def real_param_visibility(pid: int) -> str:
    """Visibility as the engine reports it; unknown ids default to ``real``."""
    return catalogue_visibility().get(int(pid), "real")


def wire_mock_engine(engine, *, visibility=None):
    """Teach a MagicMock engine the current dispatcher API. Returns ``engine``.

    ``visibility``: optional ``pid -> str`` override; default is the shipped
    catalogue (:func:`real_param_visibility`).
    """
    engine.param_visibility = visibility or real_param_visibility
    builder = getattr(engine, "tm_builder", None)
    if builder is None or not isinstance(builder, MagicMock):
        return engine
    # The real pack_tm_segmented calls self._pack_tm per segment; make sure
    # the double's _pack_tm returns bytes rather than an auto-created mock.
    if isinstance(builder._pack_tm.return_value, MagicMock):
        builder._pack_tm = MagicMock(return_value=b"\x00" * 20)
    builder.pack_tm_segmented = TMBuilder.pack_tm_segmented.__get__(
        _KwargPackProxy(builder))
    return engine


class _KwargPackProxy:
    """``self`` for the real ``pack_tm_segmented`` bound to a mock builder.

    The real method calls ``self._pack_tm(service, subtype, body, ...)``
    positionally; the dispatcher's single-packet paths call it with keywords.
    Forwarding as keywords keeps ``builder._pack_tm.call_args[1]['data']``
    uniform for every test that inspects the last packed packet.
    """

    def __init__(self, builder):
        self._builder = builder

    def _pack_tm(self, service, subtype, data, **kw):
        return self._builder._pack_tm(service=service, subtype=subtype,
                                      data=data, **kw)


def make_mock_engine(*, cuc: int = 1000, prop: bool = False):
    """A minimal dispatcher-ready MagicMock engine, already wired."""
    engine = MagicMock()
    engine.params = {}
    engine._hk_structures = {}
    engine._hk_enabled = {}
    engine._hk_intervals = {}
    engine._get_cuc_time = MagicMock(return_value=cuc)
    engine.tm_builder = MagicMock()
    engine.tm_builder._pack_tm = MagicMock(return_value=b"\x00" * 20)
    engine.tm_builder.build_hk_packet = MagicMock(return_value=b"\x00" * 20)
    engine.tm_builder.build_connection_test_report = MagicMock(return_value=b"\x00" * 20)
    engine.tm_builder.build_param_value_report = MagicMock(return_value=b"\x00" * 20)
    engine.tm_builder.build_time_report = MagicMock(return_value=b"\x00" * 20)
    engine.subsystems = {
        "aocs": MagicMock(), "eps": MagicMock(), "payload": MagicMock(),
        "tcs": MagicMock(), "obdh": MagicMock(), "ttc": MagicMock(),
    }
    if prop:
        engine.subsystems["prop"] = MagicMock()
    engine._tc_scheduler = MagicMock()
    engine._tm_storage = MagicMock()
    engine.event_types_enabled = set(range(256))
    return wire_mock_engine(engine)
