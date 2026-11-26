from tiddl.core.models.downloader import DownloadResult
from tiddl.core.models.tidal.items import Track, Video
from tiddl.core.models.tidal.responses import TrackStream, VideoStream
from tiddl.core.protocols import Handle


class NullReporter:
    """Reporter that ignores every event."""

    def on_queued(self) -> None:
        pass

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
