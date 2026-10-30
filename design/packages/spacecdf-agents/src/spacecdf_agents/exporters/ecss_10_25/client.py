"""ECSS-E-TM-10-25 Annex C.2 (REST) client and ``push_study``.

Annex C.2 (as implemented by COMET / CDP4 WebServices) exposes the same
JSON objects as Annex C.3 over HTTP::

    GET  {base}/SiteDirectory?extent=deep
    POST {base}/EngineeringModel/{em_iid}/iteration/{it_iid}
         body = {"_create": [...], "_update": [...], "_delete": [...]}   (multipart or JSON)

``AnnexCClient`` is a thin ``httpx`` wrapper; ``push_study`` posts the
exporter's objects as a single create transaction (SiteDirectory-level
objects first, then the iteration).  Only exercised against a real server
when ``COMET_URL``/``COMET_USER``/``COMET_PASSWORD`` are set (see tests).
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from .exporter import Model1025, build_10_25_model

logger = logging.getLogger(__name__)

__all__ = ["AnnexCClient", "push_study"]


class AnnexCClient:
    def __init__(self, base_url: str, auth: tuple[str, str] | httpx.Auth | None = None,
                 *, timeout: float = 30.0, client: httpx.AsyncClient | None = None):
        self.base_url = base_url.rstrip("/")
        self.auth = auth
        self.timeout = timeout
        self._client = client

    def _c(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, auth=self.auth, timeout=self.timeout)
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def get(self, path: str, **query: Any) -> Any:
        r = await self._c().get("/" + path.lstrip("/"), params=query or None)
        r.raise_for_status()
        return r.json()

    async def post_iteration(self, em_iid: str, iteration_iid: str, *, create: list[dict] | None = None,
                             update: list[dict] | None = None, delete: list[dict] | None = None) -> Any:
        body = {"_create": create or [], "_update": update or [], "_delete": delete or []}
        r = await self._c().post(f"/EngineeringModel/{em_iid}/iteration/{iteration_iid}", json=body)
        r.raise_for_status()
        return r.json() if r.content else None

    async def post_site_directory(self, *, create: list[dict] | None = None,
                                  update: list[dict] | None = None) -> Any:
        body = {"_create": create or [], "_update": update or [], "_delete": []}
        r = await self._c().post("/SiteDirectory", json=body)
        r.raise_for_status()
        return r.json() if r.content else None


async def push_study(study_id: str, client: AnnexCClient, *, model: Model1025 | None = None) -> dict[str, Any]:
    """Push the study as create-transactions. Returns counts + server replies."""
    model = model or await build_10_25_model(study_id)
    dump = lambda xs: [t.model_dump(mode="json") for t in xs]  # noqa: E731
    replies: dict[str, Any] = {}
    replies["site_directory"] = await client.post_site_directory(
        create=dump(model.site_directory) + dump(model.rdl) + dump(model.engineering_model))
    replies["iteration"] = await client.post_iteration(
        model.em_iid, model.iteration_iid, create=dump(model.iteration))
    return {
        "study_id": study_id, "em_iid": model.em_iid, "iteration_iid": model.iteration_iid,
        "created": {"site_directory": len(model.site_directory) + len(model.rdl) + len(model.engineering_model),
                    "iteration": len(model.iteration)},
        "replies": replies, "warnings": model.warnings,
    }
