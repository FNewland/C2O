"""Logbook store: one append-only JSONL file per person (LOGBOOK_SPEC.md §2).

Framework-free on purpose: the ops tools (aiohttp, sim/) read and write the
same files with their own implementation, and on the server every ground
container and ``spacecdf`` mount the same volume, so one person's logbook
spans every tool. Keep this module byte-compatible with the spec:

- directory ``$SMO_LOGBOOK_DIR`` (default ``/opt/smo/workspace/logbook`` in
  containers), mode 0700; file ``sha256(person_id)[:32].jsonl``, mode 0600.
  With ``SMO_LOGBOOK_SHARED_GROUP=1`` (ground VM: the SMO containers run as
  uid 10001, SpaceCDF as 10002 with the smo group added) 0660 files in a
  setgid 02770 directory, as smo-common does;
- one JSON object per line; edits and deletes are new records with ``op``;
- writers hold an exclusive ``fcntl.flock`` while appending, readers a
  shared one, and fold the records (last edit wins, deletes drop);
- purge: the whole file goes when its mtime is older than the retention
  (48 h); a kept file is rewritten without entries older than the max age
  (7 days). Purge is idempotent and safe to run from several processes.

Edit churn is bounded the same way as smo-common: once a file holds
``COMPACT_SLACK`` more records than live entries it is rewritten in place as
its folded state (an add per entry, an edit where it was edited, the newest
download marker).

The file's mtime is the time of the person's last *write*. Recording a
download marker or rewriting the file during purge restores the previous
mtime, so neither extends the retention.
"""
from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import logging
import os
import re
import secrets
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1
KINDS = ("decision", "thought", "reflection", "observation", "worksheet")
TOOLS = ("mcs", "delayed_tm", "orbit", "radio", "docs", "instructor", "design", "portal")
LANGS = ("en", "fr")

TEXT_LIMIT = 8_000          # characters per entry
ENTRY_LIMIT = 2_000         # live entries per person
COMPACT_SLACK = 2_000       # records beyond the live entries before a compaction
CONTEXT_LIMIT = 4_096       # bytes of JSON for the context object
CONTEXT_VALUE_MAX = 200     # characters per context string (as smo-common)

CONTAINER_DIR = Path("/opt/smo/workspace/logbook")


