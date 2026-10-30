"""Agent-side TM log: bounded send queue + replay buffer (LINK_DESIGN §3.8).

Every coalesced TM frame gets a link seq and is appended here. Entries before
``send_seq`` have been handed to the link writer (the *replay* region); the
rest are waiting to be sent (the *queue* region).

* Replay region: kept for ``max_age_s`` seconds **or** the newest
  ``max_bytes`` bytes, whichever holds more (plus a hard byte ceiling).
* Queue region: bounded by ``queue_max_packets`` / ``queue_max_bytes``. On
  overflow the oldest frames are dropped and the next frame sent carries GAP.
  The sim TM socket is never blocked.
"""
from __future__ import annotations

import time
from collections import deque
from typing import NamedTuple

from .protocol import GAP, seq_add, seq_diff


class Entry(NamedTuple):
    seq: int
    payload: bytes
    flags: int
    packets: int
    t: float


class ReplayBuffer:
    def __init__(self, max_age_s: float = 10.0, max_bytes: int = 2 * 1024 * 1024,
                 queue_max_packets: int = 20_000, queue_max_bytes: int = 8 * 1024 * 1024,
                 hard_max_bytes: int = 64 * 1024 * 1024, first_seq: int = 0):
        self.max_age_s = max_age_s
        self.max_bytes = max_bytes
        self.queue_max_packets = queue_max_packets
        self.queue_max_bytes = queue_max_bytes
        self.hard_max_bytes = hard_max_bytes
        self._entries: deque[Entry] = deque()
        self.next_seq = first_seq      # seq the next appended frame gets
        self.send_seq = first_seq      # seq of the next frame to send
        self._sent_bytes = 0
        self._unsent_bytes = 0
        self._unsent_packets = 0
        self._gap_pending = False
        self.dropped_frames = 0
        self.dropped_packets = 0

    # -- regions ------------------------------------------------------------
    def _is_sent(self, e: Entry) -> bool:
        return seq_diff(e.seq, self.send_seq) < 0

    @property
    def oldest_seq(self) -> int | None:
        return self._entries[0].seq if self._entries else None

    @property
    def unsent_frames(self) -> int:
        return max(0, seq_diff(self.next_seq, self.send_seq)) if self._entries else 0

    @property
    def unsent_bytes(self) -> int:
        return self._unsent_bytes

    @property
    def unsent_packets(self) -> int:
        return self._unsent_packets

    @property
    def replay_bytes(self) -> int:
        return self._sent_bytes

    def __len__(self) -> int:
        return len(self._entries)

    def has_unsent(self) -> bool:
        return bool(self._entries) and seq_diff(self.next_seq, self.send_seq) > 0

    # -- producer -----------------------------------------------------------
    def append(self, payload: bytes, packets: int = 1, flags: int = 0,
               now: float | None = None) -> int:
        now = time.monotonic() if now is None else now
        seq = self.next_seq
        self._entries.append(Entry(seq, payload, flags, packets, now))
        self.next_seq = seq_add(seq, 1)
        self._unsent_bytes += len(payload)
        self._unsent_packets += packets
        self._trim(now)
        return seq

    # -- consumer -----------------------------------------------------------
    def pop_unsent(self, now: float | None = None) -> Entry | None:
        """Next frame to send (with GAP set if frames were dropped before it)."""
        if not self.has_unsent():
            return None
        idx = seq_diff(self.send_seq, self._entries[0].seq)
        e = self._entries[idx]
        self.send_seq = seq_add(e.seq, 1)
        self._unsent_bytes -= len(e.payload)
        self._unsent_packets -= e.packets
        self._sent_bytes += len(e.payload)
        if self._gap_pending:
            self._gap_pending = False
            e = e._replace(flags=e.flags | GAP)
        self._trim(time.monotonic() if now is None else now)
        return e

    def rewind(self, seq: int) -> bool:
        """Resend from ``seq`` (complete mode). Returns True if ``seq`` is still
        buffered; otherwise resends from the oldest frame with GAP."""
        if not self._entries:
            if seq_diff(seq, self.next_seq) != 0:
                self._gap_pending = True
            return seq_diff(seq, self.next_seq) == 0
        oldest = self._entries[0].seq
        if seq_diff(seq, oldest) >= 0 and seq_diff(seq, self.next_seq) <= 0:
            self._set_send_seq(seq)
            return True
        self._set_send_seq(oldest)
        self._gap_pending = True
        return False

    def skip_to_new(self) -> int:
        """Timely mode: drop everything not yet sent. Returns frames skipped."""
        skipped = self.unsent_frames
        if skipped:
            self.dropped_frames += skipped
            self.dropped_packets += self._unsent_packets
            self._gap_pending = True
        self._set_send_seq(self.next_seq)
        return skipped

    def _set_send_seq(self, seq: int) -> None:
        self.send_seq = seq
        self._sent_bytes = self._unsent_bytes = self._unsent_packets = 0
        for e in self._entries:
            if self._is_sent(e):
                self._sent_bytes += len(e.payload)
            else:
                self._unsent_bytes += len(e.payload)
                self._unsent_packets += e.packets

    # -- bounds -------------------------------------------------------------
    def _trim(self, now: float) -> None:
        # Queue region over its bound: discard the replay region first, then
        # the oldest unsent frames (GAP on the next one sent).
        while self._entries and (self._unsent_packets > self.queue_max_packets
                                 or self._unsent_bytes > self.queue_max_bytes):
            e = self._entries.popleft()
            if self._is_sent(e):
                self._sent_bytes -= len(e.payload)
                continue
            self._unsent_bytes -= len(e.payload)
            self._unsent_packets -= e.packets
            self.send_seq = seq_add(e.seq, 1)
            self.dropped_frames += 1
            self.dropped_packets += e.packets
            self._gap_pending = True
        # Replay region: evict only when older than max_age AND beyond the
        # newest max_bytes (whichever holds more), or above the hard ceiling.
        while self._entries and self._is_sent(self._entries[0]):
            e = self._entries[0]
            too_old = (now - e.t) > self.max_age_s
            too_big = self._sent_bytes > self.max_bytes
            over_hard = (self._sent_bytes + self._unsent_bytes) > self.hard_max_bytes
            if not ((too_old and too_big) or over_hard):
                break
            self._entries.popleft()
            self._sent_bytes -= len(e.payload)

    def expire(self, now: float | None = None) -> None:
        self._trim(time.monotonic() if now is None else now)
