import asyncio
from logging import getLogger
from pathlib import Path
from typing import Annotated

import typer
from rich.live import Live

from tiddl.cli.commands import subcommands
from tiddl.cli.commands.auth import refresh
from tiddl.cli.ctx import Context
from tiddl.cli.settings import CONFIG
from tiddl.core.download import Downloader, ItemPipeline
from tiddl.core.download.pagination import paginate
from tiddl.core.download.quality import get_item_quality
from tiddl.core.exceptions import ApiError
from tiddl.core.metadata import (
    Cover,
    ItemMetadata,
)
from tiddl.core.models import (
    Album,
    DownloadOptions,
    ItemPipelineOptions,
    TidalResource,
)
from tiddl.core.types import (
    ChoiceFilterArtistSingles,
    ChoiceFilterAtmos,
    ChoiceFilterVideos,
    ChoiceQualityTrack,
    ChoiceQualityVideo,
)
from tiddl.core.utils.format import format_template
from tiddl.core.utils.m3u import save_m3u

from .output import RichOutput

download_command = typer.Typer(name="download")
download_command.add_typer(subcommands.url_subcommand)
download_command.add_typer(subcommands.fav_subcommand)
download_command.add_typer(subcommands.search_subcommand)


log = getLogger(__name__)


@download_command.callback(no_args_is_help=True)
def download_callback(
    ctx: Context,
    TRACK_QUALITY: Annotated[
        ChoiceQualityTrack,
        typer.Option(
            "--track-quality",
            "-q",
        ),
    ] = CONFIG.download.track_quality,
    VIDEO_QUALITY: Annotated[
        ChoiceQualityVideo,
        typer.Option(
            "--video-quality",
            "-vq",
        ),
    ] = CONFIG.download.video_quality,
    SKIP_EXISTING: Annotated[
        bool,
        typer.Option(
            "--no-skip",
            "-ns",
            help="Don't skip downloading existing files.",
        ),
    ] = not CONFIG.download.skip_existing,
    REWRITE_METADATA: Annotated[
        bool,
        typer.Option(
            "--rewrite-metadata",
            "-r",
            help="Rewrite metadata for already downloaded tracks.",
        ),
    ] = CONFIG.download.rewrite_metadata,
    THREADS_COUNT: Annotated[
        int,
        typer.Option(
            "--threads-count",
            "-t",
            help="Number of concurrent download threads.",
            min=1,
        ),
    ] = CONFIG.download.threads_count,
    DOWNLOAD_PATH: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Base directory path for all downloads.",
        ),
    ] = CONFIG.download.download_path,
    SCAN_PATH: Annotated[
        Path,
        typer.Option(
            "--scan-path",
            "--sp",
            help="Directory to search for your existing downloads.",
        ),
    ] = CONFIG.download.scan_path,
    TEMPLATE: Annotated[
        str,
        typer.Option(
            "--output",
            "-o",
            help="Format output file template.",
        ),
    ] = "",
    SINGLES_FILTER: Annotated[
        ChoiceFilterArtistSingles,
        typer.Option(
            "--singles",
            "-s",
            help="Filter for including artists' singles, used while downloading artist.",
        ),
    ] = CONFIG.download.singles_filter,
    VIDEOS_FILTER: Annotated[
        ChoiceFilterVideos,
        typer.Option(
            "--videos",
            "-vid",
            help="Videos handling: 'none' to exclude, 'allow' to include, 'only' to download videos only.",
        ),
    ] = CONFIG.download.videos_filter,
    RAISE_ERRORS: Annotated[
        bool,
        typer.Option(
            "--raise-errors",
            "-err",
            help="Raise an error on resource download failure. Use for debugging",
        ),
    ] = False,
    DOLBY_ATMOS_FILTER: Annotated[
        ChoiceFilterAtmos,
        typer.Option(
            "--dolby-atmos",
            "-da",
            help="Dolby Atmos filter, 'none' to exclude, 'allow' to include, 'only' to download only Dolby Atmos, if available.",
        ),
    ] = CONFIG.download.atmos_filter,
):
    """
    Download Tidal resources.
    """

    ctx.invoke(refresh, EARLY_EXPIRE_TIME=600)

    log.debug(f"{ctx.params=}")

    async def download_resources():
        rich_output = RichOutput(ctx.obj.console)

        downloader = Downloader(
            api=ctx.obj.api,
            options=DownloadOptions(
                threads_count=THREADS_COUNT,
                track_quality=TRACK_QUALITY,
                video_quality=VIDEO_QUALITY,
                videos_filter=VIDEOS_FILTER,
                skip_existing=not SKIP_EXISTING,
                download_path=DOWNLOAD_PATH,
                scan_path=SCAN_PATH,
                match_existing_path_case=CONFIG.download.match_existing_path_case,
                atmos_filter=DOLBY_ATMOS_FILTER,
            ),
            reporter=rich_output,
        )

        pipeline = ItemPipeline(
            api=ctx.obj.api,
            downloader=downloader,
            reporter=rich_output,
            options=ItemPipelineOptions(
                metadata_enable=CONFIG.metadata.enable,
                metadata_lyrics=CONFIG.metadata.lyrics,
                metadata_cover=CONFIG.metadata.cover,
                write_lrc_file=CONFIG.download.write_lrc_file,
                update_mtime=CONFIG.download.update_mtime,
                rewrite_metadata=REWRITE_METADATA,
            ),
        )
        handle_item = pipeline.run

        async def handle_resource(resource: TidalResource):
            async def download_album(album: Album):
                futures = []

                cover: Cover | None = None
                save_cover = ("album" in CONFIG.cover.allowed) and CONFIG.cover.save

                if album.cover and (CONFIG.metadata.cover or save_cover):
                    cover = Cover(album.cover, size=CONFIG.cover.size)

                album_review = ""

                if CONFIG.metadata.album_review:
                    try:
                        album_review = ctx.obj.api.get_album_review(
                            album_id=album.id
                        ).normalized_text()
                    except ApiError as e:
                        log.error(e)

                for album_items in paginate(
                    lambda offset: ctx.obj.api.get_album_items_credits(
                        album_id=album.id, offset=offset
                    )
                ):
                    for album_item in album_items.items:
                        try:
                            template = TEMPLATE or CONFIG.templates.album
                            file_path = format_template(
                                template=template,
                                item=album_item.item,
                                album=album,
                                quality=get_item_quality(
                                    album_item.item,
                                    TRACK_QUALITY,
                                    VIDEO_QUALITY,
                                ),
                            )

                        except AttributeError as exc:
                            log.error(f"{exc=}")
                            ctx.obj.console.print(
                                f"[red]Wrong Album Template:[/] {exc} ({template=}, {album.id=}, {album_item.item.id=})"
                            )
                            continue

                        try:
                            futures.append(
                                handle_item(
                                    item=album_item.item,
                                    file_path=file_path,
                                    track_metadata=ItemMetadata(
                                        cover=cover,
                                        date=str(album.releaseDate),
                                        artist=(
                                            album.artist.name if album.artist else ""
                                        ),
                                        credits=album_item.credits,
                                        album_review=album_review,
                                    ),
                                )
                            )
                        except ApiError as e:
                            item = album_item.item
                            track_info = f"Track: {getattr(item, 'title', 'Unknown')} (ID: {item.id})"
                            if hasattr(item, "album") and item.album:
                                track_info += f", Album ID: {item.album.id}"
                            ctx.obj.console.print(
                                f"[red]API Error:[/] {e} ({track_info})"
                            )
                            if RAISE_ERRORS:
                                raise
                        except Exception as e:
                            item = album_item.item
                            track_info = f"Track: {getattr(item, 'title', 'Unknown')} (ID: {item.id})"
                            ctx.obj.console.print(f"[red]Error:[/] {e} ({track_info})")
                            if RAISE_ERRORS:
                                raise

                tracks_with_path = await asyncio.gather(*futures)

                save_m3u(
                    settings=CONFIG.m3u,
                    download_path=DOWNLOAD_PATH,
                    resource_type="album",
                    filename=format_template(
                        CONFIG.m3u.templates.album,
                        album=album,
                        type="album",
                    ),
                    tracks_with_path=tracks_with_path,
                )

                if save_cover and cover:
                    cover.save_to_directory(
                        path=DOWNLOAD_PATH
                        / format_template(
                            template=CONFIG.cover.templates.album, album=album
                        )
                    )

            # resources should be collected from a distinct function
            # that would yield the resources.
            # then we would be able to reuse the logic in the export command

            match resource.type:
                case "track":
                    track = ctx.obj.api.get_track(resource.id)
                    album = ctx.obj.api.get_album(track.album.id)

                    cover: Cover | None = None
                    save_cover = ("track" in CONFIG.cover.allowed) and CONFIG.cover.save

                    if album.cover and (CONFIG.metadata.cover or save_cover):
                        cover = Cover(album.cover, size=CONFIG.cover.size)

                    await handle_item(
                        item=track,
                        file_path=format_template(
                            template=TEMPLATE or CONFIG.templates.track,
                            item=track,
                            album=album,
                            quality=get_item_quality(
                                track,
                                TRACK_QUALITY,
                                VIDEO_QUALITY,
                            ),
                        ),
                        track_metadata=ItemMetadata(
                            cover=cover,
                            date=str(album.releaseDate),
                            artist=album.artist.name if album.artist else "",
                            # credits are missing
                        ),
                    )

                    if (
                        CONFIG.cover.save
                        and ("track" in CONFIG.cover.allowed)
                        and track.album.cover
                    ):
                        Cover(
                            track.album.cover, size=CONFIG.cover.size
                        ).save_to_directory(
                            path=DOWNLOAD_PATH
                            / format_template(
                                CONFIG.cover.templates.track, item=track, album=album
                            )
                        )

                case "video":
                    video = ctx.obj.api.get_video(resource.id)
                    template = TEMPLATE or CONFIG.templates.video

                    if (
                        "{album" in template
                        and video.album
                        and video.album.id is not None
                    ):
                        album = ctx.obj.api.get_album(video.album.id)
                    else:
                        album = None

                    await handle_item(
                        item=video,
                        file_path=format_template(
                            template=template,
                            item=video,
                            album=album,
                            quality=get_item_quality(
                                video,
                                TRACK_QUALITY,
                                VIDEO_QUALITY,
                            ),
                        ),
                    )

                case "mix":
                    futures = []

                    for mix_items in paginate(
                        lambda offset: ctx.obj.api.get_mix_items(
                            resource.id, offset=offset
                        )
                    ):
                        for mix_item in mix_items.items:
                            template = TEMPLATE or CONFIG.templates.mix

                            try:
                                if "{album" in template:
                                    album = ctx.obj.api.get_album(
                                        mix_item.item.album.id
                                    )
                                else:
                                    album = None

                                futures.append(
                                    handle_item(
                                        item=mix_item.item,
                                        file_path=format_template(
                                            template=template,
                                            item=mix_item.item,
                                            album=album,
                                            mix_id=resource.id,
                                            quality=get_item_quality(
                                                mix_item.item,
                                                TRACK_QUALITY,
                                                VIDEO_QUALITY,
                                            ),
                                        ),
                                    )
                                )
                            except ApiError as e:
                                item = mix_item.item
                                track_info = f"Track: {getattr(item, 'title', 'Unknown')} (ID: {item.id})"
                                ctx.obj.console.print(
                                    f"[red]API Error:[/] {e} ({track_info})"
                                )
                                if RAISE_ERRORS:
                                    raise
                            except Exception as e:
                                item = mix_item.item
                                track_info = f"Track: {getattr(item, 'title', 'Unknown')} (ID: {item.id})"
                                ctx.obj.console.print(
                                    f"[red]Error:[/] {e} ({track_info})"
                                )
                                if RAISE_ERRORS:
                                    raise

                    tracks_with_path = await asyncio.gather(*futures)

                    save_m3u(
                        settings=CONFIG.m3u,
                        download_path=DOWNLOAD_PATH,
                        resource_type="mix",
                        filename=format_template(
                            CONFIG.m3u.templates.mix,
                            mix_id=resource.id,
                            type="mix",
                        ),
                        tracks_with_path=tracks_with_path,
                    )

                case "album":
                    album = ctx.obj.api.get_album(album_id=resource.id)
                    await download_album(album)

                case "artist":
                    futures = []

                    async def safe_download_album(album: Album):
                        try:
                            await download_album(album)
                        except ApiError as e:
                            ctx.obj.console.print(
                                f"[red]API Error:[/] {e} (Album: {album.title}, ID: {album.id})"
                            )
                            if RAISE_ERRORS:
                                raise
                        except Exception as e:
                            ctx.obj.console.print(
                                f"[red]Error:[/] {e} (Album: {album.title}, ID: {album.id})"
                            )
                            if RAISE_ERRORS:
                                raise

                    def get_all_albums(singles: bool):
                        for artist_albums in paginate(
                            lambda offset: ctx.obj.api.get_artist_albums(
                                artist_id=resource.id,
                                offset=offset,
                                filter="EPSANDSINGLES" if singles else "ALBUMS",
                            )
                        ):
                            for album in artist_albums.items:
                                futures.append(safe_download_album(album))

                    def get_all_videos():
                        for artist_videos in paginate(
                            lambda offset: ctx.obj.api.get_artist_videos(
                                resource.id, offset=offset
                            )
                        ):
                            for video in artist_videos.items:
                                template = TEMPLATE or CONFIG.templates.video

                                try:
                                    if "{album" in template and video.album:
                                        album = ctx.obj.api.get_album(video.album.id)
                                    else:
                                        album = None

                                    futures.append(
                                        handle_item(
                                            item=video,
                                            file_path=format_template(
                                                template=template,
                                                item=video,
                                                album=album,
                                                quality=get_item_quality(
                                                    video,
                                                    TRACK_QUALITY,
                                                    VIDEO_QUALITY,
                                                ),
                                            ),
                                        )
                                    )
                                except ApiError as e:
                                    ctx.obj.console.print(
                                        f"[red]API Error:[/] {e} (Video: {video.title}, ID: {video.id})"
                                    )
                                    if RAISE_ERRORS:
                                        raise
                                except Exception as e:
                                    ctx.obj.console.print(
                                        f"[red]Error:[/] {e} (Video: {video.title}, ID: {video.id})"
                                    )
                                    if RAISE_ERRORS:
                                        raise

                    if VIDEOS_FILTER != "none":
                        get_all_videos()

                    if VIDEOS_FILTER != "only":
                        if SINGLES_FILTER == "include":
                            get_all_albums(False)
                            get_all_albums(True)
                        else:
                            get_all_albums(SINGLES_FILTER == "only")

                    await asyncio.gather(*futures)

                case "playlist":
                    futures = []
                    playlist_index = 0
                    playlist = ctx.obj.api.get_playlist(playlist_uuid=resource.id)

                    for playlist_items in paginate(
                        lambda offset: ctx.obj.api.get_playlist_items(
                            playlist_uuid=resource.id, offset=offset
                        )
                    ):
                        for playlist_item in playlist_items.items:
                            playlist_index += 1
                            template = TEMPLATE or CONFIG.templates.playlist

                            try:
                                if "{album" in template:
                                    album = ctx.obj.api.get_album(
                                        playlist_item.item.album.id
                                    )
                                else:
                                    album = None

                                futures.append(
                                    handle_item(
                                        item=playlist_item.item,
                                        file_path=format_template(
                                            template=template,
                                            item=playlist_item.item,
                                            album=album,
                                            playlist=playlist,
                                            playlist_index=playlist_index,
                                            quality=get_item_quality(
                                                playlist_item.item,
                                                TRACK_QUALITY,
                                                VIDEO_QUALITY,
                                            ),
                                        ),
                                        track_metadata=ItemMetadata(),
                                    )
                                )
                            except ApiError as e:
                                item = playlist_item.item
                                track_info = f"Track: {getattr(item, 'title', 'Unknown')} (ID: {item.id})"
                                if hasattr(item, "album") and item.album:
                                    track_info += f", Album ID: {item.album.id}"
                                ctx.obj.console.print(
                                    f"[red]API Error:[/] {e} ({track_info})"
                                )
                                if RAISE_ERRORS:
                                    raise
                            except Exception as e:
                                item = playlist_item.item
                                track_info = f"Track: {getattr(item, 'title', 'Unknown')} (ID: {item.id})"
                                ctx.obj.console.print(
                                    f"[red]Error:[/] {e} ({track_info})"
                                )
                                if RAISE_ERRORS:
                                    raise

                    tracks_with_path = await asyncio.gather(*futures)

                    save_m3u(
                        settings=CONFIG.m3u,
                        download_path=DOWNLOAD_PATH,
                        resource_type="playlist",
                        filename=format_template(
                            CONFIG.m3u.templates.playlist,
                            playlist=playlist,
                            type="playlist",
                        ),
                        tracks_with_path=tracks_with_path,
                    )

                    if (
                        CONFIG.cover.save
                        and ("playlist" in CONFIG.cover.allowed)
                        and playlist.squareImage
                    ):
                        Cover(
                            playlist.squareImage, size=min(CONFIG.cover.size, 1080)
                        ).save_to_directory(
                            path=DOWNLOAD_PATH
                            / format_template(
                                template=CONFIG.cover.templates.playlist,
                                playlist=playlist,
                            )
                        )

        with Live(
            rich_output.group,
            refresh_per_second=10,
            console=ctx.obj.console,
            transient=True,
        ):

            async def wrapper(r: TidalResource):
                try:
                    await handle_resource(r)
                except ApiError as e:
                    ctx.obj.console.print(f"[red]API Error:[/] {e} ({r})")
                    if RAISE_ERRORS:
                        raise
                except Exception as e:
                    ctx.obj.console.print(f"[red]Error:[/] {e} ({r})")
                    if RAISE_ERRORS:
                        raise

            await asyncio.gather(*(wrapper(r) for r in ctx.obj.resources))

        rich_output.show_stats()

    def run():
        asyncio.run(download_resources())

    ctx.call_on_close(run)
