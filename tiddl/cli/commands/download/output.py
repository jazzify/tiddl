from pathlib import Path

from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    FileSizeColumn,
    MofNCompleteColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    Task,
    TaskID,
    TransferSpeedColumn,
)
from rich.text import Text

from tiddl.core.constants import (
    QUALITY_COLOR_TRACK,
    QUALITY_COLOR_VIDEO,
    RESULT_MESSAGE,
)
from tiddl.core.download import PlanError, PlanErrorKind, Reporter
from tiddl.core.download.reporter import Handle
from tiddl.core.exceptions import ApiError, CLIValidationException
from tiddl.core.models import (
    DownloadResult,
    Track,
    TrackStream,
    Video,
    VideoStream,
)
from tiddl.core.types import DownloadStatus


def vibrant_color(item: Track | Video) -> str:
    color = item.album.vibrantColor if isinstance(item, Track) else item.vibrantColor
    return color or "gray"


def quality_label(stream: TrackStream | VideoStream) -> str:
    if isinstance(stream, VideoStream):
        return QUALITY_COLOR_VIDEO[stream.videoQuality]
    label = QUALITY_COLOR_TRACK[stream.audioQuality]
    if (
        stream.audioQuality in ["HI_RES_LOSSLESS", "LOSSLESS"]
        and stream.audioMode == "STEREO"
    ):
        return (
            f"{label} {stream.bitDepth}-bit, {(stream.sampleRate or 0) / 1000:.1f} kHz"
        )
    if stream.audioMode == "DOLBY_ATMOS":
        return "[blue]Dolby Atmos[/]"
    return label


class TimeElapsedColumn(ProgressColumn):
    """Renders time elapsed."""

    def render(self, task: Task) -> Text:
        """Show time elapsed."""
        elapsed = task.finished_time if task.finished else task.elapsed
        if elapsed is None:
            return Text("---", style="progress.elapsed")
        return Text(f"{elapsed:.2f}s", style="progress.elapsed")


class RichOutput(Reporter):
    def __init__(self, console: Console, download_height: int | None = None) -> None:
        self.console = console

        self.download_progress = Progress(
            SpinnerColumn(),
            "{task.description}",
            FileSizeColumn(),
            TransferSpeedColumn(),
            console=self.console,
        )
        self.total_progress = Progress(
            TimeElapsedColumn(),
            BarColumn(bar_width=None),
            MofNCompleteColumn(),
            console=self.console,
        )

        self.group = Group(
            Panel(
                self.download_progress,
                title="Downloading",
                border_style="magenta",
                title_align="left",
                height=download_height + 2 if download_height else None,
            ),
            Panel(
                self.total_progress,
                title="Total Progress",
                border_style="green",
                title_align="left",
            ),
        )

        self.total_task = self.total_progress.add_task("Total", total=0, start=True)
        self.total_downloads = 0

    def total_increment(self, count: float = 1):
        task = self.total_progress._tasks.get(self.total_task)

        if not task or task.total is None:
            raise CLIValidationException(
                key="CLI_VALIDATION_TOTAL_INCREMENT_EXCEPTION", extra={"task": task}
            )

        self.total_progress.update(self.total_task, total=task.total + count)

    def download_start(self, description: str) -> TaskID:
        return self.download_progress.add_task(description=description, total=None)

    def download_advance(self, task_id: TaskID, size: float):
        self.download_progress.update(task_id=task_id, advance=size, refresh=True)

    def download_finish(self, task_id: TaskID) -> Task:
        task = self.download_progress._tasks.get(task_id)

        if not task:
            raise CLIValidationException(
                key="CLI_VALIDATION_DOWNLOAD_FINISH_EXCEPTION", extra={"task": task}
            )

        self.download_progress.remove_task(task_id=task_id)
        self.total_progress.advance(self.total_task, advance=1)
        self.total_downloads += 1

        return task

    def show_stats(self):
        self.console.print(f"[green]Total downloads: {self.total_downloads}")

    def show_item_result(
        self, result_message: str, item_description: str, item_path: Path | None
    ):
        if item_path:
            description = f"[link={item_path.as_uri()}]{item_description}[/link] [link={item_path.parent.as_uri()}]{item_path.parent}[/link]"
        else:
            description = item_description

        self.console.print(f"{result_message} {description}")

    def on_queued(self) -> None:
        self.total_increment()

    def on_start(
        self, item: Track | Video, stream: TrackStream | VideoStream
    ) -> Handle:
        return self.download_start(
            f"[{vibrant_color(item)}]{item.title} {quality_label(stream)}"
        )

    def on_progress(self, handle: Handle, size: int) -> None:
        self.download_advance(handle, size=size)

    def on_done(self, handle: Handle, result: DownloadResult) -> None:
        task = self.download_finish(task_id=handle)
        self.show_item_result(
            result_message=RESULT_MESSAGE[result.status],
            item_description=task.description,
            item_path=result.path,
        )

    def on_skip(self, result: DownloadResult) -> None:
        item = result.item

        match result.status:
            case DownloadStatus.EXISTS:
                self.show_item_result(
                    result_message="[yellow]Exists",
                    item_description=f"[{vibrant_color(item)}]{item.title}",
                    item_path=result.path,
                )
            case DownloadStatus.NOT_STREAMABLE:
                self.console.print(f"[red]Can't stream[/] {item.title} ({item.id})")
            case DownloadStatus.SKIPPED_VIDEO_FILTER:
                self.console.print(
                    f"Skipping '{item.title}' due to video filter set to '{result.reason}'"
                )
            case DownloadStatus.SKIPPED_ATMOS_FILTER:
                self.console.print(
                    f"[blue]Skipping[/] [gray]{item.title}[/] [blue]due to Dolby Atmos filter[/] {result.reason}"
                )
            case DownloadStatus.FAILED:
                self.console.print(
                    f"[red]Error [{vibrant_color(item)}]{item.title}[/] - {result.reason}"
                )


class ErrorReporter:
    """Prints failures and decides whether they abort the download."""

    def __init__(self, console: Console, raise_errors: bool) -> None:
        self.console = console
        self.raise_errors = raise_errors

    def plan_error(self, error: PlanError) -> None:
        if error.kind is PlanErrorKind.TEMPLATE:
            self.console.print(
                f"[red]Wrong Album Template:[/] {error.exc} ({error.context})"
            )
            return
        self.failure(error.exc, error.context)

    def failure(self, exc: Exception, context: str) -> None:
        label = "API Error" if isinstance(exc, ApiError) else "Error"
        self.console.print(f"[red]{label}:[/] {exc} ({context})")
        if self.raise_errors:
            raise exc
