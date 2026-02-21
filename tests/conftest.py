"""Shared pytest fixtures for automated-data-cataloger tests."""

import pytest


@pytest.fixture
def sample_fixture() -> dict[str, str]:
    """Example fixture - replace with actual fixtures as needed."""
    return {"example": "data"}
