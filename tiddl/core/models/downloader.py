from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from tiddl.core.models.tidal.resources import Track, Video
from tiddl.core.types import (
    ChoiceFilterAtmos,
    ChoiceFilterVideos,
    ChoiceQualityTrack,
    ChoiceQualityVideo,
    DownloadStatus,
)


class DownloadOptions(BaseModel, frozen=True):
    threads_count: int = Field(ge=1)
    track_quality: ChoiceQualityTrack
    video_quality: ChoiceQualityVideo
    videos_filter: ChoiceFilterVideos
    skip_existing: bool
    download_path: Path
    scan_path: Path
    match_existing_path_case: bool = False
    atmos_filter: ChoiceFilterAtmos = "none"


@dataclass(frozen=True)
class DownloadResult:
    status: DownloadStatus
    item: Track | Video
    path: Path | None = None
    # extra detail: the filter mode for SKIPPED_*, the API message for FAILED
    reason: str = ""

    @property
    def downloaded(self) -> bool:
        return self.status in (
            DownloadStatus.DOWNLOADED,
            DownloadStatus.OVERWRITTEN,
        )
