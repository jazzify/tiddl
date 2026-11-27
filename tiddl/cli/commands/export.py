from logging import getLogger

import typer

from tiddl.cli.commands.auth import refresh
from tiddl.cli.console import console
from tiddl.cli.ctx import Context

export_command = typer.Typer(name="export")

log = getLogger(__name__)


@export_command.callback(no_args_is_help=True)
def export_callback(ctx: Context):
    """
    Export Tidal data.

    You can export the data to json file
    or pipe it to another process.
    """

    ctx.invoke(refresh)

    # TODO implement export functionality

    # exported structure
    # [{resource_type: str, resource_id: str|int, album: {...}, album_items: {...}}]

    # export to single files like id.json
    # or export all in one

    def handle_export():
        console.print("WIP")

    ctx.call_on_close(handle_export)
