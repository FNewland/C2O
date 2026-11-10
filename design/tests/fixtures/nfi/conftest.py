"""Fixtures for the Northern Fire and Ice seed tests: the API client over a throw-away DB."""
from tests.test_api.conftest import client, study_obj  # noqa: F401
from tests.test_repositories.conftest import db_factory, study  # noqa: F401
