import asyncio
from logging import getLogger
from pathlib import Path
from typing import Annotated

import typer

from tiddl.cli.commands.auth import refresh
from tiddl.cli.ctx import Context
from tiddl.cli.settings import CONFIG
from tiddl.core.models import (
    DownloadOptions,
    ItemPipelineOptions,
    PlanOptions,
)
from tiddl.core.types import (
    ChoiceFilterArtistSingles,
    ChoiceFilterAtmos,
    ChoiceFilterVideos,
    ChoiceQualityTrack,
    ChoiceQualityVideo,
)

from .session import download_resources
from .subcommands import (
    fav_subcommand,
    search_subcommand,
    url_subcommand,
)

download_command = typer.Typer(name="download")
download_command.add_typer(url_subcommand)
download_command.add_typer(fav_subcommand)
download_command.add_typer(search_subcommand)


log = getLogger(__name__)


@download_command.callback(no_args_is_help=True)
def download_callback(
    ctx: Context,
    track_quality: Annotated[
        ChoiceQualityTrack,
        typer.Option(
            "--track-quality",
            "-q",
            help="",
        ),
    ] = CONFIG.download.track_quality,
    video_quality: Annotated[
        ChoiceQualityVideo,
        typer.Option(
            "--video-quality",
            "-vq",
        ),
    ] = CONFIG.download.video_quality,
    skip_existing: Annotated[
        bool,
        typer.Option(
            "--no-skip",
            "-ns",
            help="Don't skip downloading existing files.",
        ),
    ] = not CONFIG.download.skip_existing,
    rewrite_metada: Annotated[
        bool,
        typer.Option(
            "--rewrite-metadata",
            "-r",
            help="Rewrite metadata for already downloaded tracks.",
        ),
    ] = CONFIG.download.rewrite_metadata,
    threads_count: Annotated[
        int,
        typer.Option(
            "--threads-count",
            "-t",
            help="Number of concurrent download threads.",
            min=1,
        ),
    ] = CONFIG.download.threads_count,
    download_path: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Base directory path for all downloads.",
        ),
    ] = CONFIG.download.download_path,
    scan_path: Annotated[
        Path,
        typer.Option(
            "--scan-path",
            "--sp",
            help="Directory to search for your existing downloads.",
        ),
    ] = CONFIG.download.scan_path,
    template: Annotated[
        str,
        typer.Option(
            "--output",
            "-o",
            help="Format output file template.",
        ),
    ] = "",
    singles_filter: Annotated[
        ChoiceFilterArtistSingles,
        typer.Option(
            "--singles",
            "-s",
            help="Filter for including artists' singles, used while downloading artist.",
        ),
    ] = CONFIG.download.singles_filter,
    videos_filter: Annotated[
        ChoiceFilterVideos,
        typer.Option(
            "--videos",
            "-vid",
            help="Videos handling: 'none' to exclude, 'allow' to include, 'only' to download videos only.",
        ),
    ] = CONFIG.download.videos_filter,
    dolby_atmos_filter: Annotated[
        ChoiceFilterAtmos,
        typer.Option(
            "--dolby-atmos",
            "-da",
            help="Dolby Atmos filter, 'none' to exclude, 'allow' to include, 'only' to download only Dolby Atmos, if available.",
        ),
    ] = CONFIG.download.atmos_filter,
    raise_errors: Annotated[
        bool,
        typer.Option(
            "--raise-errors",
            "-err",
            help="Raise an error on resource download failure. Use for debugging",
        ),
    ] = False,
):
    """
    Download resources from TIDAL, including tracks, albums, playlists, and videos.

    Remember that better quality tracks and videos consume more bandwidth and storage space. Choose wisely based on your needs and available resources.

    """

    ctx.invoke(refresh, EARLY_EXPIRE_TIME=600)

    log.debug(f"{ctx.params=}")

    ctx.call_on_close(
        lambda: asyncio.run(
            download_resources(
                obj=ctx.obj,
                config=CONFIG,
                download_options=DownloadOptions(
                    threads_count=threads_count,
                    track_quality=track_quality,
                    video_quality=video_quality,
                    videos_filter=videos_filter,
                    skip_existing=not skip_existing,
                    download_path=download_path,
                    scan_path=scan_path,
                    match_existing_path_case=CONFIG.download.match_existing_path_case,
                    atmos_filter=dolby_atmos_filter,
                ),
                plan_options=PlanOptions(
                    template=template,
                    track_quality=track_quality,
                    video_quality=video_quality,
                    videos_filter=videos_filter,
                    singles_filter=singles_filter,
                    download_path=download_path,
                ),
                pipeline_options=ItemPipelineOptions(
                    metadata_enable=CONFIG.metadata.enable,
                    metadata_lyrics=CONFIG.metadata.lyrics,
                    metadata_cover=CONFIG.metadata.cover,
                    write_lrc_file=CONFIG.download.write_lrc_file,
                    update_mtime=CONFIG.download.update_mtime,
                    rewrite_metadata=rewrite_metada,
                ),
                raise_errors=raise_errors,
            )
        )
    )
