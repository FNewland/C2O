# EOSAT-1 VR kit — stub server, sample data, starter clients

Everything a VR team needs to start **without** the full simulator. The
protocol is defined in [`docs/VR_INTERFACE_ICD.md`](../../docs/VR_INTERFACE_ICD.md)
(`smo-vr/1`). The real simulator and this stub send identical messages, so code
that works here works on demo day.

| File | What it is |
|---|---|
| `vr_stub.py` | Test server. Python 3.8+, standard library only — copy it anywhere |
| `vr_client_example.py` | Reference client (no graphics); also records real sessions to files |
| `sample_vr_frames.ndjson` | Flat file: one orbit, 5 s steps, exactly as sent on the socket |
| `sample_vr_frames.csv` | The same data as a spreadsheet-friendly CSV |
| `unity/VRLinkClient.cs` | Unity starter script: socket thread, frame conversion, status line |

## Week 1 — read the flat file
Load `sample_vr_frames.csv` (or the `.ndjson`, one JSON object per line; skip
the first `hello` line) and step through the rows. Get the satellite rotating
correctly (`attitude_q_body_to_eci_*`), the Earth in the right place
(`orbit_pos_eci_km_*`), and the Sun lighting it (`sun_dir_eci_*`).
Check yourself: from t = 1200 s the imager face (+Z) must point at Earth.

## Week 2+ — go live against the stub
```bash
python3 vr_stub.py                        # real time, 1 frame/s (like the simulator)
python3 vr_stub.py --speed 10 --rate 10   # faster story, smooth frames
python3 vr_stub.py --story nominal        # skip LEOP: deployed and nadir-pointing
python3 vr_stub.py --replay sample_vr_frames.ndjson --speed 5
python3 vr_stub.py --chaos                # bad lines, stalls, duplicates: be robust!
```
Connect to `<laptop-ip>:8100` (TCP, Unity/native) or `ws://<laptop-ip>:8101/vr`
(WebXR/three.js). The headset and laptop must be on the same network, and the
laptop firewall must allow ports 8100–8101. Find the laptop IP with
`ipconfig` (Windows) or `ipconfig getifaddr en0` (macOS).

Sanity check before blaming your headset:
```bash
python3 vr_client_example.py --host <laptop-ip> --team T07
```

## The optional status line
Send once a second, one line of JSON:
```json
{"type":"status","team":"T07","status_word":15,"state":"OK","seq_ack":123,"fps":72}
```
`status_word` bits: 1 = receiving frames, 2 = last frame parsed, 4 = rendering,
8 = data fresh (< 2 s old). 15 (0x000F) = healthy. The stub prints each team's
state and logs every reply to `vr_logs/vr_replies_<time>.jsonl`; the simulator
shows it as the **VR** badge on the instructor console.

## Recording from the real simulator
```bash
python3 vr_client_example.py --host <sim-ip> --record pass.ndjson --csv pass.csv
python3 vr_stub.py --replay pass.ndjson
```

## Regenerating the sample files
```bash
python3 vr_stub.py --write-sample .            # 5 s steps
python3 vr_stub.py --write-sample . --sample-step 1
```
