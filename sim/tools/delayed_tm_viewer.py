#!/usr/bin/env python3
"""delayed_tm_viewer.py — Live HTML viewer for archived delayed TM dumps.

A small aiohttp server you can start at the beginning of a simulation and
keep running. After every pass that performs an S15 dump, the simulator
writes a ``workspace/dumps/dump_sid<NN>_<UTC>.bin`` file. Open this tool
in your browser and click "Refresh" / "Load latest" / "Load all" / use
the time-window picker to decode any subset of those files into a
human-readable view (packet counts, S5 events, per-SID HK time series
with sparklines, anomalies).

It is fully offline — no CDN. The decoder is shared with
``tools/tm_report.py``; the store layout and location rules are shared with
``smo_common.dump_store``.

The tool runs in one of two modes:

**Local mode (default)** reads the dump directory off the local filesystem.
This is the single-machine workflow and is unchanged.

**API mode** (``--api http://<server>:9090``) reads the store over HTTP from
whichever service owns it — normally the MCS, optionally the simulator. Use
this when the archive lives on a server and this tool runs somewhere else,
so no shared/NFS mount is needed (defect #90). Note that students do not
need this tool at all in a networked classroom: the MCS serves its own
listing/download/summary page at ``http://<server>:9090/dumps``.

Usage::

    python tools/delayed_tm_viewer.py             # default port 8092
    python tools/delayed_tm_viewer.py --port 9100 --dumps workspace/dumps
    python tools/delayed_tm_viewer.py --api http://server:9090
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "packages" / "smo-common" / "src"))
sys.path.insert(0, str(REPO / "tools"))

from aiohttp import web

from smo_common.dump_store import (  # type: ignore
    DUMP_NAME_RE,
    list_dumps as _store_list_dumps,
    parse_dump_filename,
    resolve_dump_dir,
)

from tm_report import (  # type: ignore
    PassAnalysis,
    load_catalogs,
    read_dump,
)

logger = logging.getLogger("delayed_tm_viewer")


# ---------- ground limits on played-back series (POSITION_NEEDS G11) ----------
#
# The ground limit table lives in configs/<mission>/mcs/limits.yaml and its
# parser lives in smo_common (`smo_common.config.loader.load_limits`,
# `LimitDef` in config.schemas) — the MCS uses the same one, but this tool
# may not import smo-mcs, and does not need to.

def load_limits_by_pid(config_dir: Path) -> dict[int, Any]:
    """{param_id: LimitDef} from mcs/limits.yaml; {} when absent/broken."""
    try:
        from smo_common.config.loader import load_limits
        return {l.param_id: l for l in load_limits(config_dir)}
    except Exception as e:  # noqa: BLE001 — limits are an overlay, not a dep
        logger.warning("Could not load mcs/limits.yaml from %s: %s",
                       config_dir, e)
        return {}


def _classify(v: float, lim) -> str:
    """'red' | 'yellow' | 'ok' for one engineering value against one band."""
    if lim.red_low is not None and v < lim.red_low:
        return "red"
    if lim.red_high is not None and v > lim.red_high:
        return "red"
    if lim.yellow_low is not None and v < lim.yellow_low:
        return "yellow"
    if lim.yellow_high is not None and v > lim.yellow_high:
        return "yellow"
    return "ok"


def evaluate_limits(pts: list[tuple[float, float]], lim) -> dict[str, Any]:
    """Time-in-band accounting for one decoded series.

    Each sample owns the interval up to the next sample; the last sample
    (and a single-sample series) gets the mean observed spacing, falling
    back to the limit's ``check_interval_s``. 'yellow' means outside the
    yellow band but inside red; 'red' means outside the red band — the two
    times never double-count.
    """
    times = [t for t, _ in pts]
    dts = [max(0.0, times[i + 1] - times[i]) for i in range(len(pts) - 1)]
    positive = [d for d in dts if d > 0]
    default_dt = (sum(positive) / len(positive) if positive
                  else float(getattr(lim, "check_interval_s", 4.0) or 4.0))
    t_yellow = t_red = 0.0
    n_yellow = n_red = 0
    worst = "ok"
    for i, (_, v) in enumerate(pts):
        dt = dts[i] if i < len(dts) and dts[i] > 0 else default_dt
        c = _classify(v, lim)
        if c == "red":
            t_red += dt
            n_red += 1
            worst = "red"
        elif c == "yellow":
            t_yellow += dt
            n_yellow += 1
            if worst != "red":
                worst = "yellow"
    return {
        "time_in_yellow_s": round(t_yellow, 3),
        "time_in_red_s": round(t_red, 3),
        "samples_yellow": n_yellow,
        "samples_red": n_red,
        "state": worst,
        "band": {
            "yellow_low": lim.yellow_low, "yellow_high": lim.yellow_high,
            "red_low": lim.red_low, "red_high": lim.red_high,
        },
    }


# ---------- core analysis ----------

def clean_event_text(desc: str) -> str:
    """The readable auxiliary text of an S5 event description.

    tm_report decodes the whole event body after the event ID as text, so
    the severity byte, the 4-byte whole-second time and the length byte
    arrive as control/replacement characters in front of the real text
    ("\\x03\\x32y..\\x0fSAFE MODE ENTRY"). The aux text is what follows the
    last such character. Already-clean text is returned unchanged.
    """
    if not desc:
        return ""
    cut = -1
    for i, ch in enumerate(desc):
        if ord(ch) < 0x20 or 0x7F <= ord(ch) < 0xA0 or ch == "\ufffd":
            cut = i
    return desc[cut + 1:].strip()


def list_dumps(dump_dir: Path) -> list[dict[str, Any]]:
    """Return metadata about every dump file in ``dump_dir``.

    Thin wrapper over ``smo_common.dump_store.list_dumps`` so this tool and
    the MCS/simulator dump APIs describe the store identically.
    """
    return _store_list_dumps(dump_dir)


def _parse_ts(t: str | None) -> datetime | None:
    """Parse 'YYYY-MM-DDTHH:MM:SSZ' or '...+00:00'; None if unparseable."""
    if not t:
        return None
    try:
        return datetime.fromisoformat(t.replace("Z", "+00:00"))
    except ValueError:
        return None


def select_meta(available: list[dict[str, Any]], *, files: list[str] | None = None,
                since: str | None = None, until: str | None = None,
                all_: bool = False, latest: bool = False) -> list[dict[str, Any]]:
    """Filter a listing (local or fetched from the API) down to a selection.

    Works purely on metadata dicts keyed by ``filename``/``timestamp``, so the
    same selection logic serves the local filesystem and a remote store.
    """
    if not available:
        return []

    if latest:
        return [available[-1]]

    if files:
        wanted = {f.strip() for f in files if f.strip()}
        return [d for d in available if d["filename"] in wanted]

    if all_ and not (since or until):
        return list(available)

    s, u = _parse_ts(since), _parse_ts(until)
    out: list[dict[str, Any]] = []
    for d in available:
        ts = _parse_ts(d.get("timestamp")) or _parse_ts(d.get("mtime"))
        if ts is None:
            continue
        if s and ts < s:
            continue
        if u and ts > u:
            continue
        out.append(d)
    return out


def select_dumps(dump_dir: Path, *, files: list[str] | None = None,
                 since: str | None = None, until: str | None = None,
                 all_: bool = False, latest: bool = False) -> list[Path]:
    """Resolve a request into a concrete list of local dump file paths."""
    chosen = select_meta(list_dumps(dump_dir), files=files, since=since,
                         until=until, all_=all_, latest=latest)
    return [Path(d["path"]) for d in chosen]


# ---------- remote (API) store client ----------

class RemoteDumpStore:
    """Read a dump store over the HTTP API instead of the local filesystem.

    Downloaded archives are cached in a temporary directory so the existing
    local decode path (:func:`analyse_dumps`) is reused unchanged — the only
    difference between local and API mode is where the bytes come from.
    """

    def __init__(self, api_base: str, cache_dir: Path | None = None):
        self.api_base = api_base.rstrip("/")
        if not self.api_base.endswith("/api/dumps"):
            self.api_base += "/api/dumps"
        self._cache = Path(cache_dir) if cache_dir else \
            Path(tempfile.mkdtemp(prefix="smo-dump-cache-"))
        self._cache.mkdir(parents=True, exist_ok=True)

    @property
    def cache_dir(self) -> Path:
        return self._cache

    async def list(self) -> list[dict[str, Any]]:
        import aiohttp
        async with aiohttp.ClientSession() as s:
            async with s.get(self.api_base) as r:
                r.raise_for_status()
                body = await r.json()
        return body.get("dumps", [])

    async def fetch(self, filename: str) -> Path:
        """Download one dump into the cache (skipping an unchanged copy)."""
        import aiohttp
        # The server validates the name too; refuse locally as well so a bad
        # name never becomes a filesystem write outside the cache.
        if Path(filename).name != filename or not DUMP_NAME_RE.match(filename):
            raise ValueError(f"not a dump archive filename: {filename!r}")
        target = self._cache / filename
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{self.api_base}/file", params={"name": filename}) as r:
                r.raise_for_status()
                data = await r.read()
        target.write_bytes(data)
        return target

    async def select(self, **kwargs) -> list[Path]:
        chosen = select_meta(await self.list(), **kwargs)
        out: list[Path] = []
        for d in chosen:
            try:
                out.append(await self.fetch(d["filename"]))
            except Exception as e:  # noqa: BLE001 — one bad file must not kill the view
                logger.warning("Could not fetch %s from %s: %s",
                               d.get("filename"), self.api_base, e)
        return out


#: A hole is called a gap when it exceeds this multiple of the SID's
#: configured cadence. Same convention as
#: smo_common.reporting.analysis.completeness, so the viewer and the
#: generated reports cannot disagree about what a gap is.
GAP_THRESHOLD_MULTIPLE = 3.0


def find_sid_gaps(times: list[float], cadence: float,
                  threshold_multiple: float = GAP_THRESHOLD_MULTIPLE
                  ) -> list[dict[str, float]]:
    """Holes in a SID's arrival times, in on-board CUC seconds.

    A SID that the ground disabled (or that a boot switched off) simply stops
    producing packets: the dump then contains two runs of samples with nothing
    between them. Plotted naively that reads as one continuous line, which is
    a lie about what the spacecraft measured. Every consumer of a decoded
    series needs the gap list so it can BREAK the line instead.
    """
    if cadence <= 0 or len(times) < 2:
        return []
    threshold = threshold_multiple * cadence
    gaps = []
    for a, b in zip(times, times[1:]):
        if (b - a) > threshold:
            gaps.append({"start_cuc": a, "end_cuc": b,
                         "duration_s": round(b - a, 3),
                         "missing": max(int(round((b - a) / cadence)) - 1, 1)})
    return gaps


def analyse_dumps(paths: Iterable[Path], params_by_id: dict, hk_plist: dict,
                  limits_by_pid: dict[int, Any] | None = None,
                  hk_structs: dict[int, dict] | None = None) -> dict[str, Any]:
    """Decode one or more dump files into a JSON-friendly summary.

    ``limits_by_pid`` (G11): when given, every decoded series is run through
    the ground limits (mcs/limits.yaml) and each parameter carries
    time-in-yellow / time-in-red plus its band for plot shading; the result
    carries a per-dump ``limits`` summary line.

    ``hk_structs`` supplies each SID's configured cadence so the decoded
    series can be checked for GAPS — stretches where the SID produced nothing
    because it was disabled (by TC(3,6), or by a boot resetting the enable
    set). Each SID and each parameter carries its own ``gaps`` list, and the
    plot breaks the line across them rather than drawing straight through.
    """
    an = PassAnalysis()
    files_used: list[dict[str, Any]] = []
    for path in paths:
        # Per-file on-board time span (for the dump timeline): ingest with the
        # running span cleared, read it, then fold it back into the total.
        prev = (an.first_time, an.last_time)
        an.first_time = an.last_time = None
        try:
            count = 0
            for raw in read_dump(path):
                an.ingest_packet(raw, params_by_id, hk_plist)
                count += 1
            files_used.append({"filename": path.name, "packets": count,
                               "size_bytes": path.stat().st_size,
                               "first_cuc": an.first_time, "last_cuc": an.last_time})
        except Exception as e:
            files_used.append({"filename": path.name, "error": str(e)})
        finally:
            spans = [t for t in (prev[0], an.first_time) if t is not None]
            an.first_time = min(spans) if spans else None
            spans = [t for t in (prev[1], an.last_time) if t is not None]
            an.last_time = max(spans) if spans else None

    pkt_counts = [{"service": s, "subtype": st, "count": n}
                  for (s, st), n in sorted(an.pkt_counts.items())]
    events = [
        {"cuc": e["cuc"], "subtype": e["subtype"],
         "event_id": e["event_id"], "severity": e["severity"],
         "description": clean_event_text(e["description"])}
        for e in an.events
    ]

    hk: list[dict[str, Any]] = []
    anomalies: list[dict[str, Any]] = []
    limits_by_pid = limits_by_pid or {}
    lim_yellow: list[str] = []      # parameters whose worst state is yellow
    lim_red: list[str] = []         # parameters whose worst state is red
    lim_checked = 0
    hk_structs = hk_structs or {}
    gap_lines: list[str] = []
    for sid, samples in sorted(an.hk_samples.items()):
        if not samples:
            continue
        # cuc is full-precision on-board seconds (float).
        per_pid: dict[int, list[tuple[float, float]]] = {}
        for cuc, vals in samples:
            for pid, v in vals.items():
                per_pid.setdefault(pid, []).append((cuc, v))
        # Gap sweep for this SID, from its configured cadence. Done once per
        # SID (the arrival times are shared by every parameter in the packet)
        # and attached to every parameter so a plot can break its line.
        struct_def = hk_structs.get(sid) or {}
        try:
            cadence = float(struct_def.get("interval_s") or 0.0)
        except (TypeError, ValueError):
            cadence = 0.0
        sid_times = sorted(c for c, _ in samples)
        sid_gaps = find_sid_gaps(sid_times, cadence)
        if sid_gaps:
            total = sum(g["duration_s"] for g in sid_gaps)
            gap_lines.append(
                f"SID {sid}: {len(sid_gaps)} gap(s), {total:.0f}s missing "
                f"(cadence {cadence:g}s)")
        params_out: list[dict[str, Any]] = []
        for pid in sorted(per_pid):
            pts = per_pid[pid]
            vals = [v for _, v in pts]
            mn, mx = min(vals), max(vals)
            avg = sum(vals) / len(vals)
            meta = params_by_id.get(pid, {})
            deltas = [abs(vals[i] - vals[i-1]) for i in range(1, len(vals))]
            flag = False
            if deltas:
                mean_d = sum(deltas) / len(deltas) or 1e-9
                peak = max(deltas)
                if peak > 5 * mean_d and peak > 0.5:
                    flag = True
                    anomalies.append({"sid": sid, "pid": pid,
                                      "name": meta.get("name", f"0x{pid:04X}"),
                                      "peak_delta": peak, "mean_delta": mean_d})
            entry: dict[str, Any] = {
                "pid": pid,
                "name": meta.get("name", f"0x{pid:04X}"),
                "units": meta.get("units", ""),
                "min": mn, "max": mx, "mean": avg,
                "n": len(vals),
                "flag": flag,
                # Compact array of [cuc, value] for client-side sparkline
                "series": [[c, v] for c, v in pts],
                # G11: ground-limit evaluation (None = no band configured)
                "limit": None,
                # Holes in this SID's arrival times. NON-EMPTY means the
                # series is discontinuous and must NOT be drawn as one line.
                "gaps": sid_gaps,
            }
            lim = limits_by_pid.get(pid)
            if lim is not None:
                verdict = evaluate_limits(pts, lim)
                entry["limit"] = verdict
                lim_checked += 1
                if verdict["state"] == "red":
                    lim_red.append(entry["name"])
                elif verdict["state"] == "yellow":
                    lim_yellow.append(entry["name"])
            params_out.append(entry)
        hk.append({
            "sid": sid,
            "name": str(struct_def.get("name") or ""),
            "packet_count": an.hk_counts[sid],
            "sample_count": len(samples),
            "cadence_s": cadence,
            "gaps": sid_gaps,
            "params": params_out,
        })

    # G11: one honest per-dump summary line for the ground-limit sweep.
    if not limits_by_pid:
        lim_summary = "no ground limits loaded"
    elif lim_checked == 0:
        lim_summary = "no decoded parameter carries a ground limit"
    elif not lim_yellow and not lim_red:
        lim_summary = (f"all {lim_checked} limit-checked parameters "
                       f"within limits")
    else:
        lim_summary = (f"{len(lim_yellow)} parameter(s) exceeded yellow, "
                       f"{len(lim_red)} red")

    return {
        "files": files_used,
        "limits": {
            "checked": lim_checked,
            "yellow": lim_yellow,
            "red": lim_red,
            "summary": lim_summary,
        },
        "first_cuc": an.first_time,
        "last_cuc": an.last_time,
        "total_packets": sum(an.pkt_counts.values()),
        "packet_counts": pkt_counts,
        "events": events,
        "hk": hk,
        "anomalies": anomalies,
        # S12 on-board monitoring — the contents Franz could not see. Decoded
        # by `PassAnalysis` (tm_report), which now has the `svc == 12` branch
        # it never had. S12 packets are routed to the Alarm store (store 4),
        # so an alarm dump is mostly this.
        "s12_transitions": an.s12_transitions,
        "s12_definitions": an.s12_definitions,
        # Honest gap accounting (see find_sid_gaps). `summary` is what the
        # page prints when nothing is plotted, so a dump taken across a
        # SID-disable window says so in words as well as in the charts.
        "gaps": {
            "threshold_multiple": GAP_THRESHOLD_MULTIPLE,
            "by_sid": {str(h["sid"]): h["gaps"] for h in hk if h.get("gaps")},
            "summary": ("; ".join(gap_lines) if gap_lines
                        else ("no HK gaps detected" if hk_structs
                              else "gap detection unavailable "
                                   "(no HK cadences loaded)")),
        },
    }


# ---------- HTTP handlers ----------

def make_app(dump_dir: Path | None, api_base: str | None = None) -> web.Application:
    """Build the viewer app.

    Exactly one source is used: the local ``dump_dir`` (default), or the
    remote store at ``api_base`` when given.
    """
    params_by_id, hk_by_sid, hk_plist = load_catalogs()
    # Shared HTTP policy (gzip, cache headers) and the shared design system /
    # language runtime at /static/shared/ (R3 audit A8, §8).
    from smo_common.web.http import (relative_display_path,
                                     setup_tool_app, tool_html_response)
    import tool_frame          # shared page frame: TOOL_HEAD + title bar
    app = setup_tool_app(web.Application())
    page_html = (INDEX_HTML
                 .replace("<!--FRAME_HEAD-->", tool_frame.head())
                 .replace("<!--FRAME_BAR-->", tool_frame.bar('<span data-i18n>Delayed TM</span>',
                                                             logbook="delayed_tm"))
                 .replace("<!--FRAME_SCRIPT-->", tool_frame.SCRIPT))
    # Never print the absolute server path on a web page (R3 audit A9):
    # show the store relative to the suite root instead.
    store_label = relative_display_path(dump_dir, REPO) if dump_dir else ""
    remote = RemoteDumpStore(api_base) if api_base else None
    app["dump_dir"] = dump_dir
    app["remote"] = remote
    app["params_by_id"] = params_by_id
    app["hk_plist"] = hk_plist
    # Per-SID cadence, so a decoded series can be checked for gaps.
    app["hk_structs"] = hk_by_sid
    # G11: ground limits applied to every decoded series.
    app["limits_by_pid"] = load_limits_by_pid(REPO / "configs" / "eosat1")

    async def index(_req: web.Request) -> web.Response:
        return tool_html_response(page_html, app)

    async def api_dumps(_req: web.Request) -> web.Response:
        if remote is not None:
            try:
                dumps = await remote.list()
            except Exception as e:  # noqa: BLE001 — surface, don't 500
                return web.json_response(
                    {"dump_dir": remote.api_base, "dumps": [],
                     "error": f"cannot reach dump API: {e}"})
            return web.json_response({"dump_dir": remote.api_base, "dumps": dumps})
        return web.json_response({"dump_dir": store_label,
                                  "dumps": list_dumps(dump_dir)})

    async def api_decode(req: web.Request) -> web.Response:
        q = req.query
        files = q.get("files", "")
        file_list = files.split(",") if files else None
        selection = dict(
            files=file_list,
            since=q.get("since"),
            until=q.get("until"),
            all_=q.get("all") in ("1", "true", "yes"),
            latest=q.get("latest") in ("1", "true", "yes"),
        )
        if remote is not None:
            try:
                paths = await remote.select(**selection)
            except Exception as e:  # noqa: BLE001
                return web.json_response(
                    {"error": f"cannot reach dump API: {e}",
                     "files": [], "events": [], "hk": [],
                     "packet_counts": [], "anomalies": [],
                     "total_packets": 0, "first_cuc": None, "last_cuc": None})
        else:
            paths = select_dumps(dump_dir, **selection)
        if not paths:
            return web.json_response({"error": "no dump files matched the request",
                                      "files": [], "events": [], "hk": [],
                                      "packet_counts": [], "anomalies": [],
                                      "total_packets": 0,
                                      "first_cuc": None, "last_cuc": None})
        result = analyse_dumps(paths, app["params_by_id"], app["hk_plist"],
                               limits_by_pid=app["limits_by_pid"],
                               hk_structs=app.get("hk_structs"))
        return web.json_response(result)

    # Participant logbook (LOGBOOK_SPEC.md): private, /api/logbook on this
    # origin; "Log this" on step changes, events and check transitions.
    from smo_common.logbook import register_logbook_routes
    register_logbook_routes(app, tool="delayed_tm",
                            worksheets_dir=REPO / "configs" / "eosat1" / "worksheets")

    app.router.add_get("/", index)
    app.router.add_get("/api/dumps", api_dumps)
    app.router.add_get("/api/decode", api_decode)

    # Report generator (Phase F): same library and routes the MCS mounts, so
    # the standalone viewer offers /reports and /api/reports/* in local mode.
    if dump_dir is not None:
        try:
            from smo_common.reporting import register_report_routes
            register_report_routes(app, dump_dir,
                                   REPO / "configs" / "eosat1",
                                   owner="delayed_tm_viewer")
        except Exception as e:  # noqa: BLE001 — reports are optional here
            logger.warning("Report API not mounted: %s", e)

    # Serve Chart.js from the repo's vendor tree rather than a CDN, so the
    # "fully offline" promise in the module docstring is actually true. The
    # MCS static tree is preferred; the top-level vendor/ is the fallback.
    for candidate in (REPO / "packages" / "smo-mcs" / "src" / "smo_mcs" / "static" / "vendor",
                      REPO / "vendor"):
        if (candidate / "js" / "chart.umd.min.js").is_file():
            app.router.add_static("/vendor", str(candidate))
            break
    else:  # pragma: no cover - only on a broken checkout
        logger.warning("Chart.js not found in the vendor tree; plots will not render")
    return app


# ---------- HTML page (served inline so the tool is single-file) ----------

INDEX_HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title data-i18n>Delayed TM</title>
<!--FRAME_HEAD-->
<!-- Vendored locally (see the /vendor static route) so the tool really is
     offline, as the module docstring promises. -->
<script src="/vendor/js/chart.umd.min.js"></script>
<style>
/* Delayed TM. Picture first: what the loaded dumps contain, laid out on the
   on-board time axis (coverage per SID, gaps, events, limit excursions);
   the packet-level tables are one tab deeper. Tokens only. */
.dt-wrap{ display:grid; grid-template-columns:320px minmax(0,1fr); gap:var(--sp-4); align-items:start; }
.dt-rail{ position:sticky; top:64px; max-height:calc(100vh - 80px); display:flex; flex-direction:column; }
.dt-rail .ds-panel-b{ padding:var(--sp-3) var(--sp-4); }
.dt-acts{ display:grid; grid-template-columns:1fr 1fr; gap:var(--sp-2); }
.dt-acts .wide{ grid-column:1 / -1; }
.dt-files{ overflow:auto; flex:1 1 auto; min-height:80px; border-top:1px solid var(--line); }
.dt-file{ display:grid; grid-template-columns:auto minmax(0,1fr) auto; gap:2px var(--sp-2); align-items:center;
  padding:6px var(--sp-4); border-bottom:1px solid var(--line); cursor:pointer; }
.dt-file:hover{ background:var(--s2); }
.dt-file.is-active{ background:var(--accent-wash); box-shadow:inset 2px 0 0 var(--accent); }
.dt-file .when{ font-family:var(--mono); font-size:var(--fs-body); color:var(--tx); }
.dt-file .fn{ grid-column:2 / 4; font-family:var(--mono); font-size:var(--fs-label); color:var(--tx3);
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.dt-file .sz{ font-family:var(--mono); font-size:var(--fs-label); color:var(--tx3); }
.dt-file.loaded .when::after{ content:""; display:inline-block; width:6px; height:6px; margin-left:6px;
  background:var(--tx2); border-radius:1px; vertical-align:2px; }
.dt-range{ display:grid; grid-template-columns:1fr 1fr; gap:var(--sp-2); }
.dt-range .ds-input{ font-size:var(--fs-label); }
#limitBanner .ds-banner{ flex-wrap:wrap; }
#limitBanner .ds-banner .r{ min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:100%; }
.dt-main{ display:flex; flex-direction:column; gap:var(--sp-4); min-width:0; }
.dt-facts{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); }
.dt-facts>div{ padding:var(--sp-2) var(--sp-4) var(--sp-3); border-right:1px solid var(--line);
  display:flex; flex-direction:column; gap:2px; min-width:0; }
.dt-facts>div:last-child{ border-right:0; }
.dt-facts .k{ font-size:var(--fs-label); color:var(--tx3); }
.dt-facts .v{ font-family:var(--mono); font-size:var(--fs-value); font-weight:500; color:var(--val);
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.dt-facts .v small{ font-size:var(--fs-label); color:var(--tx3); font-weight:400; }
.dt-tl{ padding:var(--sp-2) var(--sp-4) var(--sp-3); }
.dt-tl .cov{ fill:var(--fill); }
.dt-tl .gap{ fill:none; stroke:var(--warn); stroke-width:1; stroke-dasharray:3 2; }
.dt-tl .gapt{ fill:var(--warn) !important; }
.dt-tl .file{ fill:var(--s3); stroke:var(--line-2); }
.dt-tl .lane{ stroke:var(--line); }
.dt-tl .lab{ fill:var(--tx2) !important; font-family:var(--sans) !important; font-size:13px !important; }
.dt-tl .labs{ fill:var(--tx3) !important; }
.dt-tl .ev1{ fill:var(--tx2); }
.dt-tl .ev3{ fill:var(--bg); stroke:var(--warn); stroke-width:1.5; }
.dt-tl .ev4{ fill:var(--alarm); }
.dt-tl .exy{ fill:var(--warn); }
.dt-tl .exr{ fill:var(--alarm); }
.dt-tl .hl{ stroke:var(--accent); stroke-width:1; }
.dt-legend{ display:flex; flex-wrap:wrap; gap:var(--sp-1) var(--sp-4); padding:0 var(--sp-4) var(--sp-3);
  font-size:var(--fs-label); color:var(--tx3); }
.dt-legend span{ display:inline-flex; align-items:center; gap:6px; }
.dt-legend svg{ width:16px; height:10px; overflow:visible; }
.dt-tabpanel{ min-height:120px; }
.dt-tabpanel>.ds-table, .dt-tabpanel .ds-table{ font-size:var(--fs-body); }
.dt-sid>summary{ min-height:40px; }
.dt-sid>summary .ds-chip{ margin-left:var(--sp-2); }
.dt-sid>.bd{ padding:0 0 var(--sp-3); }
.dt-par td{ vertical-align:middle; }
.dt-par td.id{ font-family:var(--mono); font-size:var(--fs-label); color:var(--tx3); white-space:nowrap; }
.dt-par td.nm{ min-width:12ch; }
.dt-par td.nm small{ display:block; font-family:var(--mono); color:var(--tx3); }
.dt-par .ds-spark{ width:180px; height:28px; }
.dt-plotrow>td{ padding:0 !important; background:var(--bg); }
.dt-plot{ position:relative; height:260px; padding:var(--sp-3) var(--sp-4); }
.dt-gaps{ margin:var(--sp-2) var(--sp-4); }
.dt-cnt .bar{ display:inline-block; height:8px; background:var(--fill); border-radius:1px; vertical-align:middle; }
.dt-scroll{ overflow:auto; max-height:560px; position:relative; }
.ds-table td.lb-cell{ width:1%; padding-top:2px; padding-bottom:2px; text-align:right; }
@media (max-width:980px){
  .dt-wrap{ grid-template-columns:minmax(0,1fr); }
  .dt-rail{ position:static; max-height:none; }
  .dt-files{ max-height:240px; }
  .dt-facts{ grid-template-columns:repeat(2,minmax(0,1fr)); }
  .dt-facts>div{ border-bottom:1px solid var(--line); }
  .dt-par .ds-spark{ width:96px; }
  .dt-par .hide-sm{ display:none; }
}
</style>
</head><body>
<a class="ds-skip" href="#main" data-i18n>Skip to content</a>
<!--FRAME_BAR-->
<main id="main" class="tf-main dt-wrap">
  <aside class="ds-panel dt-rail" aria-labelledby="files-h">
    <div class="ds-panel-h"><span id="files-h" data-i18n>Dump files</span><span class="r" id="files-meta"></span></div>
    <div class="ds-panel-b ds-stack" style="gap:var(--sp-2)">
      <div class="dt-acts">
        <button type="button" class="ds-btn primary" id="btnLatest" data-i18n>Load latest</button>
        <button type="button" class="ds-btn" id="btnAll" data-i18n>Load all</button>
        <button type="button" class="ds-btn wide" id="btnSelected" data-i18n>Load selected</button>
      </div>
    </div>
    <div class="dt-files" id="dumpsList" role="group" aria-labelledby="files-h"></div>
    <details class="ds-disclosure" id="rangeBox">
      <summary><span data-i18n>Time window</span><span class="r" data-i18n>file time, UTC</span></summary>
      <div class="bd" style="padding-left:var(--sp-4)">
        <div class="dt-range">
          <div class="ds-field"><label for="from" data-i18n>From</label><input class="ds-input" type="datetime-local" id="from"></div>
          <div class="ds-field"><label for="to" data-i18n>To</label><input class="ds-input" type="datetime-local" id="to"></div>
        </div>
        <div class="ds-row" style="margin-top:var(--sp-2)"><button type="button" class="ds-btn sm" id="btnRange" data-i18n>Load range</button></div>
      </div>
    </details>
    <div class="ds-row" style="padding:var(--sp-2) var(--sp-4); border-top:1px solid var(--line)">
      <button type="button" class="ds-btn ghost sm" id="btnRefresh" data-i18n>Refresh list</button>
      <a class="ds-btn sm" href="reports" target="_blank" rel="noopener" id="btnReports"
         title="Pass report, daily ops review or anomaly investigation from these dumps (Markdown / HTML)" data-i18n-title><span data-i18n>Generate report…</span></a>
      <span id="lbReport"></span>
      <span class="ds-meta" id="pollNote"></span>
    </div>
  </aside>

  <div class="dt-main">
    <div id="limitBanner"></div>
    <section class="ds-panel" aria-labelledby="sum-h">
      <h2 class="ds-sr" id="sum-h" data-i18n>Summary</h2>
      <div class="dt-facts" id="summary"></div>
    </section>
    <section class="ds-panel" aria-labelledby="tl-h">
      <div class="ds-panel-h"><span id="tl-h" data-i18n>Dump timeline</span><span class="r" id="tl-meta"></span></div>
      <div class="dt-tl" id="timeline"></div>
      <div class="dt-legend" id="tlLegend"></div>
    </section>
    <section class="ds-panel" aria-labelledby="det-h">
      <h2 class="ds-sr" id="det-h" data-i18n>Details</h2>
      <div id="tabs" style="padding:0 var(--sp-3)"></div>
      <div class="dt-tabpanel" id="tabpanel" role="tabpanel" tabindex="0"></div>
    </section>
  </div>
</main>
<!--FRAME_SCRIPT-->
<script type="module">
import { renderValue, renderNoData, renderTabs, mountTabs, renderBanner, renderChip, renderFlag,
         setDisabled, setEnabled, glyph, esc } from "/static/shared/components.js";
import I18n from "/static/shared/i18n.js";
import { renderLogThis } from "/static/shared/logbook.js";
/* Logbook context: the dumps on screen and the open tab. A "Log this" on
 * a step change, a high/medium event or an S12 transition adds what it is
 * about ("anomaly"), which puts the anomaly ticket (WB-5.5-AT) first. */
window.c2oLogbookContext = () => {
  const names = [...loadedNames];
  const PAGES = { hk: "housekeeping", ev: "events", s12: "on-board monitoring", pk: "packet counts", an: "step changes" };
  return { page: PAGES[tab] || tab, ...(names.length ? { dump: names.length > 2 ? `${names[0]} … ${names[names.length - 1]} (${names.length})` : names.join(", ") } : {}) };
};
const lbThis = (ctx) => `<td class="lb-cell">${renderLogThis(ctx, { kind: "observation", iconOnly: true })}</td>`;
const T = (s, v) => I18n.tText(s, v);
const $ = (id) => document.getElementById(id);
const tok = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const CUC_EPOCH_UNIX_MS = Date.UTC(2000, 0, 1, 12, 0, 0);   // CUC = s since J2000 (mission.yaml time_epoch)
const utc = (cuc) => new Date(CUC_EPOCH_UNIX_MS + cuc * 1000);
const hms = (cuc) => (typeof cuc === "number" && isFinite(cuc)) ? utc(cuc).toISOString().substr(11, 8) : "";
const hmsms = (cuc) => (typeof cuc === "number" && isFinite(cuc)) ? utc(cuc).toISOString().substr(11, 12) : "";
const ymd = (cuc) => utc(cuc).toISOString().substr(0, 10);
const loc = () => (I18n.getLang() === "fr" ? "fr-FR" : "en-GB");
const n0 = (x) => Number(x).toLocaleString(loc());

let available = [], selected = new Set(), loadedNames = new Set(), store = "";
let decoded = null, tab = "hk", plots = {}, loading = null;

/* ── formatting ── */
function fmtNum(x) {
  if (x == null || !isFinite(x)) return "";
  if (Number.isInteger(x)) return String(x);
  const a = Math.abs(x);
  if (a !== 0 && (a < 1e-3 || a >= 1e6)) return x.toExponential(3);
  return x.toFixed(3);
}
const dur = (s) => s >= 3600 ? `${(s / 3600).toFixed(1)} h` : s >= 60 ? `${(s / 60).toFixed(1)} min` : `${Math.round(s)} s`;
const hex4 = (n) => "0x" + n.toString(16).padStart(4, "0").toUpperCase();
function fileWhen(d) {
  const t = d.timestamp || d.mtime || "";
  const m = /^(\d{4}-\d\d-\d\d)T(\d\d:\d\d)/.exec(t);
  return m ? `${m[1]} ${m[2]}` : t;
}
const kb = (b) => b >= 1048576 ? `${(b / 1048576).toFixed(1)} MB` : `${Math.round(b / 1024)} kB`;

/* ── status (title bar) ── */
function status(kind, text) {
  const el = $("tf-status");
  el.innerHTML = kind === "busy" ? `<span class="ds-chip is-active"><span class="ds-run" aria-hidden="true"></span>${esc(text)}</span>`
    : kind === "error" ? `<span class="ds-chip is-alarm">${glyph("alarm-up")}${esc(text)}</span>`
    : text ? `<span class="ds-meta">${esc(text)}</span>` : "";
}

/* ── archive list ── */
async function refreshDumps() {
  try {
    const j = await (await fetch("api/dumps")).json();
    available = j.dumps || []; store = j.dump_dir || "";
    for (const f of [...selected]) if (!available.some((d) => d.filename === f)) selected.delete(f);
    renderFiles();
    if (j.error) status("error", T("ERROR: {{msg}}", { msg: j.error }));
    return available;
  } catch (e) { status("error", T("ERROR: {{msg}}", { msg: String(e) })); return []; }
}
function renderFiles() {
  const root = $("dumpsList");
  // No server paths on a student screen (review §4.1): it is the dump archive.
  $("files-meta").textContent = T("Dumps: {{n}}", { n: available.length });
  document.getElementById("tf-meta").textContent = T("Dump archive");
  if (!available.length) {
    root.innerHTML = `<p class="tf-empty">${esc(T("No dumps yet. Request an S15 dump from mission control during a pass."))}</p>`;
  } else {
    root.innerHTML = [...available].reverse().map((d) => {
      const on = selected.has(d.filename);
      return `<label class="dt-file${on ? " is-active" : ""}${loadedNames.has(d.filename) ? " loaded" : ""}">` +
        `<span class="ds-check"><input type="checkbox" data-file="${esc(d.filename)}"${on ? " checked" : ""}></span>` +
        `<span class="when">${esc(fileWhen(d))}</span><span class="sz">${kb(d.size_bytes || 0)}</span>` +
        `<span class="fn">SID ${esc(d.sid ?? "?")} · ${esc(d.filename)}</span></label>`;
    }).join("");
  }
  paintButtons();
}
function paintButtons() {
  const none = T("The store has no dump files yet.");
  for (const id of ["btnLatest", "btnAll"]) available.length ? setEnabled($(id)) : setDisabled($(id), none);
  const sb = $("btnSelected");
  sb.textContent = selected.size ? T("Load selected ({{n}})", { n: selected.size }) : T("Load selected");
  if (!available.length) setDisabled(sb, none);
  else if (!selected.size) setDisabled(sb, T("Tick one or more files in the list first."));
  else setEnabled(sb);
  const rb = $("btnRange");
  if (!$("from").value && !$("to").value) setDisabled(rb, T("Set a From or To time first."));
  else setEnabled(rb);
  if (loading) for (const id of ["btnLatest", "btnAll", "btnSelected", "btnRange"])
    if (id !== loading) setDisabled($(id), T("A decode is running."));
}
$("dumpsList").addEventListener("change", (ev) => {
  const f = ev.target.dataset && ev.target.dataset.file;
  if (!f) return;
  ev.target.checked ? selected.add(f) : selected.delete(f);
  renderFiles();
});

/* ── decode ── */
async function loadDecoded(params, btnId) {
  if (loading) return;
  const btn = $(btnId);
  loading = btnId;
  const label = btn.textContent;
  btn.classList.add("is-active");
  btn.innerHTML = `<span class="ds-run" aria-hidden="true"></span>${esc(T("Decoding…"))}`;
  paintButtons();
  status("busy", T("decoding…"));
  try {
    const j = await (await fetch("api/decode?" + new URLSearchParams(params))).json();
    if (j.error) { status("error", T("ERROR: {{msg}}", { msg: j.error })); return; }
    decoded = j;
    loadedNames = new Set((j.files || []).map((f) => f.filename));
    for (const k of Object.keys(plots)) closePlot(k);
    render();
    status("", T("decoded {{n}} packet(s) from {{files}} file(s)", { n: n0(j.total_packets), files: j.files.length }));
  } catch (e) {
    status("error", T("ERROR: {{msg}}", { msg: String(e) }));
  } finally {
    loading = null;
    btn.classList.remove("is-active");
    btn.textContent = label;
    renderFiles();
  }
}
$("btnLatest").addEventListener("click", () => loadDecoded({ latest: 1 }, "btnLatest"));
$("btnAll").addEventListener("click", () => loadDecoded({ all: 1 }, "btnAll"));
$("btnSelected").addEventListener("click", () => loadDecoded({ files: [...selected].join(",") }, "btnSelected"));
$("btnRange").addEventListener("click", () => {
  const iso = (el) => el.value ? new Date(el.value + "Z").toISOString() : null;   // the picker is UTC
  const p = {}; const s = iso($("from")), u = iso($("to"));
  if (s) p.since = s; if (u) p.until = u;
  loadDecoded(p, "btnRange");
});
for (const id of ["from", "to"]) $(id).addEventListener("input", paintButtons);
$("btnRefresh").addEventListener("click", refreshDumps);

/* ── render: banner, facts, timeline, tabs ── */
function limitParams() {
  const out = [];
  for (const sid of decoded.hk) for (const p of sid.params)
    if (p.limit && p.limit.state !== "ok") out.push({ sid: sid.sid, ...p });
  out.sort((a, b) => (b.limit.state === "red") - (a.limit.state === "red") || b.limit.time_in_red_s - a.limit.time_in_red_s);
  return out;
}
function render() {
  if (!decoded) {
    $("limitBanner").innerHTML = "";
    $("summary").innerHTML = [T("Files"), T("Packets"), T("S5 events"), T("HK gaps"), T("On-board time")].map((k) =>
      `<div><span class="k">${esc(k)}</span>${renderNoData()}</div>`).join("");
    $("timeline").innerHTML = `<p class="tf-empty">${esc(T("Load the latest dump, all dumps, or a selection: what they contain is laid out here on the on-board time axis."))}</p>`;
    $("tlLegend").innerHTML = ""; $("tl-meta").textContent = "";
    $("tabs").innerHTML = ""; $("tabpanel").innerHTML = "";
    return;
  }
  const j = decoded, lp = limitParams();
  const red = lp.filter((p) => p.limit.state === "red"), yel = lp.filter((p) => p.limit.state === "yellow");
  const gapsN = j.hk.reduce((a, s) => a + (s.gaps || []).length, 0);
  $("limitBanner").innerHTML = !j.limits || !j.limits.checked
    ? renderBanner("nodata", T("No ground limits apply to the decoded parameters."))
    : red.length ? renderBanner("alarm", T("{{n}} parameter(s) went outside the alarm limits", { n: red.length }),
        { meta: red.slice(0, 3).map((p) => p.name).concat(red.length > 3 ? [T("+{{n}} more", { n: red.length - 3 })] : []) })
    : yel.length ? renderBanner("caution", T("{{n}} parameter(s) went outside the caution limits", { n: yel.length }),
        { meta: yel.slice(0, 3).map((p) => p.name) })
    : renderBanner("ok", T("All {{n}} limit-checked parameters stayed within limits", { n: j.limits.checked }));
  const span = j.first_cuc != null && j.last_cuc != null ? j.last_cuc - j.first_cuc : null;
  const fact = (k, v, small) => `<div><span class="k">${esc(k)}</span><span class="v">${v}${small ? ` <small>${esc(small)}</small>` : ""}</span></div>`;
  $("summary").innerHTML = [
    fact(T("Files"), n0(j.files.length)),
    fact(T("Packets"), n0(j.total_packets)),
    fact(T("S5 events"), n0(j.events.length), j.events.filter((e) => e.severity >= 3).length ? T("{{n}} medium or high", { n: j.events.filter((e) => e.severity >= 3).length }) : ""),
    fact(T("HK gaps"), n0(gapsN), T("in {{n}} SID(s)", { n: j.hk.length })),
    fact(T("On-board time"), span == null ? renderNoData() : `${hms(j.first_cuc).slice(0, 5)}–${hms(j.last_cuc).slice(0, 5)}`, span == null ? "" : dur(span)),
  ].join("");
  drawTimeline();
  drawTabs();
}

/* ── the dump timeline ── */
function drawTimeline() {
  const j = decoded, host = $("timeline");
  if (j.first_cuc == null) { host.innerHTML = `<p class="tf-empty">${esc(T("No time-tagged packets decoded."))}</p>`; return; }
  const W = Math.max(300, host.clientWidth - 32), narrow = W < 640;
  const L = narrow ? 92 : 168, R = 8, laneH = 24, t0 = j.first_cuc, t1 = Math.max(j.last_cuc, t0 + 1);
  const X = (c) => L + ((c - t0) / (t1 - t0)) * (W - L - R);
  const lp = limitParams().slice(0, 6);
  const lanes = [{ k: "files", lab: T("Dump files") }, { k: "ev", lab: T("S5 events") },
    ...j.hk.map((s) => ({ k: "sid", sid: s, lab: `SID ${s.sid}`, sub: s.name })),
    ...lp.map((p) => ({ k: "lim", p, lab: p.name }))];
  const H = lanes.length * laneH + 26;
  let s = `<svg class="tf-plot" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-labelledby="tl-h tl-desc">` +
    `<desc id="tl-desc">${esc(T("On-board time from {{a}} to {{b}} UTC: one lane per dump file set, events, each housekeeping SID (grey where samples exist, dashed amber where they stop) and each parameter that left its limits.", { a: hms(t0), b: hms(t1) }))}</desc>`;
  // time axis: ~6–10 ticks on round minutes
  const spanS = t1 - t0, steps = [60, 300, 600, 900, 1800, 3600, 7200, 10800, 21600, 43200, 86400];
  const step = steps.find((x) => spanS / x <= (narrow ? 4 : 9)) || 86400;
  for (let c = Math.ceil(t0 / step) * step; c <= t1; c += step) {
    const x = X(c);
    s += `<line class="grid" x1="${x}" y1="0" x2="${x}" y2="${H - 22}"/><text x="${x}" y="${H - 6}" text-anchor="middle">${hms(c).slice(0, 5)}</text>`;
  }
  lanes.forEach((ln, i) => {
    const y = i * laneH, mid = y + laneH / 2;
    s += `<line class="lane" x1="${L}" y1="${y + laneH}" x2="${W - R}" y2="${y + laneH}"/>`;
    const room = Math.floor((L - (ln.k === "lim" ? 22 : 6)) / 6.8);
    const cut = (x) => x.length > room ? x.slice(0, Math.max(1, room - 1)) + "…" : x;
    const lab = `${esc(cut(ln.lab))}<title>${esc(ln.lab)}</title>` + (ln.sub && !narrow ? ` <tspan class="labs">${esc(ln.sub)}</tspan>` : "");
    if (ln.k === "lim") {   // shape + colour: filled triangle = alarm, hollow = caution (P6)
      const red = ln.p.limit.state === "red";
      s += `<path class="${red ? "ev4" : "ev3"}" d="M5 ${mid - 5}L10 ${mid + 4}L0 ${mid + 4}Z"><title>${esc(red ? T("outside the alarm limits") : T("outside the caution limits"))}</title></path>`;
      s += `<text class="lab" x="16" y="${mid + 4}">${lab}</text>`;
    } else s += `<text class="lab" x="0" y="${mid + 4}">${lab}</text>`;
    if (ln.k === "files") for (const f of j.files) if (f.first_cuc != null) {
      s += `<rect class="file" x="${X(f.first_cuc).toFixed(1)}" y="${y + 6}" width="${Math.max(2, X(f.last_cuc) - X(f.first_cuc)).toFixed(1)}" height="${laneH - 12}" rx="1"><title>${esc(f.filename)} · ${hms(f.first_cuc)}–${hms(f.last_cuc)} · ${n0(f.packets)} ${esc(T("packets"))}</title></rect>`;
    }
    if (ln.k === "ev") for (const e of j.events) {
      const x = X(e.cuc).toFixed(1), sev = e.severity >= 4 ? 4 : e.severity >= 3 ? 3 : 1;
      const tip = `<title>${hmsms(e.cuc)} · ${esc(SEV[e.severity] ? SEV[e.severity]() : "S5." + e.subtype)} · ${hex4(e.event_id)} ${esc(e.description)}</title>`;
      s += sev === 1 ? `<rect class="ev1" x="${x - 1}" y="${mid - 5}" width="2" height="10">${tip}</rect>`
        : `<path class="ev${sev}" d="M${x} ${mid - 6}L${+x + 6} ${mid + 5}L${x - 6} ${mid + 5}Z">${tip}</path>`;
    }
    if (ln.k === "sid") {
      const ts = ln.sid.params.length ? ln.sid.params[0].series.map((p) => p[0]) : [];
      const gaps = ln.sid.gaps || [];
      // coverage = sample span minus gaps (and minus file boundaries further apart than 3 cadences)
      let a = ts[0], prev = ts[0];
      const cad = ln.sid.cadence_s || 1;
      const flush = (b) => { if (a != null) s += `<rect class="cov" x="${X(a).toFixed(1)}" y="${mid - 4}" width="${Math.max(1.5, X(b) - X(a)).toFixed(1)}" height="8"/>`; };
      for (const t of ts.slice(1)) { if (t - prev > 3 * cad) { flush(prev); a = t; } prev = t; }
      flush(prev);
      for (const g of gaps) {
        const gx = X(g.start_cuc), gw = Math.max(2, X(g.end_cuc) - gx);
        s += `<rect class="gap" x="${gx.toFixed(1)}" y="${mid - 6}" width="${gw.toFixed(1)}" height="12"><title>${esc(T("No data {{a}}–{{b}} ({{d}})", { a: hms(g.start_cuc), b: hms(g.end_cuc), d: dur(g.duration_s) }))}</title></rect>`;
        if (gw > 60) s += `<text class="gapt" x="${(gx + gw / 2).toFixed(1)}" y="${mid + 4}" text-anchor="middle">${esc(T("no data"))}</text>`;
      }
    }
    if (ln.k === "lim") {
      const b = ln.p.limit.band, ser = ln.p.series;
      const cls = (v) => (b.red_low != null && v < b.red_low) || (b.red_high != null && v > b.red_high) ? "exr"
        : (b.yellow_low != null && v < b.yellow_low) || (b.yellow_high != null && v > b.yellow_high) ? "exy" : "";
      let st = null, a = null, prev = null;
      const flush = () => { if (st) s += `<rect class="${st}" x="${X(a).toFixed(1)}" y="${mid - 4}" width="${Math.max(2, X(prev) - X(a)).toFixed(1)}" height="8"><title>${esc(ln.p.name)} ${hms(a)}–${hms(prev)} ${st === "exr" ? T("outside the alarm limits") : T("outside the caution limits")}</title></rect>`; };
      for (const [c, v] of ser) { const k = cls(v); if (k !== st || (prev != null && c - prev > 30)) { flush(); st = k; a = c; } prev = c; }
      flush();
    }
  });
  s += `<line class="ax" x1="${L}" y1="${H - 22}" x2="${W - R}" y2="${H - 22}"/></svg>`;
  host.innerHTML = s;
  const more = limitParams().length - lp.length;
  // An OBC clock that was never synchronised reads J2000 (2000-01-01).
  const unsynced = typeof t0 === "number" && utc(t0).getUTCFullYear() <= 2000;
  $("tl-meta").textContent = `${ymd(t0)} · ${T("on-board time, UTC")}` +
    (unsynced ? ` · ${T("OBC clock not synchronised")}` : "") + (more > 0 ? ` · ${T("+{{n}} more limit lanes in Housekeeping", { n: more })}` : "");
  const sw = (svg) => `<svg viewBox="0 0 16 10" aria-hidden="true">${svg}</svg>`;
  $("tlLegend").innerHTML = [
    [sw(`<rect class="cov" x="0" y="2" width="16" height="6"/>`), T("Samples received")],
    [sw(`<rect class="gap" x="0.5" y="0.5" width="15" height="9"/>`), T("Gap: the SID produced nothing")],
    [sw(`<rect class="ev1" x="7" y="0" width="2" height="10"/>`), T("Info event")],
    [sw(`<path class="ev3" d="M8 0L14 10L2 10Z"/>`), T("Medium-severity event")],
    [sw(`<path class="ev4" d="M8 0L14 10L2 10Z"/>`), T("High-severity event")],
    [sw(`<rect class="exy" x="0" y="2" width="16" height="6"/>`), T("Outside caution limits")],
    [sw(`<rect class="exr" x="0" y="2" width="16" height="6"/>`), T("Outside alarm limits")],
  ].map(([g, t]) => `<span class="dt-tl" style="padding:0">${g}${esc(t)}</span>`).join("");
}
const SEV = { 1: () => T("Info"), 2: () => T("Low"), 3: () => T("Medium"), 4: () => T("High") };

/* ── detail tabs ── */
function drawTabs() {
  const j = decoded;
  const s12n = (j.s12_transitions || []).length;
  const hkN = j.hk.reduce((a, s) => a + s.params.length, 0);
  $("tabs").innerHTML = renderTabs([
    { id: "hk", label: T("Housekeeping"), count: hkN },
    { id: "ev", label: T("Events"), count: j.events.length, countKind: j.events.some((e) => e.severity >= 4) ? "alarm" : j.events.some((e) => e.severity >= 3) ? "warn" : undefined },
    { id: "s12", label: T("On-board monitoring"), count: s12n },
    { id: "pk", label: T("Packet counts") },
    { id: "an", label: T("Step changes"), count: j.anomalies.length },
  ], tab, { label: T("Details"), panel: "tabpanel" });
  mountTabs($("tabs"), (id) => { tab = id; for (const k of Object.keys(plots)) closePlot(k); drawTabs(); });
  $("tabpanel").setAttribute("aria-labelledby", "tab-" + tab);
  $("tabpanel").innerHTML = { hk: hkPanel, ev: evPanel, s12: s12Panel, pk: pkPanel, an: anPanel }[tab]();
}

function spark(p) {
  const pts = p.series;
  if (!pts || pts.length < 2) return "";
  const w = 180, h = 28, b = p.limit && p.limit.band;
  const xs = pts.map((q) => q[0]), ys = pts.map((q) => q[1]);
  const x0 = xs[0], x1 = xs[xs.length - 1];
  let y0 = Math.min(...ys), y1 = Math.max(...ys);
  const lims = b ? [b.yellow_low, b.yellow_high, b.red_low, b.red_high].filter((v) => v != null) : [];
  for (const v of lims) if (v >= y0 - (y1 - y0) * 0.5 && v <= y1 + (y1 - y0) * 0.5) { y0 = Math.min(y0, v); y1 = Math.max(y1, v); }
  const dx = (x1 - x0) || 1, dy = (y1 - y0) || 1;
  const X = (x) => ((x - x0) / dx) * (w - 2) + 1, Y = (y) => (h - 2) - ((y - y0) / dy) * (h - 4);
  let d = "", pen = false;
  const gl = p.gaps || []; let gi = 0;
  for (let i = 0; i < pts.length; i++) {
    if (i > 0 && gi < gl.length && pts[i - 1][0] <= gl[gi].start_cuc && pts[i][0] >= gl[gi].end_cuc) { pen = false; gi++; }
    d += `${pen ? "L" : "M"}${X(pts[i][0]).toFixed(1)} ${Y(pts[i][1]).toFixed(1)}`; pen = true;
  }
  let lim = "";
  if (b) for (const [k, c] of [["yellow_low", ""], ["yellow_high", ""], ["red_low", " r"], ["red_high", " r"]]) {
    const v = b[k]; if (v == null || v < y0 || v > y1) continue;
    lim += `<line class="lim${c}" x1="0" x2="${w}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}"/>`;
  }
  const st = p.limit ? (p.limit.state === "red" ? " is-alarm" : p.limit.state === "yellow" ? " is-caution" : "") : "";
  return `<svg class="ds-spark${st}" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true">${lim}<path d="${d}"/></svg>`;
}
function limitCell(p) {
  const l = p.limit;
  if (!l) return `<span class="ds-meta">${esc(T("no limit"))}</span>`;
  if (l.state === "ok") return `<span class="ds-chip">${esc(T("in limits"))}</span>`;
  let out = "";
  if (l.time_in_red_s > 0) out += `<span class="ds-chip is-alarm">${glyph("alarm-up")}${esc(T("alarm {{d}}", { d: dur(l.time_in_red_s) }))}</span> `;
  if (l.time_in_yellow_s > 0) out += `<span class="ds-chip is-caution">${glyph("warn-up")}${esc(T("caution {{d}}", { d: dur(l.time_in_yellow_s) }))}</span>`;
  return out;
}
function hkPanel() {
  const j = decoded;
  if (!j.hk.length) return `<p class="tf-empty">${esc(T("No HK packets decoded."))}</p>`;
  return j.hk.map((sid, i) => {
    const gaps = sid.gaps || [];
    const worst = sid.params.some((p) => p.limit && p.limit.state === "red") ? "alarm" : sid.params.some((p) => p.limit && p.limit.state === "yellow") ? "warn" : "";
    const chips = (gaps.length ? renderChip({ kind: "warn", label: T("{{n}} gap(s)", { n: gaps.length }) }) : "") +
      (worst ? renderChip({ kind: worst, label: worst === "alarm" ? T("alarm limits") : T("caution limits") }) : "");
    const gapTable = gaps.length ? `<details class="ds-disclosure dt-gaps"><summary>${esc(T("SID {{sid}} stopped producing housekeeping {{n}} time(s) (cadence {{cad}} s); nothing is interpolated across a gap.", { sid: sid.sid, n: gaps.length, cad: sid.cadence_s }))}</summary>` +
      `<div class="bd"><table class="ds-table"><thead><tr><th>${esc(T("Gap start"))}</th><th>${esc(T("Gap end"))}</th><th class="n">${esc(T("Duration"))}</th><th class="n">${esc(T("Packets missing"))}</th></tr></thead><tbody>` +
      gaps.map((g) => `<tr><td class="num">${hmsms(g.start_cuc)}</td><td class="num">${hmsms(g.end_cuc)}</td><td class="n">${dur(g.duration_s)}</td><td class="n">~${g.missing}</td></tr>`).join("") +
      `</tbody></table></div></details>` : "";
    const rows = sid.params.map((p) => {
      const key = `${sid.sid}-${p.pid}`;
      return `<tr id="row-${key}"><td class="id">${hex4(p.pid)}</td><td class="nm">${esc(p.name)}</td>` +
        `<td>${spark(p)}</td>` +
        `<td class="n hide-sm">${renderValue(p.min, { units: p.units, digits: undefined })}</td>` +
        `<td class="n">${renderValue(p.mean, { units: p.units })}</td>` +
        `<td class="n hide-sm">${renderValue(p.max, { units: p.units })}</td>` +
        `<td>${limitCell(p)}</td>` +
        `<td><button type="button" class="ds-btn sm" data-plot="${key}" aria-pressed="false" aria-label="${esc(T("Plot {{name}}", { name: p.name }))}">${esc(T("Plot"))}</button></td></tr>`;
    }).join("");
    return `<details class="ds-disclosure dt-sid"${i === 0 ? " open" : ""}><summary>SID ${sid.sid}${sid.name ? ` · ${esc(sid.name)}` : ""}` +
      `<span class="tf-sub">&nbsp;${esc(T("{{p}} packets, {{n}} parameters", { p: n0(sid.packet_count), n: sid.params.length }))}</span>${chips}` +
      `</summary>` +
      `<div class="bd"><div class="ds-row" style="padding:var(--sp-1) var(--sp-4)">${gapTable ? "" : ""}<button type="button" class="ds-btn ghost sm" data-plotall="${sid.sid}" aria-pressed="false">${esc(T("Plot all"))}</button></div>${gapTable}<div class="dt-scroll" tabindex="0" aria-label="${esc(T("Parameters of SID {{sid}}", { sid: sid.sid }))}"><table class="ds-table dt-par"><thead><tr><th>ID</th><th>${esc(T("Name"))}</th><th>${esc(T("Trend"))}</th>` +
      `<th class="n hide-sm">Min</th><th class="n">${esc(T("Mean"))}</th><th class="n hide-sm">Max</th><th>${esc(T("Limits"))}</th><th><span class="ds-sr">${esc(T("Plot"))}</span></th></tr></thead>` +
      `<tbody id="sid-${sid.sid}-rows">${rows}</tbody></table></div></div></details>`;
  }).join("");
}
function evPanel() {
  const ev = decoded.events;
  if (!ev.length) return `<p class="tf-empty">${esc(T("No events."))}</p>`;
  return `<div class="dt-scroll" tabindex="0" aria-label="${esc(T("Events"))}"><table class="ds-table"><thead><tr><th>${esc(T("On-board time"))}</th><th>${esc(T("Severity"))}</th><th>${esc(T("Event ID"))}</th><th>${esc(T("Description"))}</th><th><span class="ds-sr">${esc(T("Logbook"))}</span></th></tr></thead><tbody>` +
    ev.map((e) => {
      const sv = e.severity >= 4 ? `<span class="ds-chip is-alarm">${glyph("alarm-up")}${esc(T("High"))}</span>`
        : e.severity >= 3 ? `<span class="ds-chip is-caution">${glyph("warn-up")}${esc(T("Medium"))}</span>`
        : `<span class="ds-chip">${esc((SEV[e.severity] || SEV[1])())}</span>`;
      const lb = e.severity >= 3 ? lbThis({ anomaly: `${hex4(e.event_id)} ${e.description || ""}`.trim() }) : "<td></td>";
      return `<tr><td class="num">${hmsms(e.cuc)}</td><td>${sv}</td><td class="num">${hex4(e.event_id)}</td><td>${e.description ? esc(e.description) : renderNoData({ label: T("no text") })}</td>${lb}</tr>`;
    }).join("") + `</tbody></table></div>`;
}
function s12Panel() {
  const tr = decoded.s12_transitions || [], defs = decoded.s12_definitions || [];
  if (!tr.length && !defs.length) return `<p class="tf-empty">${esc(T("No S12 monitoring packets in this dump."))}</p>`;
  let h = "";
  if (tr.length) {
    const entered = tr.filter((t) => t.entered).length;
    h += `<div style="padding:var(--sp-2) var(--sp-4)" class="ds-meta">${esc(T("{{n}} check transition(s): {{a}} out of limits, {{b}} back to nominal.", { n: tr.length, a: entered, b: tr.length - entered }))}</div>` +
      `<div class="dt-scroll" tabindex="0" aria-label="${esc(T("Check transitions"))}"><table class="ds-table"><thead><tr><th>${esc(T("On-board time"))}</th><th class="n">${esc(T("Monitor"))}</th><th>${esc(T("Parameter"))}</th><th>${esc(T("Transition"))}</th>` +
      `<th class="n">${esc(T("Value"))}</th><th>${esc(T("Check"))}</th><th>${esc(T("Severity"))}</th><th>${esc(T("Limit band"))}</th><th><span class="ds-sr">${esc(T("Logbook"))}</span></th></tr></thead><tbody>` +
      tr.map((t) => `<tr><td class="num">${t.cuc == null ? renderNoData() : hmsms(t.cuc)}</td><td class="n">${t.mon_id ?? ""}</td>` +
        `<td><span class="ds-id">${esc(t.param_hex || "")}</span> ${esc(t.param_name || "")}</td>` +
        `<td>${t.entered ? `<span class="ds-chip is-alarm">${glyph("alarm-up")}${esc(T("Out of limits"))}</span>` : `<span class="ds-chip ok">${esc(T("Back to nominal"))}</span>`}</td>` +
        `<td class="n">${renderValue(t.value, { units: t.units || "" })}</td><td>${esc(t.check_type_name || "")}</td>` +
        `<td>${esc(t.severity_name || "")}</td><td class="num">${t.band ? esc(t.band) : renderNoData({ label: T("not reported") })}</td>` +
        (t.entered ? lbThis({ anomaly: `${t.param_name || t.param_hex || ""} ${T("Out of limits")}`.trim(), ...(t.param_hex ? { param: t.param_hex } : {}) }) : "<td></td>") + `</tr>`).join("") +
      `</tbody></table></div>`;
  }
  if (defs.length) h += `<details class="ds-disclosure"><summary>${esc(T("Monitoring definitions (TM 12,13)"))}<span class="r">${defs.length}</span></summary><div class="bd">` +
    `<table class="ds-table"><thead><tr><th class="n">${esc(T("Monitor"))}</th><th>${esc(T("Parameter"))}</th><th>${esc(T("Check"))}</th><th>${esc(T("State"))}</th><th class="n">${esc(T("Low"))}</th><th class="n">${esc(T("High"))}</th></tr></thead><tbody>` +
    defs.map((d) => `<tr><td class="n">${d.mon_id}</td><td><span class="ds-id">${esc(d.param_hex || "")}</span> ${esc(d.param_name || "")}</td><td>${esc(d.check_type_name || "")}</td>` +
      `<td>${d.enabled ? esc(T("enabled")) : `<span class="ds-chip is-disabled">${esc(T("disabled"))}</span>`}</td><td class="n">${fmtNum(d.low_limit)}</td><td class="n">${fmtNum(d.high_limit)}</td></tr>`).join("") +
    `</tbody></table></div></details>`;
  return h;
}
const SVC = { "1.1": () => T("TC acceptance"), "1.2": () => T("TC acceptance failure"), "1.7": () => T("TC completion"),
  "1.8": () => T("TC completion failure"), "3.25": () => T("HK report"), "5.1": () => T("Event (info)"),
  "5.2": () => T("Event (low)"), "5.3": () => T("Event (medium)"), "5.4": () => T("Event (high)"),
  "12.9": () => T("Check transition"), "12.10": () => T("Check transition"), "12.13": () => T("Monitoring definitions") };
function pkPanel() {
  const pc = decoded.packet_counts;
  if (!pc.length) return `<p class="tf-empty">${esc(T("No packets decoded."))}</p>`;
  const mx = Math.max(...pc.map((c) => c.count));
  return `<table class="ds-table dt-cnt"><thead><tr><th>${esc(T("Service"))}</th><th>${esc(T("Meaning"))}</th><th class="n">${esc(T("Count"))}</th><th style="width:40%"><span class="ds-sr">${esc(T("Share"))}</span></th></tr></thead><tbody>` +
    pc.map((c) => { const k = `${c.service}.${c.subtype}`; return `<tr><td class="num">TM(${c.service},${c.subtype})</td><td>${SVC[k] ? esc(SVC[k]()) : ""}</td><td class="n">${n0(c.count)}</td>` +
      `<td><span class="bar" style="width:${Math.max(1, c.count / mx * 100).toFixed(1)}%"></span></td></tr>`; }).join("") + `</tbody></table>`;
}
function anPanel() {
  const an = [...decoded.anomalies].sort((a, b) => b.peak_delta / b.mean_delta - a.peak_delta / a.mean_delta);
  if (!an.length) return `<p class="tf-empty">${esc(T("No step changes: no parameter jumped by more than five times its mean sample-to-sample change."))}</p>`;
  return `<p class="ds-meta" style="padding:var(--sp-2) var(--sp-4)">${esc(T("Parameters whose largest sample-to-sample change is more than five times their mean change. Often a mode change, sometimes a fault."))}</p>` +
    `<div class="dt-scroll" tabindex="0" aria-label="${esc(T("Step changes"))}"><table class="ds-table"><thead><tr><th>SID</th><th>${esc(T("Name"))}</th><th class="n">${esc(T("Largest step"))}</th><th class="n">${esc(T("Mean step"))}</th><th class="n">${esc(T("Ratio"))}</th><th><span class="ds-sr">${esc(T("Logbook"))}</span></th></tr></thead><tbody>` +
    an.map((a) => `<tr><td class="num">${a.sid}</td><td>${esc(a.name)}</td><td class="n">${fmtNum(a.peak_delta)}</td><td class="n">${fmtNum(a.mean_delta)}</td><td class="n">×${(a.peak_delta / a.mean_delta).toFixed(0)}</td>` +
      lbThis({ anomaly: `SID ${a.sid} ${a.name}: ${T("step")} ×${(a.peak_delta / a.mean_delta).toFixed(0)}`, param: a.name }) + `</tr>`).join("") +
    `</tbody></table></div>`;
}

/* ── plots: open BELOW the row that asked, so nothing above moves ── */
function splitAcrossGaps(series, gaps) {
  const out = [];
  let gi = 0;
  for (let i = 0; i < series.length; i++) {
    while (gaps && gi < gaps.length && i > 0 && gaps[gi].start_cuc >= series[i - 1][0] && gaps[gi].end_cuc <= series[i][0]) {
      out.push({ x: (gaps[gi].start_cuc + gaps[gi].end_cuc) / 2, y: null }); gi++;
    }
    out.push({ x: series[i][0], y: series[i][1] });
  }
  return out;
}
const bandPlugin = {
  id: "limitBands",
  beforeDatasetsDraw(chart, _a, o) {
    const b = o && o.band; if (!b) return;
    const area = chart.chartArea, y = chart.scales.y, ctx = chart.ctx;
    ctx.save(); ctx.setLineDash([4, 3]); ctx.lineWidth = 1;
    for (const [k, c] of [["yellow_low", "--warn"], ["yellow_high", "--warn"], ["red_low", "--alarm"], ["red_high", "--alarm"]]) {
      const v = b[k]; if (v == null) continue;
      const yv = y.getPixelForValue(v); if (yv < area.top || yv > area.bottom) continue;
      ctx.strokeStyle = tok(c); ctx.beginPath(); ctx.moveTo(area.left, yv); ctx.lineTo(area.right, yv); ctx.stroke();
    }
    ctx.restore();
  },
};
function chartFor(canvas, datasets, band) {
  const grid = tok("--line"), ink = tok("--tx3");
  const font = { family: tok("--font-mono") || "monospace", size: 12 };
  return new Chart(canvas.getContext("2d"), {
    type: "line", data: { datasets },
    options: {
      responsive: true, maintainAspectRatio: false, animation: false, parsing: false, normalized: true,
      interaction: { mode: "nearest", intersect: false, axis: "x" },
      plugins: {
        legend: { display: datasets.length > 1, position: "bottom", labels: { color: tok("--tx2"), font, boxWidth: 12, boxHeight: 2 } },
        tooltip: { backgroundColor: tok("--s3"), titleColor: tok("--val"), bodyColor: tok("--tx"), borderColor: tok("--line-2"), borderWidth: 1,
          titleFont: font, bodyFont: font,
          callbacks: { title: (c) => `${hmsms(c[0].parsed.x)} UTC`, label: (c) => `${c.dataset.label}: ${fmtNum(c.parsed.y)}` } },
        limitBands: { band },
      },
      scales: {
        x: { type: "linear", ticks: { color: ink, font, maxTicksLimit: 8, callback: (v) => hms(v) }, grid: { color: grid } },
        y: { ticks: { color: ink, font }, grid: { color: grid } },
      },
    },
    plugins: [bandPlugin],
  });
}
const SERIES_TOKENS = ["--tx2", "--cat-1", "--cat-2", "--cat-3", "--cat-4", "--cat-5", "--cat-6", "--cat-7"];
function openPlot(key, afterRow, title, build) {
  const tr = document.createElement("tr");
  tr.className = "dt-plotrow"; tr.id = "plot-" + key;
  tr.innerHTML = `<td colspan="8"><div class="dt-plot" role="img" aria-label="${esc(title)}"><canvas></canvas></div></td>`;
  afterRow.after(tr);
  plots[key] = { tr, build, chart: build(tr.querySelector("canvas")) };
}
function closePlot(key) {
  const p = plots[key]; if (!p) return;
  try { p.chart.destroy(); } catch (e) { /* gone */ }
  p.tr.remove(); delete plots[key];
  const b = document.querySelector(`[data-plot="${key}"],[data-plotall="${key.replace(/^all-/, "")}"]`);
  if (b) b.setAttribute("aria-pressed", "false");
}
document.addEventListener("click", (ev) => {
  const b = ev.target.closest("[data-plot],[data-plotall]");
  if (!b || !decoded || typeof Chart === "undefined") return;
  ev.preventDefault();
  if (b.dataset.plot) {
    const key = b.dataset.plot;
    if (plots[key]) return closePlot(key);
    const [sid, pid] = key.split("-").map(Number);
    const p = decoded.hk.find((s) => s.sid === sid).params.find((q) => q.pid === pid);
    b.setAttribute("aria-pressed", "true");
    openPlot(key, $("row-" + key), T("Plot {{name}}", { name: p.name }), (cv) => chartFor(cv, [{
      label: `${p.name}${p.units ? " [" + p.units + "]" : ""}`, data: splitAcrossGaps(p.series, p.gaps),
      borderColor: tok("--tx2"), borderWidth: 1.5, pointRadius: 0, spanGaps: false, tension: 0 }],
      p.limit && p.limit.band));
  } else {
    const sid = +b.dataset.plotall, key = "all-" + sid;
    if (plots[key]) return closePlot(key);
    const s = decoded.hk.find((x) => x.sid === sid);
    const body = $(`sid-${sid}-rows`);
    if (!body) return;
    const det = body.closest("details"); if (det) det.open = true;
    b.setAttribute("aria-pressed", "true");
    const head = document.createElement("tr"); body.prepend(head);
    openPlot(key, head, T("All parameters of SID {{sid}}", { sid }), (cv) => chartFor(cv, s.params.slice(0, 8).map((p, i) => ({
      label: p.name, data: splitAcrossGaps(p.series, s.gaps), borderColor: tok(SERIES_TOKENS[i % SERIES_TOKENS.length]),
      borderWidth: 1.25, pointRadius: 0, spanGaps: false, tension: 0 })), null));
    head.remove();
  }
});
window.addEventListener("c2o:themechange", () => {
  for (const p of Object.values(plots)) { p.chart.destroy(); p.chart = p.build(p.tr.querySelector("canvas")); }
});

/* ── boot ── */
let lastW = 0;
new ResizeObserver(() => { const w = $("timeline").clientWidth; if (decoded && Math.abs(w - lastW) > 4) { lastW = w; drawTimeline(); } }).observe($("timeline"));
const rerender = () => {
  renderFiles(); render(); $("pollNote").textContent = T("checks for new files every 30 s");
  $("lbReport").innerHTML = renderLogThis({}, { kind: "observation" });
};
window.addEventListener("smo:i18nready", rerender);
window.addEventListener("smo:langchange", rerender);
rerender();
refreshDumps().then((list) => { if (list.length) loadDecoded({ latest: 1 }, "btnLatest"); });
setInterval(refreshDumps, 30000);
</script>
</body></html>
"""


