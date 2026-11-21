from logging import getLogger
from pathlib import Path

from pydantic import BaseModel, field_validator

from tiddl.core.constants import DEFAULT_DOWNLOAD_PATH
from tiddl.core.types import (
    ChoiceFilterArtistSingles,
    ChoiceFilterAtmos,
    ChoiceFilterVideos,
    ChoiceQualityTrack,
    ChoiceQualityVideo,
    ChoiceResourceCover,
    ChoiceResourceM3U,
)

log = getLogger(__name__)


class Config(BaseModel):
    enable_cache: bool = True
    debug: bool = False

    class MetadataConfig(BaseModel):
        enable: bool = True
        lyrics: bool = False
        cover: bool = False
        album_review: bool = False

    metadata: MetadataConfig = MetadataConfig()

    class CoverConfig(BaseModel):
        save: bool = False
        size: int = 1280
        allowed: list[ChoiceResourceCover] = []

        class CoverTemplatesConfig(BaseModel):
            track: str = ""
            album: str = ""
            playlist: str = ""

        templates: CoverTemplatesConfig = CoverTemplatesConfig()

    cover: CoverConfig = CoverConfig()

    class DownloadConfig(BaseModel):
        track_quality: ChoiceQualityTrack = "max"
        video_quality: ChoiceQualityVideo = "fhd"
        skip_existing: bool = True
        threads_count: int = 4
        download_path: Path = DEFAULT_DOWNLOAD_PATH
        scan_path: Path = DEFAULT_DOWNLOAD_PATH
        singles_filter: ChoiceFilterArtistSingles = "none"
        videos_filter: ChoiceFilterVideos = "none"
        update_mtime: bool = False
        rewrite_metadata: bool = False
        write_lrc_file: bool = False
        match_existing_path_case: bool = False
        atmos_filter: ChoiceFilterAtmos = "none"

        def model_post_init(self, __context, /):
            # set scan path to download path when download path is non default
            if (
                self.scan_path == DEFAULT_DOWNLOAD_PATH
                and self.download_path != DEFAULT_DOWNLOAD_PATH
            ):
                self.scan_path = self.download_path

        @field_validator("download_path", "scan_path", mode="before")
        def str_to_path(cls, v):
            # convert to absolute, expand ~, normalize
            return Path(v).expanduser().resolve() if isinstance(v, str) else v

    download: DownloadConfig = DownloadConfig()

    class M3UConfig(BaseModel):
        # m3u playlists
        save: bool = False
        allowed: list[ChoiceResourceM3U] = []

        class M3UTemplatesConfig(BaseModel):
            album: str = ""
            playlist: str = ""
            mix: str = ""

        templates: M3UTemplatesConfig = M3UTemplatesConfig()

    m3u: M3UConfig = M3UConfig()

    class TemplatesConfig(BaseModel):
        default: str = "{album.artist}/{album.title}/{item.title}"
        track: str = ""
        video: str = ""
        album: str = ""
        playlist: str = ""
        mix: str = ""

        def model_post_init(self, __context, /):
            # override templates to default
            for field in ["track", "video", "album", "playlist", "mix"]:
                if getattr(self, field) == "":
                    setattr(self, field, self.default)

    templates: TemplatesConfig = TemplatesConfig()
