import logging
from typing import Annotated

import typer
from rich.console import Console

from tiddl.cli import commands
from tiddl.cli.config import APP_PATH, CONFIG
from tiddl.cli.ctx import Context, ContextObject
from tiddl.core.utils.ffmpeg import is_ffmpeg_installed as ifs

log = logging.getLogger("tiddl")

app = typer.Typer(name="tiddl", no_args_is_help=True, rich_markup_mode="rich")
app.add_typer(commands.auth_command)
app.add_typer(commands.download_command)

VERSION = "v3.4.4"


@app.callback()
def callback(
    ctx: Context,
    OMIT_CACHE: Annotated[
        bool,
        typer.Option(
            "--omit-cache",
        ),
    ] = not CONFIG.enable_cache,
    DEBUG: Annotated[
        bool,
        typer.Option(
            "--debug",
        ),
    ] = CONFIG.debug,
):
    log.debug(f"{VERSION=}")
    log.debug(f"{ctx.params=}")

    is_ffmpeg_installed = ifs()
    log.debug(f"{is_ffmpeg_installed=}")

    if DEBUG:
        debug_path = APP_PATH / "api_debug"
    else:
        debug_path = None

    ctx.obj = ContextObject(
        api_omit_cache=OMIT_CACHE, console=Console(), debug_path=debug_path
    )

    if not is_ffmpeg_installed:
        ctx.obj.console.print(
            "[yellow]WARNING ffmpeg is not installed, tiddl might not work properly"
        )
