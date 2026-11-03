"""SMO Simulator — automatic snapshots before injected faults, kept on disk.

INSTRUCTOR_CONSOLE_DESIGN.md §13 item 6 (ruled 2026-11-03). Before every
injected fault (an instructor inject with "snapshot first", or a scenario
inject event) the simulator saves a full breakpoint, so the instructor can
put the team back just before the fault. These used to live in RAM only
(newest six) and were lost with the process; a restart or crash is exactly
when an instructor needs one.

Policy as built:

* Directory: ``SMO_AUTO_SNAPSHOT_DIR`` > simulation.yaml
  ``auto_snapshots.dir`` (default ``workspace/snapshots/auto``, i.e.
  ``/opt/smo/workspace/snapshots/auto`` in the container, on the space
  workspace volume). Only files named ``auto_*.json.gz`` there are ever
  touched; manual snapshots (``workspace/breakpoints/``) never are.
* File name: ``auto_<run>__<sim time UTC>__<fault>.json.gz`` — the run, the
  simulated time and the fault (``subsystem.failure``, ``+`` for a batch).
* A *run* is one scenario run (``scn-<scenario>-<wall stamp>``) or, outside
  scenarios, the free run since the simulator started (``free-<stamp>``).
  Starting a scenario starts a new run and deletes every auto snapshot of the
  previous runs (disk and memory). A simulator restart does NOT: the files of
  the run that was going on are listed again, marked "before restart", and can
  be restored.
* Retention: newest ``keep_per_run`` (10) per run; files older than
  ``max_age_h`` (48 h, file time) are deleted at start and at every save;
  whichever comes first.
* Size: each snapshot is gzip-compressed JSON (typically 50-500 kB). One that
  is still larger than ``max_snapshot_mb`` is kept in memory only (and the
  timeline says so); the folder is held under ``max_total_mb`` by dropping the
  oldest files; nothing is written while the disk has less than
  ``min_free_mb`` free.

The state is captured on the tick thread (BreakpointManager.save, consistent
between ticks); compression and the write happen on one background thread.
"""
from __future__ import annotations

import gzip
import json
import logging
import os
import re
import shutil
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

PREFIX = "auto_"
SUFFIX = ".json.gz"
_FILE_RE = re.compile(r"^auto_(?P<run>[A-Za-z0-9._-]+)__(?P<sim>\d{8}T\d{6}Z)__"
                      r"(?P<fault>[A-Za-z0-9._+-]+)(?:__(?P<n>\d+))?\.json\.gz$")


def _slug(text: str, keep: str = "._+-") -> str:
    out = "".join(c if (c.isalnum() or c in keep) else "_" for c in str(text))
    return re.sub(r"_+", "_", out).strip("_")[:80] or "fault"


def _wall_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