class LogbookError(Exception):
    """A request the store refuses. ``status`` is the HTTP status to answer."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


# ─── Configuration ────────────────────────────────────────────────────────

def _env_float(name: str, default: float) -> float:
    try:
        v = float(os.environ.get(name, ""))
        return v if v > 0 else default
    except ValueError:
        return default


def retention_hours() -> float:
    return _env_float("SMO_LOGBOOK_RETENTION_H", 48.0)


def max_age_hours() -> float:
    return _env_float("SMO_LOGBOOK_MAX_AGE_H", 168.0)


def shared_group() -> bool:
    return os.environ.get("SMO_LOGBOOK_SHARED_GROUP", "").strip().lower() in ("1", "true", "yes")


def modes() -> tuple[int, int]:
    """(directory mode, file mode)."""
    return (0o2770, 0o660) if shared_group() else (0o700, 0o600)


def default_dir() -> Path:
    """``$SMO_LOGBOOK_DIR``, else the container workspace, else a dev default.

    Dev default: the ops tools' local logbook ``<repo>/sim/workspace/logbook``
    when it already exists (a laptop running both then shares one logbook);
    otherwise ``~/.local/share/c2o/logbook``. SpaceCDF never creates a
    logbook directory inside the repository by itself (the repo is public).
    """
    env = os.environ.get("SMO_LOGBOOK_DIR")
    if env:
        return Path(env)
    if CONTAINER_DIR.parent.is_dir():
        return CONTAINER_DIR
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "design").is_dir() and (parent / "sim").is_dir():
            ops = parent / "sim" / "workspace" / "logbook"
            if ops.is_dir():
                return ops
            break
    return Path.home() / ".local" / "share" / "c2o" / "logbook"


# ─── Time helpers ─────────────────────────────────────────────────────────

def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    """``2026-11-02T23:41:07.123Z`` (UTC, milliseconds), the record format."""
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# ─── Identity ─────────────────────────────────────────────────────────────

IAP_HEADER = "x-goog-authenticated-user-email"
COOKIE_NAME = "c2o_lb"
COOKIE_MAX_AGE = 30 * 24 * 3600
_COOKIE_RE = re.compile(r"^(?:local:)?([0-9a-f]{32})$")


def person_from_iap(raw: str | None) -> str | None:
    """IAP header value → person id (``accounts.google.com:`` stripped, lower-cased)."""
    if not raw:
        return None
    value = raw.strip()
    if value.lower().startswith("accounts.google.com:"):
        value = value.split(":", 1)[1]
    value = value.strip().lower()
    return value or None


def person_from_cookie(raw: str | None) -> str | None:
    """``c2o_lb`` cookie value → ``local:<hex>`` (``local:`` prefix optional on read)."""
    if not raw:
        return None
    m = _COOKIE_RE.match(raw.strip().strip('"').lower())
    return f"local:{m.group(1)}" if m else None


def new_local_id() -> str:
    """A fresh random 128-bit local id, ``local:<32 hex>``."""
    return f"local:{secrets.token_hex(16)}"


def file_name(person_id: str) -> str:
    return hashlib.sha256(person_id.encode("utf-8")).hexdigest()[:32] + ".jsonl"


# ─── Folding ──────────────────────────────────────────────────────────────

@dataclass
class Folded:
    entries: dict[str, dict] = field(default_factory=dict)   # id → entry, insertion order
    last_write: datetime | None = None
    last_download: datetime | None = None
    last_download_format: str | None = None

    def newest_first(self) -> list[dict]:
        epoch = datetime.min.replace(tzinfo=timezone.utc)
        return sorted(self.entries.values(), key=lambda e: parse_ts(e["ts"]) or epoch, reverse=True)

    @property
    def unsaved(self) -> int:
        """Entries added or edited since the last download (all of them if never)."""
        if self.last_download is None:
            return len(self.entries)
        # >= matches the ops store: a write in the same millisecond as the
        # download still counts as unsaved (conservative).
        return sum(1 for e in self.entries.values()
                   if (t := parse_ts(e.get("updated_ts"))) is not None and t >= self.last_download)


def _later(a: datetime | None, b: datetime | None) -> datetime | None:
    if a is None:
        return b
    if b is None:
        return a
    return max(a, b)


def fold(records: list[dict]) -> Folded:
    """Fold raw records into live entries (last edit wins, deletes drop)."""
    out = Folded()
    gone: set[str] = set()
    for r in records:
        if not isinstance(r, dict):
            continue
        op = r.get("op")
        ts = parse_ts(r.get("ts"))
        rid = r.get("id")
        if op == "add":
            if not isinstance(rid, str) or not rid or rid in out.entries or rid in gone:
                continue
            out.entries[rid] = {
                "id": rid,
                "ts": r.get("ts"),
                "updated_ts": r.get("ts"),
                "edited": False,
                "tool": r.get("tool"),
                "kind": r.get("kind"),
                "text": r.get("text") if isinstance(r.get("text"), str) else "",
                "context": r.get("context") if isinstance(r.get("context"), dict) else {},
                "worksheet": r.get("worksheet") if isinstance(r.get("worksheet"), dict) else None,
                "sim_ts": r.get("sim_ts"),
                "lang": r.get("lang"),
            }
            out.last_write = _later(out.last_write, ts)
        elif op == "edit":
            e = out.entries.get(rid) if isinstance(rid, str) else None
            if e is None or not isinstance(r.get("text"), str):
                continue
            e["text"] = r["text"]
            if isinstance(r.get("worksheet"), dict) and e.get("worksheet"):
                e["worksheet"] = {**e["worksheet"], **r["worksheet"]}   # e.g. {"checked": true}
            e["updated_ts"] = r.get("ts")
            e["edited"] = True
            out.last_write = _later(out.last_write, ts)
        elif op == "delete":
            if isinstance(rid, str) and out.entries.pop(rid, None) is not None:
                gone.add(rid)
                out.last_write = _later(out.last_write, ts)
        elif op == "downloaded":
            if ts and (out.last_download is None or ts >= out.last_download):
                out.last_download = ts
                out.last_download_format = r.get("format")
    return out


def compacted(records: list[dict], keep=lambda e: True) -> list[dict]:
    """The folded state as records: an add per live entry (an edit after it
    when it was edited) and the newest download marker. Same shape as
    smo-common's compaction."""
    f = fold(records)
    epoch = datetime.min.replace(tzinfo=timezone.utc)
    out: list[dict] = []
    for e in sorted(f.entries.values(), key=lambda e: parse_ts(e.get("ts")) or epoch):
        if not keep(e):
            continue
        r = {"v": SCHEMA_VERSION, "id": e["id"], "op": "add", "ts": e["ts"], "tool": e.get("tool"),
             "kind": e.get("kind"), "text": e.get("text"), "context": e.get("context") or {},
             "lang": e.get("lang") or "en"}
        if e.get("sim_ts"):
            r["sim_ts"] = e["sim_ts"]
        if e.get("worksheet"):
            r["worksheet"] = e["worksheet"]
        out.append(r)
        if e.get("edited"):
            out.append({"v": SCHEMA_VERSION, "id": e["id"], "op": "edit", "ts": e.get("updated_ts"),
                        "text": e.get("text")})
    if f.last_download:
        rec = {"v": SCHEMA_VERSION, "op": "downloaded", "ts": iso(f.last_download)}
        if f.last_download_format:
            rec["format"] = f.last_download_format
        out.append(rec)
    return out


