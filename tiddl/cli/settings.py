from logging import getLogger
from os import environ
from pathlib import Path
from tomllib import loads as parse_toml

from tiddl.core.constants import (
    APP_DIR_NAME,
    CONFIG_FILENAME,
    ENV_APP_PATH,
)
from tiddl.core.models import Config

log = getLogger(__name__)


def load_config_file(config_file: Path) -> Config:
    log.debug(f"loading '{config_file}'")

    if not config_file.exists():
        log.debug("config file not found, loading default config")
        return Config()

    toml_dict = parse_toml(config_file.read_text())
    config = Config.model_validate(toml_dict, strict=True)

    log.debug("loaded config from file")

    return config


def get_app_path(env_key: str = ENV_APP_PATH) -> Path:
    if environ.get(env_key):
        return Path(environ[env_key])
    return Path.home() / APP_DIR_NAME


def create_app_path() -> Path:
    app_path = get_app_path()
    app_path.mkdir(exist_ok=True)
    return app_path


APP_PATH = create_app_path()
AUTH_DATA_FILE = APP_PATH / "auth.json"
CONFIG = load_config_file(APP_PATH / CONFIG_FILENAME)