# ---------- entrypoint ----------

def main(argv: list[str] | None = None) -> int:
    import os
    parser = argparse.ArgumentParser(description="Delayed TM viewer")
    parser.add_argument("--port", type=int, default=8092)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--dumps", default=None,
                        help="Directory containing dump_*.bin files "
                             "(default: $SMO_DUMP_DIR, else mission dump_dir, "
                             "else workspace/dumps)")
    parser.add_argument("--api", default=os.environ.get("SMO_DUMP_API"),
                        help="Read the store over HTTP from a service that "
                             "serves it (e.g. http://server:9090) instead of "
                             "the local filesystem. Also honoured via "
                             "SMO_DUMP_API.")
    parser.add_argument("--public", action="store_true",
                        help="Bind 0.0.0.0 (also honoured via SMO_PUBLIC=1)")
    # ── one-shot report mode (Phase F) ──
    parser.add_argument("--report", metavar="TEMPLATE", default=None,
                        help="Generate a report from a template id (e.g. "
                             "pass_report, daily_ops_review, "
                             "anomaly_investigation) or a YAML path, then "
                             "exit — no server is started. Uses the same "
                             "library as the MCS /reports page.")
    parser.add_argument("--period-start", default=None,
                        help="With --report: absolute period start "
                             "(ISO-8601 UTC, CUC-based selection)")
    parser.add_argument("--period-end", default=None,
                        help="With --report: absolute period end")
    parser.add_argument("--var", action="append", default=[],
                        metavar="KEY=VALUE",
                        help="With --report: template vars "
                             "(e.g. --var t0=2026-08-20T16:18:22Z)")
    parser.add_argument("-o", "--out", default=None,
                        help="With --report: output HTML path "
                             "(default workspace/reports/<auto>)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    host = "0.0.0.0" if (args.public or os.environ.get("SMO_PUBLIC") == "1") else args.host

    if args.report:
        # One-shot report generation over the local store, no server.
        from smo_common.reporting import generate_report
        from smo_common.reporting.spec import SpecError
        mission_cfg = None
        try:
            from smo_common.config.loader import load_mission_config
            mission_cfg = load_mission_config(REPO / "configs" / "eosat1")
        except Exception:  # noqa: BLE001
            pass
        dump_dir = resolve_dump_dir(mission_cfg, explicit=args.dumps).resolve()
        period = None
        if args.period_start and args.period_end:
            period = {"kind": "absolute", "start": args.period_start,
                      "end": args.period_end}
        vars_ = {}
        for kv in args.var:
            if "=" in kv:
                k, v = kv.split("=", 1)
                vars_[k.strip()] = v.strip()
        try:
            meta = generate_report(
                args.report, config_dir=REPO / "configs" / "eosat1",
                dump_dir=dump_dir, vars=vars_, period_override=period,
                out_path=args.out)
        except SpecError as e:
            for err in e.errors:
                print(f"spec error — {err['path']}: {err['msg']}",
                      file=sys.stderr)
            return 2
        except FileNotFoundError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(f"{meta['title']}: {meta['packets']} packets over "
              f"{meta['period']['start_utc']} → {meta['period']['end_utc']}"
              f" -> {meta['path']}")
        return 0

    if args.api:
        app = make_app(None, api_base=args.api)
        logger.info("Delayed TM viewer listening on http://%s:%d (API store=%s)",
                    host, args.port, args.api)
    else:
        # Shared resolution order: --dumps > SMO_DUMP_DIR > mission dump_dir >
        # workspace/dumps. Resolved to an absolute path here because the viewer
        # may be started from a different working directory than the simulator.
        mission_cfg = None
        try:
            from smo_common.config.loader import load_mission_config
            mission_cfg = load_mission_config(REPO / "configs" / "eosat1")
        except Exception as e:  # noqa: BLE001 — config is optional for this tool
            logger.debug("No mission config for dump_dir resolution: %s", e)
        dump_dir = resolve_dump_dir(mission_cfg, explicit=args.dumps).resolve()
        dump_dir.mkdir(parents=True, exist_ok=True)
        app = make_app(dump_dir)
        logger.info("Delayed TM viewer listening on http://%s:%d (dumps=%s)",
                    host, args.port, dump_dir)

    web.run_app(app, host=host, port=args.port, print=None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