# ─── Validation ───────────────────────────────────────────────────────────

def _clean_context(ctx: Any) -> dict:
    if ctx is None:
        return {}
    if not isinstance(ctx, dict):
        raise LogbookError(400, "context must be an object")
    clean: dict[str, Any] = {}
    for k, v in ctx.items():
        if not isinstance(k, str) or len(k) > 64:
            raise LogbookError(400, "context keys must be short strings")
        if isinstance(v, str):
            clean[k] = v[:CONTEXT_VALUE_MAX]
        elif v is None or isinstance(v, (int, float, bool)):
            clean[k] = v
        else:
            raise LogbookError(400, f"context.{k} must be a string, number, boolean or null")
    if len(json.dumps(clean, ensure_ascii=False).encode("utf-8")) > CONTEXT_LIMIT:
        raise LogbookError(413, "context is too large")
    return clean


def _clean_worksheet(ws: Any) -> dict | None:
    if ws is None:
        return None
    if not isinstance(ws, dict) or not isinstance(ws.get("id"), str) or not isinstance(ws.get("q"), str):
        raise LogbookError(400, "worksheet must be {id, q}")
    clean = {"id": ws["id"][:64], "q": ws["q"][:64]}
    # Optional, same names as smo-common: the worksheet title and question
    # text as the participant saw them (q_text), so any tool's export prints
    # the question without that workbook's YAML; section; a checkbox state.
    if "q_text" not in ws and isinstance(ws.get("question"), str):
        ws = {**ws, "q_text": ws["question"]}
    for k in ("title", "q_text", "section"):
        if isinstance(ws.get(k), str) and ws[k].strip():
            clean[k] = ws[k][:1_000]
    if isinstance(ws.get("checked"), bool):
        clean["checked"] = ws["checked"]
    return clean


def _check_text(text: Any) -> str:
    if not isinstance(text, str):
        raise LogbookError(400, "text must be a string")
    text = text.replace("\r\n", "\n").strip()
    if not text:
        raise LogbookError(400, "text is empty")
    if len(text) > TEXT_LIMIT:
        raise LogbookError(413, f"An entry holds at most {TEXT_LIMIT} characters.")
    return text


def validate_new(payload: Any) -> dict:
    """Body of POST /api/logbook/entries → the fields of an ``add`` record."""
    if not isinstance(payload, dict):
        raise LogbookError(400, "body must be a JSON object")
    kind = payload.get("kind")
    if kind not in KINDS:
        raise LogbookError(400, f"kind must be one of {', '.join(KINDS)}")
    tool = payload.get("tool")
    if tool not in TOOLS:
        raise LogbookError(400, f"tool must be one of {', '.join(TOOLS)}")
    text = _check_text(payload.get("text"))
    worksheet = _clean_worksheet(payload.get("worksheet"))
    if kind == "worksheet" and worksheet is None:
        raise LogbookError(400, "a worksheet answer needs worksheet {id, q}")
    lang = payload.get("lang") or "en"
    if lang not in LANGS:
        raise LogbookError(400, "lang must be en or fr")
    sim_ts = payload.get("sim_ts")
    if sim_ts is not None and (not isinstance(sim_ts, str) or parse_ts(sim_ts) is None):
        raise LogbookError(400, "sim_ts must be an ISO 8601 time")
    return {
        "tool": tool, "kind": kind, "text": text,
        "context": _clean_context(payload.get("context")),
        "worksheet": worksheet, "sim_ts": sim_ts, "lang": lang,
    }


# ─── The store ────────────────────────────────────────────────────────────