class AutoSnapshotStore:
    """Newest auto snapshots of the current run in memory, all of them on disk."""

    def __init__(self, engine, cfg=None, *, directory: str | Path | None = None):
        self.engine = engine
        get = (lambda k, d: getattr(cfg, k, d)) if cfg is not None and not isinstance(cfg, dict) \
            else (lambda k, d: (cfg or {}).get(k, d))
        self.keep_per_run = max(1, int(get("keep_per_run", 10)))
        self.max_age_s = float(get("max_age_h", 48.0)) * 3600.0
        self.max_snapshot_bytes = int(float(get("max_snapshot_mb", 25.0)) * 1e6)
        self.max_total_bytes = int(float(get("max_total_mb", 250.0)) * 1e6)
        self.min_free_bytes = int(float(get("min_free_mb", 200.0)) * 1e6)
        d = directory or os.environ.get("SMO_AUTO_SNAPSHOT_DIR") or get("dir", "workspace/snapshots/auto")
        self.dir = Path(d)
        self.run_id = f"free-{_wall_stamp()}"
        self._lock = threading.RLock()
        self._mem: "OrderedDict[str, dict]" = OrderedDict()      # name -> state (this run)
        self._meta: "OrderedDict[str, dict]" = OrderedDict()     # name -> listing row
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="auto-snap")
        self._pending: list = []
        self.prune()
        self._scan()

    # ── naming ──────────────────────────────────────────────────────────
    @staticmethod
    def display_name(sim_iso: str, fault: str) -> str:
        return f"auto {sim_iso[:10]} {sim_iso[11:19]} before {fault}"

    def _filename(self, sim_dt: datetime, fault: str) -> str:
        base = f"{PREFIX}{_slug(self.run_id, '._-')}__{sim_dt.strftime('%Y%m%dT%H%M%SZ')}__{_slug(fault.replace('/', '.'))}"
        name, n = base + SUFFIX, 2
        while (self.dir / name).exists():
            name, n = f"{base}__{n}{SUFFIX}", n + 1
        return name

    # ── disk listing ────────────────────────────────────────────────────
    def _files(self) -> list[Path]:
        try:
            return sorted((p for p in self.dir.glob(f"{PREFIX}*{SUFFIX}") if p.is_file()),
                          key=lambda p: p.stat().st_mtime)
        except OSError:
            return []

    def _scan(self) -> None:
        """List the files a previous process left (restorable after a restart)."""
        for p in self._files():
            m = _FILE_RE.match(p.name)
            if not m:
                continue
            sim = datetime.strptime(m.group("sim"), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
            fault = m.group("fault").replace(".", "/")
            name = self.display_name(sim.isoformat(), fault)
            if m.group("n"):
                name += f" ({m.group('n')})"
            st = p.stat()
            with self._lock:
                self._meta[name] = {"name": name, "file": p.name, "run": m.group("run"),
                                    "sim_time": sim.isoformat(), "fault": fault,
                                    "bytes": st.st_size, "on_disk": True,
                                    "saved_at": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
                                    "previous_process": True}

    # ── retention ───────────────────────────────────────────────────────
    def _delete(self, p: Path) -> None:
        try:
            p.unlink()
        except FileNotFoundError:
            pass
        except OSError as e:
            logger.warning("Auto snapshot %s not deleted: %s", p, e)
            return
        with self._lock:
            for name in [n for n, m in self._meta.items() if m.get("file") == p.name]:
                self._meta.pop(name, None)
                self._mem.pop(name, None)

    def prune(self) -> None:
        """Age limit, per-run count, folder size — oldest first."""
        now = time.time()
        files = self._files()
        for p in files:
            try:
                if now - p.stat().st_mtime > self.max_age_s:
                    self._delete(p)
            except OSError:
                continue
        by_run: dict[str, list[Path]] = {}
        for p in self._files():
            m = _FILE_RE.match(p.name)
            by_run.setdefault(m.group("run") if m else "?", []).append(p)
        for run_files in by_run.values():
            for p in run_files[:-self.keep_per_run]:
                self._delete(p)
        files = self._files()
        total = 0
        sizes = []
        for p in files:
            try:
                sizes.append((p, p.stat().st_size))
                total += sizes[-1][1]
            except OSError:
                pass
        for p, size in sizes:
            if total <= self.max_total_bytes:
                break
            self._delete(p)
            total -= size
        # memory: the newest keep_per_run of the current run only
        with self._lock:
            mine = [n for n, m in self._meta.items() if m.get("run") == _slug(self.run_id, "._-")
                    and not m.get("previous_process")]
            for n in mine[:-self.keep_per_run]:
                self._mem.pop(n, None)
                if not self._meta.get(n, {}).get("on_disk"):
                    self._meta.pop(n, None)

    def new_run(self, label: str) -> int:
        """A new scenario run: forget (and delete) every earlier auto snapshot."""
        self.wait()
        n = 0
        for p in self._files():
            self._delete(p)
            n += 1
        with self._lock:
            self._mem.clear()
            self._meta.clear()
            self.run_id = f"{_slug(label, '._-')}-{_wall_stamp()}"
        if n:
            logger.info("Auto snapshots: new run %s — %d old file(s) deleted", self.run_id, n)
        return n

    # ── save ────────────────────────────────────────────────────────────
    def take(self, fault: str) -> tuple[Optional[str], str]:
        """Snapshot now (tick thread). Returns (name, note); name None on failure."""
        from smo_simulator.breakpoints import BreakpointManager
        eng = self.engine
        sim_dt = eng._sim_time if eng._sim_time.tzinfo else eng._sim_time.replace(tzinfo=timezone.utc)
        name = self.display_name(sim_dt.isoformat(), fault)
        with self._lock:
            base, n = name, 2
            while name in self._meta:
                name, n = f"{base} ({n})", n + 1
        state = BreakpointManager(eng).save(name=name)
        state["auto"] = True
        state["auto_fault"] = fault
        state["auto_run"] = self.run_id
        raw = json.dumps(state, default=str).encode("utf-8")
        fname = self._filename(sim_dt, fault)
        row = {"name": name, "file": fname, "run": _slug(self.run_id, "._-"),
               "sim_time": sim_dt.isoformat(), "fault": fault, "bytes": None,
               "on_disk": False, "saved_at": datetime.now(timezone.utc).isoformat(),
               "previous_process": False, "note": ""}
        with self._lock:
            self._mem[name] = state
            self._meta[name] = row
        self._pending = [f for f in self._pending if not f.done()]
        self._pending.append(self._pool.submit(self._write, name, fname, raw))
        return name, ""

    def _write(self, name: str, fname: str, raw: bytes) -> None:
        try:
            blob = gzip.compress(raw, 6)
            row = self._meta.get(name)
            if row is None:            # a new run started in between
                return
            row["bytes"] = len(blob)
            if len(blob) > self.max_snapshot_bytes:
                row["note"] = (f"{len(blob) / 1e6:.1f} MB compressed, above the "
                               f"{self.max_snapshot_bytes / 1e6:.0f} MB limit: memory only")
                logger.warning("Auto snapshot %s: %s", name, row["note"])
                return
            self.dir.mkdir(parents=True, exist_ok=True)
            free = shutil.disk_usage(self.dir).free
            if free - len(blob) < self.min_free_bytes:
                row["note"] = f"disk nearly full ({free / 1e6:.0f} MB free): memory only"
                logger.warning("Auto snapshot %s: %s", name, row["note"])
                return
            tmp = self.dir / (fname + ".tmp")
            tmp.write_bytes(blob)
            os.replace(tmp, self.dir / fname)
            row["on_disk"] = True
            self.prune()
        except Exception as e:  # noqa: BLE001 — a failed write keeps the RAM copy
            logger.warning("Auto snapshot %s not written to disk: %s", name, e)
            if name in self._meta:
                self._meta[name]["note"] = f"not written to disk: {e}"

    def wait(self, timeout: float = 30.0) -> None:
        for f in list(self._pending):
            try:
                f.result(timeout=timeout)
            except Exception:  # noqa: BLE001
                pass
        self._pending = []

    # ── read ────────────────────────────────────────────────────────────
    def list(self) -> list[dict]:
        with self._lock:
            rows = [dict(r) for r in self._meta.values()
                    if r["name"] in self._mem or r.get("on_disk")]
        return sorted(rows, key=lambda r: r["sim_time"], reverse=True)

    def get(self, name: str) -> Optional[dict]:
        with self._lock:
            if name in self._mem:
                return self._mem[name]
            row = self._meta.get(name)
        if not row or not row.get("on_disk"):
            return None
        try:
            with gzip.open(self.dir / row["file"], "rb") as f:
                state: dict[str, Any] = json.loads(f.read().decode("utf-8"))
            return state
        except (OSError, ValueError) as e:
            logger.warning("Auto snapshot %s unreadable: %s", name, e)
            return None

    def __contains__(self, name: str) -> bool:
        with self._lock:
            return name in self._mem or bool(self._meta.get(name, {}).get("on_disk"))
