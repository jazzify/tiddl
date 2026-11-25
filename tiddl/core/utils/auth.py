import os
import stat
from logging import getLogger
from pathlib import Path

from pydantic import ValidationError

from tiddl.core.constants import FILE_WRITE_FLAGS, FILE_WRITE_MODE
from tiddl.core.models import AuthData
from tiddl.core.settings import AUTH_DATA_FILE

log = getLogger(__name__)


def load_auth_data(file_path: Path = AUTH_DATA_FILE) -> AuthData:
    log.debug(f"loading from '{AUTH_DATA_FILE}'")
    if not file_path.exists():
        return AuthData()
    try:
        return AuthData.model_validate_json(file_path.read_text(encoding="utf-8"))
    except ValidationError:
        file_path.unlink(missing_ok=True)
        return AuthData()


def save_auth_data(auth_data: AuthData, file_path: Path = AUTH_DATA_FILE):
    log.debug(f"saving to '{file_path}'")

    if file_path.exists():
        current_mode = stat.S_IMODE(file_path.stat().st_mode)
        if current_mode != FILE_WRITE_MODE:
            file_path.chmod(FILE_WRITE_MODE)
    else:
        file = os.open(file_path, FILE_WRITE_FLAGS, FILE_WRITE_MODE)
        os.close(file)

    file_path.write_text(auth_data.model_dump_json(), encoding="utf-8")
