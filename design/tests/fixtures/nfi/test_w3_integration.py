"""Wave 3 integration: the Northern Fire and Ice walkthrough (``walkthrough.py``) makes the SRR and
the PDR pass on the full seed and on the recording seed."""
from __future__ import annotations

import pytest

from tests.fixtures.nfi.walkthrough import _walkthrough


@pytest.mark.asyncio
async def test_walkthrough_srr_and_pdr_pass_on_the_full_seed(client):
    await _walkthrough(client, recording=False)


@pytest.mark.asyncio
async def test_walkthrough_srr_and_pdr_pass_on_the_recording_seed(client):
    await _walkthrough(client, recording=True)
