from pathlib import Path
from time import time

import typer

from tiddl.core.api.api import TidalAPI
from tiddl.core.api.client import TidalClient
from tiddl.core.auth.api import AuthAPI
from tiddl.core.exceptions import CLIValidationException
from tiddl.core.models.tidal.resources import TidalResource
from tiddl.core.settings import APP_PATH
from tiddl.core.utils.auth import load_auth_data, save_auth_data


class ContextObject:
    resources: list[TidalResource]
    auth_api: AuthAPI
    _api: TidalAPI | None
    api_omit_cache: bool
    debug_path: Path | None

    def __init__(
        self,
        api_omit_cache: bool,
        debug_path: Path | None,
    ) -> None:
        self.resources = []
        self.auth_api = AuthAPI()
        self._api = None
        self.api_omit_cache = api_omit_cache
        self.debug_path = debug_path

    @property
    def api(self):
        if self._api is not None:
            return self._api

        auth_data = load_auth_data()
        if not auth_data.token:
            raise CLIValidationException(
                key="CLI_VALIDATION_AUTH_DATA_EXCEPTION",
                message="Auth Token is missing. Use `tiddl auth login`",
            )
        if not auth_data.user_id:
            raise CLIValidationException(
                key="CLI_VALIDATION_AUTH_DATA_EXCEPTION",
                message="User ID is missing. Use `tiddl auth login`",
            )
        if not auth_data.country_code:
            raise CLIValidationException(
                key="CLI_VALIDATION_AUTH_DATA_EXCEPTION",
                message="Country Code is missing. Use `tiddl auth login`",
            )
        if not auth_data.refresh_token:
            raise CLIValidationException(
                key="CLI_VALIDATION_AUTH_DATA_EXCEPTION",
                message="Refresh Token is missing. Use `tiddl auth login`",
            )
        refresh_token = auth_data.refresh_token

        def on_token_expiry() -> str | None:
            auth_response = self.auth_api.refresh_token(refresh_token)
            auth_data.token = auth_response.access_token
            auth_data.expires_at = auth_response.expires_in + int(time())

            save_auth_data(auth_data=auth_data)

            if auth_response:
                return auth_response.access_token

            return None

        client = TidalClient(
            token=auth_data.token,
            cache_name=APP_PATH / "api_cache",
            omit_cache=self.api_omit_cache,
            debug_path=self.debug_path,
            on_token_expiry=on_token_expiry,
        )

        self._api = TidalAPI(client, auth_data.user_id, auth_data.country_code)

        return self._api


class Context(typer.Context):
    obj: ContextObject
