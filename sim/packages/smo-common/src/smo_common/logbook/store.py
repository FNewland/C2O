"""The participant logbook store (docs/plan_2026-11/LOGBOOK_SPEC.md §2).

One append-only JSONL file per person, ``<sha256(person_id)[:32]>.jsonl``
(mode 0600) in a 0700 directory. Every change is a new record; readers fold
them (last edit wins, a delete drops the entry). The same file format is
written by SpaceCDF's FastAPI implementation, so every tool on the ground VM
shares one logbook per person.

Concurrency: writers hold an exclusive ``fcntl.flock`` for the append,
readers a shared one. Whole-file rewrites (purge, compaction) happen IN
PLACE under the exclusive lock, so the inode never changes under another
process's open descriptor. A writer that finds its file unlinked after
taking the lock (purge or "Delete now" won the race) reopens and retries.

Modes: 0600 files in a 0700 directory. Where two service users share the
store (the ground VM: the SMO containers run as uid 10001, SpaceCDF as
10002 with the smo group added), ``SMO_LOGBOOK_SHARED_GROUP=1`` makes them
0660 in a setgid 02770 directory instead, so both can write and the files
keep the smo group. Either way only the service users can read them, and
the HTTP API only ever returns the caller's own logbook.

Retention: the file's mtime is the person's last write (add, edit, delete).
Records that are not writes (the ``downloaded`` marker) and purge rewrites
restore the previous mtime, so ``expires_at = mtime + retention`` is exact.
"""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

logger = logging.getLogger(__name__)

__all__ = [
    "KINDS", "TOOLS", "LogbookError", "LogbookStore", "default_store_dir",
    "file_name", "iso", "parse_ts",
]

KINDS = ("decision", "thought", "reflection", "observation", "worksheet")
TOOLS = ("mcs", "delayed_tm", "orbit", "radio", "docs", "instructor", "design", "portal")
WRITE_OPS = ("add", "edit", "delete")

DEFAULT_RETENTION_H = 48.0
DEFAULT_MAX_AGE_H = 168.0
MAX_TEXT = 8000
MAX_ENTRIES = 2000
#: Context keys kept verbatim (others are dropped); values are clipped.
CONTEXT_KEYS = ("page", "procedure", "step", "alarm_id", "param", "study_id",
                "position", "scenario", "sim_status", "report", "dump", "station",
                "pass", "doc", "phase", "anomaly", "command", "gonogo", "gate",
                "proposal")
_CTX_VALUE_MAX = 200
#: Rewrite the file as its folded state once it holds this many records
#: more than its live entries (edit churn must not grow it without bound).
COMPACT_SLACK = 2000


