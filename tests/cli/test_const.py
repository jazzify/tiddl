from pathlib import Path

import pytest

from tiddl.core.constants import APP_DIR_NAME, ENV_APP_PATH
from tiddl.core.settings import get_app_path


def test_env_key_overrides(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    custom_path = tmp_path / "customdir"
    monkeypatch.setenv(ENV_APP_PATH, str(custom_path))
    app_path = get_app_path(ENV_APP_PATH)

    assert app_path == custom_path


def test_default_path_if_unset(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv(ENV_APP_PATH, raising=False)
    app_path = get_app_path(ENV_APP_PATH)

    assert str(Path.home()) in str(app_path)
    assert app_path.name == APP_DIR_NAME
