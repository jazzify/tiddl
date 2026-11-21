from typing import Any, Protocol

from tiddl.core.models import DownloadResult, Track, TrackStream, Video, VideoStream

# opaque token: whatever `on_start` returns is passed back to `on_progress`/`on_done`
type Handle = Any


class Reporter(Protocol):
    """
    How the `Downloader` tells the outside world what it is doing.
    The downloader never prints; the CLI implements this with Rich.
    """

    def on_start(
        self, item: Track | Video, stream: TrackStream | VideoStream
    ) -> Handle: ...

    def on_progress(self, handle: Handle, size: int) -> None: ...

    def on_done(self, handle: Handle, result: DownloadResult) -> None:
        """Item was downloaded (status DOWNLOADED or OVERWRITTEN)."""
        ...

    def on_skip(self, result: DownloadResult) -> None:
        """Nothing was downloaded (EXISTS, NOT_STREAMABLE, SKIPPED_*, FAILED)."""
        ...


class NullReporter:
    def on_start(
        self, item: Track | Video, stream: TrackStream | VideoStream
    ) -> Handle:
        return None

    def on_progress(self, handle: Handle, size: int) -> None:
        pass

    def on_done(self, handle: Handle, result: DownloadResult) -> None:
        pass

    def on_skip(self, result: DownloadResult) -> None:
        pass
