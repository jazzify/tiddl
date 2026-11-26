from collections.abc import Callable
from typing import Any, Protocol

from tiddl.core.models.downloader import DownloadResult
from tiddl.core.models.plan import PlanError
from tiddl.core.models.tidal.items import Track, Video
from tiddl.core.models.tidal.responses import TrackStream, VideoStream

# opaque token: whatever `on_start` returns is passed back to `on_progress`/`on_done`
type Handle = Any

# Called for every error that does not stop planning. The sink decides what
# to do: print it, log it, or re-raise `error.exc` to abort planning.
type ErrorSink = Callable[[PlanError], None]

# Called for every failure of a resource or a labeled plan, with a description
# of what failed. The sink decides what to do: print it, or re-raise to abort.
type FailureSink = Callable[[Exception, str], None]


class Reporter(Protocol):
    """
    How the `Downloader` tells the outside world what it is doing.
    The downloader never prints; the CLI implements this with Rich.
    """

    def on_queued(self) -> None:
        """An item entered the pipeline (used for the overall total)."""
        ...

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
