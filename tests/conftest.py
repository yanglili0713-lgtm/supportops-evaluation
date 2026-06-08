from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _force_offline_embeddings(monkeypatch: pytest.MonkeyPatch):
    if os.getenv("RUN_REAL_DENSE_TESTS") == "1":
        yield
        return

    monkeypatch.setenv("SUPPORTOPS_FORCE_FALLBACK_EMBEDDING", "1")
    monkeypatch.setenv("SUPPORTOPS_MOCK_EMBEDDING", "1")
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    yield
