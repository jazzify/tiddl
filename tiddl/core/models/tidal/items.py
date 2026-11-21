from typing import Literal

from pydantic import BaseModel

from tiddl.core.types import ItemType

from .resources import (
    Album,
    Playlist,
    Track,
    Video,
)


class Items(BaseModel):
    limit: int
    offset: int
    totalNumberOfItems: int


class ArtistAlbumsItems(Items):
    items: list[Album]


class ArtistVideosItems(Items):
    items: list[Video]


class AlbumItems(Items):
    class VideoItem(BaseModel):
        item: Video
        type: ItemType = "video"

    class TrackItem(BaseModel):
        item: Track
        type: ItemType = "track"

    items: list[TrackItem | VideoItem]


class AlbumItemsCredits(Items):
    class ItemWithCredits(BaseModel):
        class CreditsEntry(BaseModel):
            class Contributor(BaseModel):
                name: str
                id: int | None = None

            type: str
            contributors: list[Contributor]

        credits: list[CreditsEntry]

    class VideoItem(ItemWithCredits):
        item: Video
        type: ItemType = "video"

    class TrackItem(ItemWithCredits):
        item: Track
        type: ItemType = "track"

    items: list[TrackItem | VideoItem]


class PlaylistItems(Items):
    class PlaylistVideoItem(BaseModel):
        class PlaylistVideo(Video):
            dateAdded: str
            index: int
            itemUuid: str

        item: PlaylistVideo
        type: ItemType = "video"
        cut: None

    class PlaylistTrackItem(BaseModel):
        class PlaylistTrack(Track):
            dateAdded: str
            index: int
            itemUuid: str
            # playlist tracks albums have releasedate,
            # but tracks alone do not lol

        item: PlaylistTrack
        type: ItemType = "track"
        cut: None

    items: list[PlaylistTrackItem | PlaylistVideoItem]


class MixItems(Items):
    class MixItem(BaseModel):
        item: Track
        type: ItemType = "track"

    items: list[MixItem]


class SearchArtist(BaseModel):  # search-specific, fewer required fields
    id: int
    name: str
    type: Literal["MAIN", "FEATURED"] | None = None
    url: str | None = None
    picture: str | None = None
    popularity: int | None = None


class Search(BaseModel):
    class Artists(Items):
        items: list[SearchArtist]  # ← uses the inner model, not resources.Artist

    class Albums(Items):
        items: list[Album]

    class Playlists(Items):
        items: list[Playlist]

    class Tracks(Items):
        items: list[Track]

    class Videos(Items):
        items: list[Video]

    class TopHit(BaseModel):
        value: SearchArtist | Track | Playlist | Album
        type: Literal["ARTISTS", "TRACKS", "PLAYLISTS", "ALBUMS"]

    artists: Artists
    albums: Albums
    playlists: Playlists
    tracks: Tracks
    videos: Videos
    topHit: TopHit | None = None
