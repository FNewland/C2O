"""API-test fixtures (SCDF-160): the FastAPI app over the throw-away DB.

Reuses ``db_factory`` / ``study`` from the repository tests, then hands out an
``httpx.AsyncClient`` bound to the app via ``ASGITransport`` (lifespan is not
run — caches start empty and are reset per test). A ``Study`` object is
registered in the in-memory study store under the same id as the ``StudyRow``.
"""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from tests.test_repositories.conftest import db_factory, study  # noqa: F401


@pytest.fixture()
async def client(db_factory):  # noqa: F811
    from spacecdf_server.app import app
    from spacecdf_server.routers import elements, requirements, studies

    elements._elements.clear()
    elements._interfaces.clear()
    requirements._requirements.clear()
    saved_studies = dict(studies.get_study_store())
    studies.get_study_store().clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    elements._elements.clear()
    elements._interfaces.clear()
    requirements._requirements.clear()
    studies.get_study_store().clear()
    studies.get_study_store().update(saved_studies)


@pytest.fixture()
async def study_obj(client, study):  # noqa: F811
    """A ``Study`` pydantic object registered in the study store, id == StudyRow id."""
    from spacecdf_common.models.study import Study
    from spacecdf_server.routers.studies import get_study_store

    s = Study(id=study, name="API test study")
    get_study_store()[study] = s
    return s


async def make_element(client, study_id: str, name: str, element_type: str = "subsystem",
                       parent_id: str | None = None, subsystem_domain: str | None = None) -> dict:
    r = await client.post(f"/api/elements/?study_id={study_id}", json={
        "name": name, "element_type": element_type, "parent_id": parent_id,
        "subsystem_domain": subsystem_domain,
    })
    assert r.status_code == 200, r.text
    return r.json()


async def make_interface(client, study_id: str, from_id: str, to_id: str, name: str = "",
                         interface_type: str = "data") -> dict:
    r = await client.post(f"/api/interfaces/?study_id={study_id}", json={
        "name": name, "interface_type": interface_type,
        "from_element_id": from_id, "to_element_id": to_id,
    })
    assert r.status_code == 200, r.text
    return r.json()


async def make_requirement(client, study_id: str, req_id: str, level: str = "system",
                           parent_id: str | None = None, element_id: str | None = None, **extra) -> dict:
    r = await client.post("/api/requirements/", json={
        "id": req_id, "study_id": study_id, "level": level, "parent_id": parent_id,
        "element_id": element_id, "text": f"Requirement {req_id}", **extra,
    })
    assert r.status_code == 200, r.text
    return r.json()
