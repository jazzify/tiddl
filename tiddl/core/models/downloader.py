from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from tiddl.core.models.tidal.resources import Track, Video
from tiddl.core.types import (
    ChoiceFilterArtistSingles,
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


class PlanOptions(BaseModel, frozen=True):
    # replaces the per-resource template from the config when not empty
    template: str = ""
    track_quality: ChoiceQualityTrack
    video_quality: ChoiceQualityVideo
    videos_filter: ChoiceFilterVideos
    singles_filter: ChoiceFilterArtistSingles
    download_path: Path


class ItemPipelineOptions(BaseModel, frozen=True):
    metadata_enable: bool
    metadata_lyrics: bool
    metadata_cover: bool
    write_lrc_file: bool
    update_mtime: bool
    # tag files that were skipped because they already exist
    rewrite_metadata: bool


@dataclass(frozen=True)
class DownloadResult:
    status: DownloadStatus
    item: Track | Video
    path: Path | None = None
    reason: str = ""

    @property
    def downloaded(self) -> bool:
        return self.status in (
            DownloadStatus.DOWNLOADED,
            DownloadStatus.OVERWRITTEN,
        )
