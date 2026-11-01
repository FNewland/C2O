#!/usr/bin/env python3
"""vr_client_example.py — a reference smo-vr/1 client with no graphics.

Use it to check the link before blaming your headset, and to record real
simulator sessions to files you can replay with vr_stub.py.

    python3 vr_client_example.py --host 192.168.1.20 --team T07
    python3 vr_client_example.py --host <sim-ip> --record pass.ndjson --csv pass.csv
    python3 vr_client_example.py --frames 10            # stop after 10 frames

It does what every headset client should do (docs/VR_INTERFACE_ICD.md §8):

* reads one JSON object per line from TCP port 8100;
* refuses to run if the schema's major version is not smo-vr/1;
* skips lines that do not parse and message types it does not know;
* treats seq gaps and repeats as normal;
* reconnects every 2 s when the connection drops;
* sends the optional status line once a second.

Python 3.8 or newer, standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
import socket
import sys
import time

SCHEMA_MAJOR = "smo-vr/1"
RX_OK, PARSE_OK, RENDERING, DATA_FRESH = 0x1, 0x2, 0x4, 0x8


def flatten(frame, prefix=""):
    """Flatten a frame for CSV, the same way as sample_vr_frames.csv."""
    out = {}
    for key, value in frame.items():
        if not prefix and key in ("type", "schema"):
            continue
        name = prefix + key
        if isinstance(value, dict):
            out.update(flatten(value, name + "_"))
        elif isinstance(value, list):
            for axis, x in zip("xyzw", value):
                out[f"{name}_{axis}"] = x
        elif isinstance(value, bool):
            out[name] = int(value)
        else:
            out[name] = value
    return out


def describe(f):
    """One readable line per frame."""
    o, a, d, m = f["orbit"], f["attitude"], f["deploy"], f["mission"]
    return (f"seq {f['seq']:>6}  {f['sim_time']}  lat {o['lat_deg']:7.2f} "
            f"lon {o['lon_deg']:8.2f}  {a['aocs_mode']:<9} {a['pointing']:<12} "
            f"wings {d['wing_py']['state'][:4]}/{d['wing_my']['state'][:4]}  "
            f"ant {d['antenna']['state'][:4]}  "
            f"{'ECLIPSE' if f['sun']['in_eclipse'] else 'sun    '}  "
            f"{m['ground_station'] or '-'}")


def run(args):
    record = open(args.record, "w", encoding="utf-8") if args.record else None
    csv_file = open(args.csv, "w", encoding="utf-8", newline="") if args.csv else None
    csv_writer = None
    frames = 0
    while True:
        try:
            sock = socket.create_connection((args.host, args.port), timeout=5)
        except OSError as e:
            print(f"cannot connect to {args.host}:{args.port} ({e}); retrying in 2 s")
            time.sleep(2)
            continue
        print(f"connected to {args.host}:{args.port}")
        sock.settimeout(0.2)
        buf = b""
        last_seq, last_rx, parsed_ok, next_status = None, 0.0, False, 0.0
        try:
            while True:
                try:
                    chunk = sock.recv(65536)
                    if not chunk:
                        raise ConnectionError("server closed the connection")
                    buf += chunk
                except socket.timeout:
                    pass
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    try:
                        msg = json.loads(line)
                        if not isinstance(msg, dict):
                            raise ValueError("not an object")
                    except ValueError:
                        parsed_ok = False
                        print("  (skipped a line that does not parse)")
                        continue
                    parsed_ok = True
                    if record:
                        record.write(line.decode("utf-8") + "\n")
                        record.flush()
                    kind = msg.get("type")
                    if kind == "hello":
                        if msg.get("schema") != SCHEMA_MAJOR:
                            sys.exit(f"server speaks {msg.get('schema')!r}, "
                                     f"this client needs {SCHEMA_MAJOR}")
                        print(f"hello from {msg.get('source')} "
                              f"(max {msg.get('max_rate_hz')} frames/s)")
                    elif kind == "state":
                        if last_seq is not None and msg["seq"] != last_seq + 1:
                            print(f"  (seq {last_seq} -> {msg['seq']}: "
                                  f"{'repeat' if msg['seq'] <= last_seq else 'gap'})")
                        last_seq, last_rx = msg["seq"], time.monotonic()
                        print(describe(msg))
                        if csv_file:
                            row = flatten(msg)
                            if csv_writer is None:
                                csv_writer = csv.DictWriter(
                                    csv_file, fieldnames=list(row),
                                    extrasaction="ignore")
                                csv_writer.writeheader()
                            csv_writer.writerow(row)
                            csv_file.flush()
                        frames += 1
                        if args.frames and frames >= args.frames:
                            return 0
                    # any other type: ignore it (ICD §8 rule 1)
                now = time.monotonic()
                if args.team and now >= next_status:
                    next_status = now + 1.0
                    word = RENDERING
                    if last_seq is not None:
                        word |= RX_OK
                    if parsed_ok:
                        word |= PARSE_OK
                    if last_rx and now - last_rx < 2.0:
                        word |= DATA_FRESH
                    status = {"type": "status", "team": args.team,
                              "status_word": word,
                              "state": "OK" if word == 0xF else "WARN",
                              "seq_ack": last_seq, "text": "vr_client_example"}
                    if last_seq is None:
                        del status["seq_ack"]
                    sock.sendall((json.dumps(status) + "\n").encode("utf-8"))
        except (ConnectionError, OSError) as e:
            print(f"connection lost ({e}); reconnecting in 2 s")
            sock.close()
            time.sleep(2)


def main(argv=None):
    p = argparse.ArgumentParser(description="smo-vr/1 reference client")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8100)
    p.add_argument("--team", default="T00",
                   help="team name for the status line; '' sends none")
    p.add_argument("--record", metavar="FILE.ndjson",
                   help="save every message exactly as received")
    p.add_argument("--csv", metavar="FILE.csv", help="save frames as CSV")
    p.add_argument("--frames", type=int, default=0,
                   help="stop after this many frames (default: run forever)")
    args = p.parse_args(argv)
    try:
        return run(args)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
