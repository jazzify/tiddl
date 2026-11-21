from datetime import datetime
from typing import Any, Literal, get_args
from urllib.parse import urlparse

from pydantic import BaseModel

from tiddl.core.types import MediaMetadataTags, ResourceTypeLiteral, TrackQuality


class TidalResource(BaseModel):
    type: ResourceTypeLiteral
    id: str

    @property
    def url(self) -> str:
        return f"https://listen.tidal.com/{self.type}/{self.id}"

    @classmethod
    def from_string(cls, string: str):
        """
        Extracts the resource type (e.g., "track", "album")
        and resource ID from a given input string.

        The input string can either be a full URL or a shorthand string
        in the format `resource_type/resource_id` (e.g., `track/12345678`).
        """

        segments = [seg for seg in urlparse(string).path.split("/") if seg]

        resource_type = next(
            (seg for seg in segments if seg in get_args(ResourceTypeLiteral)), None
        )

        if not resource_type:
            raise ValueError(f"Invalid resource type: {resource_type}")

        try:
            resource_id = segments[segments.index(resource_type) + 1]
        except IndexError:
            raise ValueError(f"No resource ID found {resource_type=} {string=}")

        digit_resource_types: list[ResourceTypeLiteral] = [
            "track",
            "album",
            "video",
            "artist",
        ]

        if resource_type in digit_resource_types and not resource_id.isdigit():
            raise ValueError(f"Invalid resource id: {resource_id}")

        return cls(type=resource_type, id=resource_id)  # type: ignore

    def __str__(self) -> str:
        return f"{self.type}/{self.id}"


class Track(BaseModel):
    class Artist(BaseModel):
        id: int
        name: str
        type: str
        picture: str | None = None

    class Album(BaseModel):
        id: int
        title: str
        cover: str | None = None
        vibrantColor: str | None = None
        videoCover: str | None = None

    class MediaMetadata(BaseModel):
        tags: list[MediaMetadataTags]

    id: int
    title: str
    duration: int
    replayGain: float
    peak: float
    allowStreaming: bool
    streamReady: bool
    adSupportedStreamReady: bool
    djReady: bool
    stemReady: bool
    premiumStreamingOnly: bool
    trackNumber: int
    volumeNumber: int
    popularity: int
    url: str
    isrc: str
    editable: bool
    explicit: bool
    audioQuality: TrackQuality
    audioModes: list[str]
    mediaMetadata: MediaMetadata
    artists: list[Artist]
    album: Album
    streamStartDate: datetime | None = None
    version: str | None = None
    copyright: str | None = None
    bpm: int | None = None
    artist: Artist | None = None
    mixes: dict[str, str] | None = None


class Video(BaseModel):
    class Artist(BaseModel):
        id: int
        name: str
        type: str
        picture: str | None = None

    class Album(BaseModel):
        id: int | None = None
        title: str | None = None
        cover: str | None = None
        vibrantColor: str | None = None
        videoCover: str | None = None

    id: int
    title: str
    volumeNumber: int
    trackNumber: int
    streamStartDate: datetime | None = None
    imagePath: str | None = None
    imageId: str | None = None
    vibrantColor: str | None = None
    duration: int
    quality: Literal["MP4_1080P"] | str
    streamReady: bool
    adSupportedStreamReady: bool
    djReady: bool
    stemReady: bool
    allowStreaming: bool
    explicit: bool
    popularity: int
    type: str
    adsUrl: str | None = None
    adsPrePaywallOnly: bool
    artist: Artist | None = None
    artists: list[Artist]
    album: Album | None = None


class Album(BaseModel):
    class Artist(BaseModel):
        id: int
        name: str
        type: Literal["MAIN", "FEATURED"]
        picture: str | None = None

    class MediaMetadata(BaseModel):
        tags: list[MediaMetadataTags]

    id: int
    title: str
    duration: int
    streamReady: bool
    adSupportedStreamReady: bool
    djReady: bool
    stemReady: bool
    allowStreaming: bool
    premiumStreamingOnly: bool
    numberOfTracks: int
    numberOfVideos: int
    numberOfVolumes: int
    type: Literal["ALBUM", "SINGLE", "EP"]
    url: str
    explicit: bool
    popularity: int
    audioQuality: str
    audioModes: list[str]
    mediaMetadata: MediaMetadata
    # artist is none in search query
    streamStartDate: datetime | None = None
    releaseDate: datetime | None = None
    copyright: str | None = None
    version: str | None = None
    cover: str | None = None
    vibrantColor: str | None = None
    videoCover: str | None = None
    upc: str | None = None
    artist: Artist | None = None
    artists: list[Artist]


class Playlist(BaseModel):
    class Creator(BaseModel):
        id: int

    uuid: str
    title: str
    numberOfTracks: int
    numberOfVideos: int
    creator: Creator | dict[Any, Any]
    duration: int
    lastUpdated: str
    created: str
    type: str
    publicPlaylist: bool
    url: str
    popularity: int
    promotedArtists: list[Album.Artist]
    description: str | None = None
    image: str | None = None
    squareImage: str | None = None
    lastItemAddedAt: str | None = None


class Artist(BaseModel):
    class Role(BaseModel):
        categoryId: int
        category: Literal[
            "Artist",
            "Songwriter",
            "Performer",
            "Producer",
            "Engineer",
            "Production team",
            "Misc",
        ]

    class Mix(BaseModel):
        ARTIST_MIX: str
        MASTER_ARTIST_MIX: str | None = None

    id: int
    name: str
    type: Literal["MAIN", "FEATURED"]
    artistTypes: list[Literal["ARTIST", "CONTRIBUTOR"]] | None = None
    url: str | None = None
    picture: str | None = None
    selectedAlbumCoverFallback: str | None = None
    popularity: int | None = None
    artistRoles: list[Role] | None = None
    mixes: Mix | dict[Any, Any] | None = None