def _dumps(rec: dict) -> bytes:
    return (json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def _parse_lines(data: bytes) -> list[dict]:
    out = []
    for line in data.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            logger.warning("logbook: skipping a malformed line")
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def _read_fd(fd: int) -> bytes:
    os.lseek(fd, 0, os.SEEK_SET)
    chunks = []
    while True:
        b = os.read(fd, 1 << 16)
        if not b:
            break
        chunks.append(b)
    return b"".join(chunks)


class LogbookStore:
    def __init__(self, root: Path | str | None = None,
                 retention_h: float | None = None, max_age_h: float | None = None):
        self._root = Path(root) if root is not None else None
        self._retention_h = retention_h
        self._max_age_h = max_age_h

    # Configuration is read per call so tests and operators can change the
    # environment without rebuilding the store.
    @property
    def root(self) -> Path:
        return self._root if self._root is not None else default_dir()

    @property
    def retention_h(self) -> float:
        return self._retention_h if self._retention_h is not None else retention_hours()

    @property
    def max_age_h(self) -> float:
        return self._max_age_h if self._max_age_h is not None else max_age_hours()

    def path_for(self, person_id: str) -> Path:
        return self.root / file_name(person_id)

    def _ensure_dir(self) -> None:
        root = self.root
        dmode, _ = modes()
        root.mkdir(parents=True, exist_ok=True, mode=dmode & 0o777)
        try:
            if os.stat(root).st_mode & 0o7777 != dmode:
                os.chmod(root, dmode)
        except OSError:
            pass

    @contextmanager
    def _locked(self, path: Path, exclusive: bool, create: bool) -> Iterator[int | None]:
        """Open ``path`` and flock it. Yields the fd, or None when absent and not creating.

        A purge or "Delete now" may unlink the file while we wait for the
        lock; after locking we check the fd still names the path and retry.
        """
        for _ in range(5):
            flags = os.O_RDWR | os.O_APPEND
            if create:
                self._ensure_dir()
                flags |= os.O_CREAT
            try:
                fd = os.open(path, flags, modes()[1])
            except FileNotFoundError:
                if create:
                    raise
                yield None
                return
            try:
                fcntl.flock(fd, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
                try:
                    st = os.fstat(fd)
                    cur = os.stat(path)
                    same = st.st_nlink > 0 and (st.st_ino, st.st_dev) == (cur.st_ino, cur.st_dev)
                except FileNotFoundError:
                    same = False
                if not same:
                    continue          # unlinked under us: reopen
                if create and st.st_mode & 0o777 != modes()[1]:
                    try:
                        os.fchmod(fd, modes()[1])    # the umask may have stripped group bits
                    except OSError:
                        pass
                yield fd
                return
            finally:
                try:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                finally:
                    os.close(fd)
        raise LogbookError(503, "logbook file is busy; try again")

    def _write(self, fd: int, records: list[dict]) -> None:
        data = b"".join(_dumps(r) for r in records)
        view = memoryview(data)
        while view:
            n = os.write(fd, view)
            view = view[n:]
        os.fsync(fd)

    # ── reads ──

    def read_records(self, person_id: str) -> list[dict]:
        with self._locked(self.path_for(person_id), exclusive=False, create=False) as fd:
            if fd is None:
                return []
            return _parse_lines(_read_fd(fd))

    def folded(self, person_id: str) -> Folded:
        return fold(self.read_records(person_id))

    def expires_at(self, folded: Folded) -> datetime | None:
        if folded.last_write is None:
            return None
        return folded.last_write + timedelta(hours=self.retention_h)

    # ── writes ──

    def add(self, person_id: str, payload: Any, *, now: datetime | None = None) -> dict:
        fields = validate_new(payload)
        ts = iso(now or now_utc())
        rec = {"v": SCHEMA_VERSION, "id": str(uuid.uuid4()), "op": "add", "ts": ts}
        if fields["sim_ts"]:
            rec["sim_ts"] = fields["sim_ts"]
        rec.update({"tool": fields["tool"], "kind": fields["kind"], "text": fields["text"],
                    "context": fields["context"]})
        if fields["worksheet"]:
            rec["worksheet"] = fields["worksheet"]
        rec["lang"] = fields["lang"]
        with self._locked(self.path_for(person_id), exclusive=True, create=True) as fd:
            records = _parse_lines(_read_fd(fd))
            if len(fold(records).entries) >= ENTRY_LIMIT:
                raise LogbookError(413, (
                    f"Your logbook is full ({ENTRY_LIMIT} entries). Download it, "
                    "then use Delete now to start a fresh one."))
            self._write(fd, [rec])
            self._maybe_compact(fd, records + [rec])
        return fold([rec]).entries[rec["id"]]

    def edit(self, person_id: str, entry_id: str, text: Any, *, checked: bool | None = None,
             now: datetime | None = None) -> dict:
        text = _check_text(text)
        rec = {"v": SCHEMA_VERSION, "id": entry_id, "op": "edit", "ts": iso(now or now_utc()), "text": text}
        if isinstance(checked, bool):
            rec["worksheet"] = {"checked": checked}
        with self._locked(self.path_for(person_id), exclusive=True, create=False) as fd:
            if fd is None:
                raise LogbookError(404, "no such entry")
            records = _parse_lines(_read_fd(fd))
            if entry_id not in fold(records).entries:
                raise LogbookError(404, "no such entry")
            self._write(fd, [rec])
            self._maybe_compact(fd, records + [rec])
            return fold(records + [rec]).entries[entry_id]

    def delete(self, person_id: str, entry_id: str, *, now: datetime | None = None) -> None:
        rec = {"v": SCHEMA_VERSION, "id": entry_id, "op": "delete", "ts": iso(now or now_utc())}
        with self._locked(self.path_for(person_id), exclusive=True, create=False) as fd:
            if fd is None or entry_id not in fold(_parse_lines(_read_fd(fd))).entries:
                raise LogbookError(404, "no such entry")
            self._write(fd, [rec])

    def mark_downloaded(self, person_id: str, fmt: str, *, now: datetime | None = None) -> None:
        """Append a ``downloaded`` marker without moving the retention clock."""
        rec = {"v": SCHEMA_VERSION, "op": "downloaded", "ts": iso(now or now_utc()), "format": fmt}
        path = self.path_for(person_id)
        with self._locked(path, exclusive=True, create=False) as fd:
            if fd is None:
                return                      # nothing to download from: no file
            st = os.fstat(fd)
            self._write(fd, [rec])
            os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns))

    def delete_all(self, person_id: str) -> bool:
        path = self.path_for(person_id)
        with self._locked(path, exclusive=True, create=False) as fd:
            if fd is None:
                return False
            os.unlink(path)
            return True

    def _rewrite(self, fd: int, records: list[dict]) -> None:
        """Rewrite in place (same inode, so other processes' fds stay valid)."""
        os.ftruncate(fd, 0)
        self._write(fd, records)

    def _maybe_compact(self, fd: int, records: list[dict]) -> None:
        if len(records) - len(fold(records).entries) < COMPACT_SLACK:
            return
        self._rewrite(fd, compacted(records))
        os.utime(fd)          # follows a write: the mtime says "now"

    # ── purge ──

    def purge(self, *, now: datetime | None = None) -> dict:
        """Apply retention and the max-age cap to every file. Idempotent."""
        now = now or now_utc()
        stats = {"deleted": 0, "trimmed": 0, "kept": 0}
        root = self.root
        if not root.is_dir():
            return stats
        retention = timedelta(hours=self.retention_h)
        cutoff = now - timedelta(hours=self.max_age_h)
        for path in sorted(root.glob("*.jsonl")):
            try:
                outcome = self._purge_one(path, now, retention, cutoff)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    logger.warning("logbook purge: %s: %s", path.name, e)
                continue
            stats[outcome] += 1
        return stats

    def _purge_one(self, path: Path, now: datetime, retention: timedelta, cutoff: datetime) -> str:
        with self._locked(path, exclusive=True, create=False) as fd:
            if fd is None:
                return "deleted"
            st = os.fstat(fd)
            mtime = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
            if now - mtime > retention:
                os.unlink(path)
                return "deleted"
            records = _parse_lines(_read_fd(fd))
            old = {r.get("id") for r in records
                   if r.get("op") == "add" and (parse_ts(r.get("ts")) or now) < cutoff}
            live_adds = {r.get("id") for r in records if r.get("op") == "add"} - old
            kept = []
            for r in records:
                op = r.get("op")
                if op == "downloaded":
                    if (parse_ts(r.get("ts")) or now) >= cutoff:
                        kept.append(r)
                elif op in ("add", "edit", "delete"):
                    if r.get("id") in live_adds:
                        kept.append(r)
                # unknown ops and orphans are dropped
            if not live_adds:
                os.unlink(path)
                return "deleted"
            if len(kept) == len(records):
                return "kept"
            os.ftruncate(fd, 0)
            self._write(fd, kept)
            os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns))
            return "trimmed"
