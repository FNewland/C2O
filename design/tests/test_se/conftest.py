"""Fixtures for the systems-engineering protocol tests (wave 3, agent S): the API client over a
throw-away DB, as for the Northern Fire and Ice seed tests."""
from tests.test_api.conftest import client, study_obj  # noqa: F401
from tests.test_repositories.conftest import db_factory, study  # noqa: F401
