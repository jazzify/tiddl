from tiddl.core.models import DownloadResult, Track, TrackStream, Video, VideoStream
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