class LogbookError(Exception):
    """A request the store refuses; ``status`` is the HTTP status to use."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def iso(dt: datetime | None = None) -> str:
    """``2026-11-02T23:41:07.123Z`` (UTC, milliseconds)."""
    dt = (dt or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def parse_ts(s: Any) -> datetime | None:
    if not isinstance(s, str) or not s:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def file_name(person_id: str) -> str:
    return hashlib.sha256(person_id.encode("utf-8")).hexdigest()[:32] + ".jsonl"


def default_store_dir() -> Path:
    """``$SMO_LOGBOOK_DIR``, else ``workspace/logbook`` under the cwd."""
    env = os.environ.get("SMO_LOGBOOK_DIR", "").strip()
    return Path(env) if env else Path("workspace") / "logbook"


def _env_hours(name: str, default: float) -> float:
    try:
        v = float(os.environ.get(name, "") or default)
        return v if v > 0 else default
    except ValueError:
        return default


@dataclass
class Folded:
    entries: list[dict]            # newest first
    last_write: datetime | None
    last_download: datetime | None
    records: int


class LogbookStore:
    def __init__(self, directory: str | os.PathLike | None = None, *,
                 retention_h: float | None = None, max_age_h: float | None = None,
                 max_text: int = MAX_TEXT, max_entries: int = MAX_ENTRIES):
        self.dir = Path(directory) if directory else default_store_dir()
        self.retention_h = retention_h if retention_h is not None else \
            _env_hours("SMO_LOGBOOK_RETENTION_H", DEFAULT_RETENTION_H)
        self.max_age_h = max_age_h if max_age_h is not None else \
            _env_hours("SMO_LOGBOOK_MAX_AGE_H", DEFAULT_MAX_AGE_H)
        self.max_text = max_text
        self.max_entries = max_entries
        shared = os.environ.get("SMO_LOGBOOK_SHARED_GROUP", "").strip() in ("1", "true", "yes")
        self.dir_mode = 0o2770 if shared else 0o700
        self.file_mode = 0o660 if shared else 0o600

    # ── files ──────────────────────────────────────────────────────────
    def path_for(self, person_id: str) -> Path:
        return self.dir / file_name(person_id)

    def ensure_dir(self) -> None:
        """Create the store directory with its mode (start-up, first write)."""
        self.dir.mkdir(parents=True, exist_ok=True, mode=self.dir_mode & 0o777)
        with contextlib.suppress(OSError):
            if os.stat(self.dir).st_mode & 0o7777 != self.dir_mode:
                os.chmod(self.dir, self.dir_mode)

    _ensure_dir = ensure_dir

    @contextlib.contextmanager
    def _locked(self, path: Path, *, create: bool, exclusive: bool) -> Iterator[Any]:
        """An open, flocked file object (``None`` if absent and not create).
        Retries when the file was unlinked between open and lock."""
        for _ in range(5):
            flags = os.O_RDWR | os.O_APPEND
            if create:
                self._ensure_dir()
                flags |= os.O_CREAT
            try:
                fd = os.open(path, flags, self.file_mode)
            except FileNotFoundError:
                yield None
                return
            f = os.fdopen(fd, "r+", encoding="utf-8", newline="\n")
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
                if os.fstat(f.fileno()).st_nlink == 0:
                    continue            # purged / deleted under us: reopen
                if create:
                    with contextlib.suppress(OSError):
                        if os.fstat(f.fileno()).st_mode & 0o777 != self.file_mode:
                            os.fchmod(f.fileno(), self.file_mode)
                yield f
                return
            finally:
                with contextlib.suppress(OSError, ValueError):
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                f.close()
        raise LogbookError("logbook file is being replaced; try again", 503)

    @staticmethod
    def _read_records(f) -> list[dict]:
        f.seek(0)
        out = []
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue                # a torn line from a crash: skip it
            if isinstance(rec, dict):
                out.append(rec)
        return out

    @staticmethod
    def _append(f, recs: Iterable[dict]) -> None:
        data = "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in recs)
        f.seek(0, os.SEEK_END)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())

    @staticmethod
    def _rewrite(f, recs: Iterable[dict]) -> None:
        """Rewrite in place (same inode), keeping the mtime."""
        st = os.fstat(f.fileno())
        data = "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in recs)
        # O_APPEND would send every write to the end: rewrite through the fd.
        fd = f.fileno()
        os.ftruncate(fd, 0)
        os.write(fd, data.encode("utf-8")) if data else None
        os.fsync(fd)
        os.utime(fd, ns=(st.st_atime_ns, st.st_mtime_ns))

    # ── folding ────────────────────────────────────────────────────────
    @staticmethod
    def fold(records: list[dict]) -> Folded:
        entries: dict[str, dict] = {}
        order: list[str] = []
        last_write = last_dl = None
        for r in records:
            op = r.get("op")
            ts = parse_ts(r.get("ts"))
            if op in WRITE_OPS and ts and (last_write is None or ts > last_write):
                last_write = ts
            if op == "downloaded":
                if ts and (last_dl is None or ts > last_dl):
                    last_dl = ts
                continue
            eid = r.get("id")
            if not isinstance(eid, str):
                continue
            if op == "add":
                if eid in entries:
                    continue
                e = {k: r.get(k) for k in ("id", "ts", "sim_ts", "tool", "kind", "text",
                                            "context", "worksheet", "lang")}
                e["updated_ts"] = r.get("ts")
                e["edited"] = False
                entries[eid] = e
                order.append(eid)
            elif op == "edit" and eid in entries:
                if isinstance(r.get("text"), str):
                    entries[eid]["text"] = r["text"]
                if isinstance(r.get("worksheet"), dict) and entries[eid].get("worksheet"):
                    entries[eid]["worksheet"] = {**entries[eid]["worksheet"], **r["worksheet"]}
                entries[eid]["updated_ts"] = r.get("ts")
                entries[eid]["edited"] = True
            elif op == "delete":
                entries.pop(eid, None)
        live = [entries[i] for i in order if i in entries]
        live.sort(key=lambda e: e.get("ts") or "", reverse=True)
        return Folded(live, last_write, last_dl, len(records))

    def _folded(self, person_id: str) -> Folded:
        with self._locked(self.path_for(person_id), create=False, exclusive=False) as f:
            if f is None:
                return Folded([], None, None, 0)
            return self.fold(self._read_records(f))

    # ── reads ──────────────────────────────────────────────────────────
    def summary(self, person_id: str, *, tool: str | None = None,
                since: str | None = None) -> dict:
        fo = self._folded(person_id)
        entries = fo.entries
        if tool:
            entries = [e for e in entries if e.get("tool") == tool]
        s = parse_ts(since) if since else None
        if s:
            entries = [e for e in entries if (parse_ts(e.get("ts")) or s) > s]
        expires = fo.last_write + timedelta(hours=self.retention_h) if fo.last_write else None
        unsaved = 0
        for e in fo.entries:
            t = parse_ts(e.get("updated_ts")) or parse_ts(e.get("ts"))
            if t and (fo.last_download is None or t > fo.last_download):
                unsaved += 1
        return {
            "retention_h": self.retention_h,
            "max_age_h": self.max_age_h,
            "expires_at": iso(expires) if expires else None,
            "last_write": iso(fo.last_write) if fo.last_write else None,
            "last_download": iso(fo.last_download) if fo.last_download else None,
            "unsaved": unsaved,
            "entries": entries,
            "count": len(fo.entries),
            "max_entries": self.max_entries,
            "max_text": self.max_text,
        }

    def entries(self, person_id: str) -> list[dict]:
        return self._folded(person_id).entries

    # ── writes ─────────────────────────────────────────────────────────
    def _check_text(self, text: Any) -> str:
        if not isinstance(text, str):
            raise LogbookError("text must be a string")
        text = text.replace("\r\n", "\n").strip()
        if not text:
            raise LogbookError("text is empty")
        if len(text) > self.max_text:
            raise LogbookError(
                f"an entry is limited to {self.max_text} characters ({len(text)} given)", 413)
        return text

    @staticmethod
    def _clean_context(ctx: Any) -> dict:
        if not isinstance(ctx, dict):
            return {}
        out = {}
        for k in CONTEXT_KEYS:
            v = ctx.get(k)
            if v is None or v == "":
                continue
            if isinstance(v, bool) or isinstance(v, (int, float)):
                out[k] = v
            else:
                out[k] = str(v)[:_CTX_VALUE_MAX]
        return out

    @staticmethod
    def _clean_worksheet(ws: Any) -> dict | None:
        if not isinstance(ws, dict) or not isinstance(ws.get("id"), str) or not ws["id"]:
            return None
        out = {"id": ws["id"][:64], "q": str(ws.get("q") or "")[:32]}
        for k in ("title", "q_text", "section"):
            if isinstance(ws.get(k), str) and ws[k]:
                out[k] = ws[k][:1000]
        if isinstance(ws.get("checked"), bool):
            out["checked"] = ws["checked"]
        return out

    def add(self, person_id: str, body: dict, *, now: datetime | None = None) -> dict:
        kind = body.get("kind")
        if kind not in KINDS:
            raise LogbookError(f"kind must be one of {', '.join(KINDS)}")
        tool = body.get("tool")
        if tool not in TOOLS:
            raise LogbookError(f"tool must be one of {', '.join(TOOLS)}")
        text = self._check_text(body.get("text"))
        ws = self._clean_worksheet(body.get("worksheet"))
        if kind == "worksheet" and ws is None:
            raise LogbookError("a worksheet answer needs worksheet.id")
        rec = {"v": 1, "id": str(uuid.uuid4()), "op": "add", "ts": iso(now),
               "tool": tool, "kind": kind, "text": text,
               "context": self._clean_context(body.get("context")),
               "lang": "fr" if body.get("lang") == "fr" else "en"}
        if isinstance(body.get("sim_ts"), str) and body["sim_ts"]:
            rec["sim_ts"] = body["sim_ts"][:40]
        if ws:
            rec["worksheet"] = ws
        with self._locked(self.path_for(person_id), create=True, exclusive=True) as f:
            recs = self._read_records(f)
            fo = self.fold(recs)
            if len(fo.entries) >= self.max_entries:
                raise LogbookError(
                    f"Your logbook is full ({self.max_entries} entries). Download it, "
                    "then use Delete now to start a new one.", 413)
            self._append(f, [rec])
            self._maybe_compact(f, recs + [rec])
        return self.fold([rec]).entries[0]

    def edit(self, person_id: str, entry_id: str, body: dict, *,
             now: datetime | None = None) -> dict:
        text = self._check_text(body.get("text"))
        rec = {"v": 1, "id": entry_id, "op": "edit", "ts": iso(now), "text": text}
        if isinstance(body.get("checked"), bool):
            rec["worksheet"] = {"checked": body["checked"]}
        with self._locked(self.path_for(person_id), create=False, exclusive=True) as f:
            if f is None:
                raise LogbookError("no such entry", 404)
            recs = self._read_records(f)
            if not any(e["id"] == entry_id for e in self.fold(recs).entries):
                raise LogbookError("no such entry", 404)
            self._append(f, [rec])
            recs.append(rec)
            self._maybe_compact(f, recs)
            return next(e for e in self.fold(recs).entries if e["id"] == entry_id)

    def delete(self, person_id: str, entry_id: str, *, now: datetime | None = None) -> None:
        with self._locked(self.path_for(person_id), create=False, exclusive=True) as f:
            if f is None:
                raise LogbookError("no such entry", 404)
            recs = self._read_records(f)
            if not any(e["id"] == entry_id for e in self.fold(recs).entries):
                raise LogbookError("no such entry", 404)
            rec = {"v": 1, "id": entry_id, "op": "delete", "ts": iso(now)}
            self._append(f, [rec])

    def mark_downloaded(self, person_id: str, fmt: str, *, now: datetime | None = None) -> None:
        """Record a download without moving the retention clock."""
        with self._locked(self.path_for(person_id), create=False, exclusive=True) as f:
            if f is None:
                return
            st = os.fstat(f.fileno())
            self._append(f, [{"v": 1, "op": "downloaded", "ts": iso(now), "format": fmt}])
            os.utime(f.fileno(), ns=(st.st_atime_ns, st.st_mtime_ns))

    def delete_all(self, person_id: str) -> bool:
        path = self.path_for(person_id)
        with self._locked(path, create=False, exclusive=True) as f:
            if f is None:
                return False
            os.unlink(path)
            return True

    def _maybe_compact(self, f, recs: list[dict]) -> None:
        fo = self.fold(recs)
        if len(recs) - len(fo.entries) < COMPACT_SLACK:
            return
        self._rewrite(f, self._compacted(recs))
        # a compaction follows a write: the mtime must say "now"
        os.utime(f.fileno())

    def _compacted(self, recs: list[dict], keep=lambda e: True) -> list[dict]:
        """The folded state as add records (+ the newest download marker)."""
        fo = self.fold(recs)
        out = []
        for e in sorted(fo.entries, key=lambda e: e.get("ts") or ""):
            if not keep(e):
                continue
            r = {"v": 1, "id": e["id"], "op": "add", "ts": e["ts"], "tool": e.get("tool"),
                 "kind": e.get("kind"), "text": e.get("text"), "context": e.get("context") or {},
                 "lang": e.get("lang") or "en"}
            if e.get("sim_ts"):
                r["sim_ts"] = e["sim_ts"]
            if e.get("worksheet"):
                r["worksheet"] = e["worksheet"]
            out.append(r)
            if e.get("edited"):
                out.append({"v": 1, "id": e["id"], "op": "edit", "ts": e.get("updated_ts"),
                            "text": e.get("text")})
        if fo.last_download:
            out.append({"v": 1, "op": "downloaded", "ts": iso(fo.last_download)})
        return out

    # ── retention ──────────────────────────────────────────────────────
    def purge(self, *, now: datetime | None = None) -> dict:
        """Delete logbooks idle past the retention; drop entries past the
        max age from the rest. Idempotent; safe to run in every process."""
        now = now or datetime.now(timezone.utc)
        stats = {"files_deleted": 0, "entries_dropped": 0, "files_kept": 0}
        if not self.dir.is_dir():
            return stats
        idle = timedelta(hours=self.retention_h).total_seconds()
        cutoff = now - timedelta(hours=self.max_age_h)
        for path in sorted(self.dir.glob("*.jsonl")):
            try:
                with self._locked(path, create=False, exclusive=True) as f:
                    if f is None:
                        continue
                    if now.timestamp() - os.fstat(f.fileno()).st_mtime > idle:
                        os.unlink(path)
                        stats["files_deleted"] += 1
                        continue
                    recs = self._read_records(f)
                    fo = self.fold(recs)
                    old = [e for e in fo.entries
                           if (parse_ts(e.get("ts")) or now) < cutoff]
                    stale_dl = fo.last_download is not None and fo.last_download < cutoff
                    if old or stale_dl:
                        keep_ids = {e["id"] for e in fo.entries} - {e["id"] for e in old}
                        new = self._compacted(recs, keep=lambda e: e["id"] in keep_ids)
                        if stale_dl:
                            new = [r for r in new if r.get("op") != "downloaded"]
                        self._rewrite(f, new)
                        stats["entries_dropped"] += len(old)
                    stats["files_kept"] += 1
            except (OSError, LogbookError) as e:          # one bad file never stops a purge
                logger.warning("logbook purge: %s: %s", path.name, e)
        # stray temp files from anything else are not ours to keep
        return stats

    # ── admin (sizes, counts) ──────────────────────────────────────────
    def stats(self) -> dict:
        files = list(self.dir.glob("*.jsonl")) if self.dir.is_dir() else []
        return {"files": len(files), "bytes": sum(p.stat().st_size for p in files)}
