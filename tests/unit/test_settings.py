import importlib
from pathlib import Path

import pytest

import src.config.settings as settings_module


@pytest.fixture(autouse=True)
def reload_settings_after_test():
    """Ensure Settings module reloads to default configuration after each test."""
    yield
    importlib.reload(settings_module)


def test_feature_flags_loaded_from_yaml(tmp_path, monkeypatch):
    features_file = tmp_path / "features.yaml"
    features_file.write_text(
        """
        cag:
          categories:
            demo_category:
              state: beta
              rollout: 0.5
        """
    )

    monkeypatch.setenv("FEATURES_FILE", str(features_file))
    importlib.reload(settings_module)

    try:
        flags = settings_module.settings.feature_flags
        assert flags["cag"]["categories"]["demo_category"]["state"] == "beta"
        assert (
            settings_module.settings.get_feature_flag("cag", "categories", "demo_category", "state")
            == "beta"
        )
    finally:
        monkeypatch.delenv("FEATURES_FILE", raising=False)


def test_missing_feature_file_returns_empty(monkeypatch):
    monkeypatch.setenv("FEATURES_FILE", str(Path("nonexistent_features.yaml")))
    importlib.reload(settings_module)

    try:
        assert settings_module.settings.feature_flags == {}
    finally:
        monkeypatch.delenv("FEATURES_FILE", raising=False)


def test_reload_feature_flags(tmp_path, monkeypatch):
    features_file = tmp_path / "features.yaml"
    features_file.write_text("initial: true\n")

    monkeypatch.setenv("FEATURES_FILE", str(features_file))
    importlib.reload(settings_module)

    try:
        assert settings_module.settings.get_feature_flag("initial") is True

        features_file.write_text("initial: false\n")
        settings_module.settings.reload_feature_flags()

        assert settings_module.settings.get_feature_flag("initial") is False
    finally:
        monkeypatch.delenv("FEATURES_FILE", raising=False)
