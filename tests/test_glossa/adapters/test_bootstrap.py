"""Tests for adapter bootstrap."""

from __future__ import annotations

import pytest

from glossa.adapters.bootstrap import bootstrap
from glossa.application.service import GlossaService
from glossa.errors import PluginLoadError


def test_bootstrap_returns_service(tmp_path) -> None:
    service = bootstrap(base_path=tmp_path)
    assert isinstance(service, GlossaService)


def test_bootstrap_propagates_plugin_failures(tmp_path, monkeypatch) -> None:
    def _fail(self):
        raise PluginLoadError("boom")

    monkeypatch.setattr(
        "glossa.adapters.bootstrap.EntryPointPluginLoader.load_plugins",
        _fail,
    )

    with pytest.raises(PluginLoadError):
        bootstrap(base_path=tmp_path)
