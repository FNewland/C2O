"""Voice loops end to end against a REAL LiveKit server (opt-in).

Two Chromium browsers with fake microphones open the MCS keyset panel
(/voice, the production routes of smo_mcs/voice.py and the vendored
livekit-client). The Flight Director holds Space (push-to-talk) on the FD
loop; the Power & Thermal console, monitoring the FD loop, must receive
LiveKit's active-speaker signal for her and show "Flight Director · <name>"
on its FD key. It must also never be offered the Instructor/SIM loop.

Runs only with SMO_E2E=1 and LIVEKIT_SERVER_BIN=<a livekit-server binary>
(e.g. v1.13.10 built from source: `go build ./cmd/server` in the module):

    SMO_E2E=1 LIVEKIT_SERVER_BIN=~/bin/livekit-server \\
        python3 -m pytest -q tests/test_mcs/test_voice_livekit_e2e.py
"""
from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

import pytest
from aiohttp import web

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(os.environ.get("SMO_E2E") != "1" or not os.environ.get("LIVEKIT_SERVER_BIN"),
                       reason="set SMO_E2E=1 and LIVEKIT_SERVER_BIN to run against a real LiveKit"),
]

SIM = Path(__file__).resolve().parents[2]
MODERN = SIM / "packages/smo-mcs/src/smo_mcs/static/modern"
KEY, SECRET = "e2ekey", "e2e-secret-with-at-least-thirty-two-chars"


def _port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def livekit():
    port, tcp, udp = _port(), _port(), _port()
    body = (f"port: {port}\nbind_addresses: ['127.0.0.1']\n"
            f"rtc: {{tcp_port: {tcp}, udp_port: {udp}, node_ip: 127.0.0.1, use_external_ip: false}}\n"
            f"keys: {{{KEY}: {SECRET}}}\nlogging: {{level: warn}}\n")
    p = subprocess.Popen([os.environ["LIVEKIT_SERVER_BIN"], "--config-body", body],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}/"
    for _ in range(100):
        try:
            if urllib.request.urlopen(url, timeout=1).read() == b"OK":
                break
        except OSError:
            time.sleep(0.2)
    else:
        p.kill()
        pytest.fail("livekit-server did not start")
    yield f"ws://127.0.0.1:{port}"
    p.terminate()                      # graceful: waits for rooms to drain
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait(timeout=5)


async def _mcs_voice(ws_url: str):
    """The MCS's voice routes and static mounts, as smo_mcs/server.py wires them."""
    import smo_common
    from smo_common.web.http import apply_http_policy
    from smo_mcs.voice import register_voice_routes
    app = web.Application()
    apply_http_policy(app, revalidate_prefixes=("/static/",), max_age_prefixes={"/static/vendor/": 86400})
    register_voice_routes(app, SIM / "configs/eosat1", env={
        "LIVEKIT_URL": ws_url, "LIVEKIT_API_KEY": KEY, "LIVEKIT_API_SECRET": SECRET})
    app.router.add_static("/static/vendor/", SIM / "vendor")
    app.router.add_static("/static/shared/", Path(smo_common.__file__).parent / "ui")
    app.router.add_static("/static/", MODERN.parent)
    runner = web.AppRunner(app)
    await runner.setup()
    port = _port()
    await web.TCPSite(runner, "127.0.0.1", port).start()
    return runner, f"http://127.0.0.1:{port}"


def _speechlike_wav(path: Path, seconds: float = 8.0, rate: int = 48000) -> Path:
    """A fake microphone that sounds like talking: 4-5 "syllables" a second
    of a gliding, harmonic voice-band tone with pauses. Chromium's default
    fake device is a steady periodic beep, which noise suppression may learn
    as noise and remove, so the server's audio-level speaker detection would
    then never fire (seen in about one run in three)."""
    import math
    import struct
    import wave
    frames = bytearray()
    for i in range(int(seconds * rate)):
        t = i / rate
        syl = (t * 4.5) % 1.0
        env = math.sin(math.pi * syl / 0.7) ** 2 if syl < 0.7 else 0.0
        f0 = 140 + 40 * math.sin(2 * math.pi * 0.7 * t) + 30 * syl
        x = sum(math.sin(2 * math.pi * f0 * k * t) / k for k in (1, 2, 3, 4))
        frames += struct.pack("<h", int(12000 * env * x / 2.1))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))
    return path


async def test_fd_talk_is_heard_as_active_speaker_on_a_monitoring_console(livekit, tmp_path):
    pw = pytest.importorskip("playwright.async_api")
    wav = _speechlike_wav(tmp_path / "talk.wav")
    runner, base = await _mcs_voice(livekit)
    try:
        async with pw.async_playwright() as p:
            br = await p.chromium.launch(args=["--use-fake-device-for-media-stream",
                                               "--use-fake-ui-for-media-stream",
                                               f"--use-file-for-fake-audio-capture={wav}"])
            pages = {}
            for who, pos in (("Alice", "flight_director"), ("Bob", "eps_tcs")):
                ctx = await br.new_context(viewport={"width": 460, "height": 820}, permissions=["microphone"])
                pg = await ctx.new_page()
                await pg.goto(f"{base}/voice?position={pos}&lang=en")
                await pg.fill("#name", who)
                await pg.click("#join-btn")
                pages[who] = pg
            alice, bob = pages["Alice"], pages["Bob"]
            # The FD starts in TALK on the FD loop; the talk button enables once
            # the (muted) microphone is published.
            await alice.wait_for_function(
                "document.querySelector('#ptt').getAttribute('aria-disabled') !== 'true'", timeout=30000)
            await bob.wait_for_function("document.querySelector('#conn').textContent.includes('Connected')",
                                        timeout=30000)
            assert await bob.query_selector("#key-instructor_sim") is None
            fd_state = await bob.get_attribute("#key-fd", "data-state")
            assert fd_state == "MON"
            # Talk from the focused window (the panel releases a HELD talk when
            # its window loses focus, so a mic is never left open by accident).
            await alice.bring_to_front()
            await alice.keyboard.down("Space")
            await alice.wait_for_function("/TALKING/.test(document.querySelector('#ptt-l').textContent)",
                                          timeout=5000)
            try:
                await bob.wait_for_function(
                    "document.querySelector('#key-fd').classList.contains('is-heard')", timeout=30000)
            except Exception:
                diag = {"alice_ptt": await alice.text_content("#ptt-l"),
                        "alice_fd": await alice.text_content("#key-fd .tk"),
                        "bob_fd": await bob.text_content("#key-fd .tk"),
                        "bob_conn": await bob.text_content("#conn")}
                pytest.fail(f"the monitoring console never heard the FD talking: {diag}")
            txt = await bob.text_content("#key-fd .tk")
            assert "Flight Director" in txt and "Alice" in txt, txt
            assert "TALKING" in (await alice.text_content("#ptt-l"))
            await alice.screenshot(path=str(tmp_path / "alice.png"))
            await bob.screenshot(path=str(tmp_path / "bob.png"))
            await alice.keyboard.up("Space")
            await asyncio.sleep(0.5)
            assert "TALKING" not in (await alice.text_content("#ptt-l"))
            await br.close()
    finally:
        await runner.cleanup()
