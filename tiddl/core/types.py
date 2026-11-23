from enum import StrEnum
from typing import Any, Literal, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


# Tidal wire values
TrackQuality = Literal["LOW", "HIGH", "LOSSLESS", "HI_RES_LOSSLESS"]
ArtistAlbumsFilter = Literal["ALBUMS", "EPSANDSINGLES"]
StreamVideoQuality = Literal[
    "AUDIO_ONLY", "LOW", "MEDIUM", "HIGH"  # AUDIO_ONLY is not stable
]
MediaMetadataTags = Literal["LOSSLESS", "HIRES_LOSSLESS", "DOLBY_ATMOS"]

# User choices
ChoiceFilterArtistSingles = Literal["none", "only", "include"]
ChoiceFilterAtmos = Literal["none", "only", "allow"]
ChoiceFilterVideos = Literal["none", "only", "allow"]
ChoiceQualityTrack = Literal["low", "high", "lossless", "max"]
ChoiceQualityVideo = Literal["sd", "hd", "fhd"]
ChoiceResourceM3U = Literal["album", "playlist", "mix"]
ChoiceResourceCover = Literal["track", "album", "playlist"]

# Auth
type JSON = dict[str, Any]

# Api
type ID = str | int

# Models
ItemType = Literal["track", "video"]


class DownloadStatus(StrEnum):
    DOWNLOADED = "downloaded"
    OVERWRITTEN = "overwritten"
    EXISTS = "exists"
    NOT_STREAMABLE = "not_streamable"
    SKIPPED_VIDEO_FILTER = "skipped_video_filter"
    SKIPPED_ATMOS_FILTER = "skipped_atmos_filter"
    FAILED = "failed"


class PlanErrorKind(StrEnum):
    # a file template could not be formatted, the item is skipped
    TEMPLATE = "template"
    # anything else that went wrong while planning one item or album
    ITEM = "item"


### CLI
# Resources
ResourceTypeLiteral = Literal["track", "video", "album", "playlist", "artist", "mix"]
