import asyncio
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path

from tiddl.core.api import TidalAPI
from tiddl.core.constants import QUALITIES_TRACK, QUALITIES_VIDEO
from tiddl.core.exceptions import ApiError, FFmpegError
from tiddl.core.models import (
    DownloadOptions,
    DownloadResult,
    DownloadStatus,
    Track,
    TrackStream,
    Video,
    VideoStream,
)
from tiddl.core.types import StreamVideoQuality, TrackQuality
from tiddl.core.utils import parse_track_stream, parse_video_stream
from tiddl.core.utils.ffmpeg import convert_to_mp4, extract_flac

from .filters import atmos_filter_skips, video_filter_skips
from .paths import get_existing_track_filename, resolve_existing_path_case
from .reporter import NullReporter, Reporter
from .transport import stream_to_file

log = getLogger(__name__)


@dataclass(frozen=True)
class _Plan:
    """Resolved stream: what to fetch and where to put it."""

    stream: TrackStream | VideoStream
    urls: list[str]
    path: Path
    extract_flac: bool = False


class Downloader:
    def __init__(
        self,
        api: TidalAPI,
        options: DownloadOptions,
        reporter: Reporter | None = None,
    ) -> None:
        self.api = api
        self.options = options
        self.reporter: Reporter = reporter or NullReporter()
        self.semaphore = asyncio.Semaphore(options.threads_count)
        self.track_quality: TrackQuality = QUALITIES_TRACK[options.track_quality]
        self.video_quality: StreamVideoQuality = QUALITIES_VIDEO[options.video_quality]

    def _get_path(self, base_path: Path, relative_path: Path) -> Path:
        if self.options.match_existing_path_case:
            return resolve_existing_path_case(base_path, relative_path)
        return base_path / relative_path

    def _skipped(
        self,
        status: DownloadStatus,
        item: Track | Video,
        path: Path | None = None,
        reason: str = "",
    ) -> DownloadResult:
        result = DownloadResult(status=status, item=item, path=path, reason=reason)
        self.reporter.on_skip(result)
        return result

    def _plan_track(self, item: Track, filename: Path) -> _Plan | DownloadResult:
        try:
            stream = self.api.get_track_stream(
                track_id=item.id, quality=self.track_quality
            )
            log.debug(f"{stream.trackId=}, {stream.audioQuality=}, {stream.audioMode=}")
            if atmos_filter_skips(stream.audioMode, self.options.atmos_filter):
                return self._skipped(
                    DownloadStatus.SKIPPED_ATMOS_FILTER,
                    item,
                    reason=self.options.atmos_filter,
                )
        except ApiError as e:
            log.error(f"{item.id=} {e=}")
            return self._skipped(DownloadStatus.FAILED, item, reason=e.user_message)
        urls, _ = parse_track_stream(stream)
        path = self._get_path(self.options.download_path, filename)
        if (
            stream.audioQuality in ["HI_RES_LOSSLESS", "LOSSLESS"]
            and stream.audioMode == "STEREO"
        ):
            return _Plan(stream, urls, path, extract_flac=True)
        return _Plan(stream, urls, path.with_suffix(".m4a"))

    def _plan_video(self, item: Video, filename: Path) -> _Plan:
        stream = self.api.get_video_stream(video_id=item.id, quality=self.video_quality)
        urls = parse_video_stream(stream)
        path = self._get_path(self.options.download_path, filename).with_suffix(".ts")
        return _Plan(stream, urls, path)

    async def download(self, item: Track | Video, file_path: Path) -> DownloadResult:
        if not item.allowStreaming:
            return self._skipped(DownloadStatus.NOT_STREAMABLE, item)
        if isinstance(item, Track):
            filename = get_existing_track_filename(
                item.audioQuality, self.track_quality, file_path
            )
        else:
            filename = file_path.with_suffix(".mp4")
        existing_file_path = self._get_path(self.options.scan_path, filename)

        log.debug(f"{file_path=}, {filename=}, {existing_file_path=}")

        status = DownloadStatus.DOWNLOADED
        if existing_file_path.exists():
            status = DownloadStatus.OVERWRITTEN

            if self.options.skip_existing:
                return self._skipped(
                    DownloadStatus.EXISTS, item, path=existing_file_path
                )
        elif video_filter_skips(item, self.options.videos_filter):
            log.debug(f"skipping {item.id} due to {self.options.videos_filter=}")
            return self._skipped(
                DownloadStatus.SKIPPED_VIDEO_FILTER,
                item,
                reason=self.options.videos_filter,
            )
        async with self.semaphore:
            if isinstance(item, Track):
                plan = self._plan_track(item, filename)
            else:
                plan = self._plan_video(item, filename)

            if isinstance(plan, DownloadResult):
                return plan

            handle = self.reporter.on_start(item, plan.stream)

            plan.path.parent.mkdir(exist_ok=True, parents=True)
            await stream_to_file(
                plan.urls,
                plan.path,
                on_progress=lambda size: self.reporter.on_progress(handle, size),
            )
            download_path = plan.path
            try:
                if isinstance(item, Track) and plan.extract_flac:
                    download_path = extract_flac(download_path)
                elif isinstance(item, Video):
                    download_path = convert_to_mp4(download_path)
            except (FFmpegError, OSError) as exc:
                log.error(f"{plan.extract_flac=}, {exc=}")
            result = DownloadResult(status=status, item=item, path=download_path)
            self.reporter.on_done(handle, result)
            return result
