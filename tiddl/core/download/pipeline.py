import os
from logging import getLogger
from pathlib import Path

from tiddl.core.api import TidalAPI
from tiddl.core.exceptions import ApiError
from tiddl.core.metadata import (
    Cover,
    ItemMetadata,
    add_track_metadata,
    add_video_metadata,
)
from tiddl.core.models import ItemPipelineOptions, Track, Video

from .downloader import Downloader
from .lrc import write_lrc_file
from .reporter import NullReporter, Reporter

log = getLogger(__name__)


class ItemPipeline:
    """Download one item, then tag it."""

    def __init__(
        self,
        api: TidalAPI,
        downloader: Downloader,
        options: ItemPipelineOptions,
        reporter: Reporter | None = None,
    ) -> None:
        self.api = api
        self.downloader = downloader
        self.options = options
        self.reporter: Reporter = reporter or NullReporter()

    async def run(
        self,
        item: Track | Video,
        file_path: str | Path,
        track_metadata: ItemMetadata | None = None,
    ) -> tuple[Path | None, Track | Video]:
        log.debug(f"{item.id=}, {file_path=}")
        self.reporter.on_queued()
        result = await self.downloader.download(item=item, file_path=Path(file_path))
        download_path = result.path
        log.debug(f"{download_path=}, {result.downloaded=}")
        if (
            self.options.metadata_enable
            and download_path
            # rewrite metadata when track was skipped due to already existing
            and (self.options.rewrite_metadata or result.downloaded)
        ):
            if track_metadata is None:
                track_metadata = ItemMetadata()
            self._tag(item, download_path, track_metadata)
        if download_path and self.options.update_mtime:
            os.utime(download_path, None)
        return download_path, item

    def _tag(self, item: Track | Video, path: Path, metadata: ItemMetadata) -> None:
        if isinstance(item, Track):
            self._tag_track(item, path, metadata)
        else:
            add_video_metadata(path=path, video=item)

    def _tag_track(self, item: Track, path: Path, metadata: ItemMetadata) -> None:
        lyrics = ""
        if self.options.metadata_lyrics or self.options.write_lrc_file:
            try:
                lyrics = self.api.get_track_lyrics(item.id).subtitles
            except ApiError as e:
                log.error(e)
        if self.options.write_lrc_file:
            write_lrc_file(track=item, lyrics=lyrics, file_path=path)
        if not metadata.cover and item.album.cover and self.options.metadata_cover:
            metadata.cover = Cover(item.album.cover)
        if metadata.cover and metadata.cover.data is None:
            metadata.cover.fetch_data()
        add_track_metadata(
            path=path,
            track=item,
            lyrics=lyrics,
            album_artist=metadata.artist,
            cover_data=metadata.cover.data if metadata.cover else None,
            date=metadata.date,
            credits_contributors=metadata.credits,
            comment=metadata.album_review,
        )
