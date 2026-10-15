"""Ordinary tests must never make real SEC or model requests."""

import pytest
import requests


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Network calls are disabled in tests; use an explicit test double.")

    monkeypatch.setattr(requests.Session, "request", blocked)
