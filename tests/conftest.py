"""Pytest fixtures and configuration for the test suite."""

import pytest


@pytest.fixture
def anyio_backend():
    """Use asyncio as the async backend for anyio."""
    return "asyncio"
