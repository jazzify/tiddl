from typing import Literal

from pydantic import BaseModel

from tiddl.core.types import StreamVideoQuality, TrackQuality


class Favorites(BaseModel):
    PLAYLIST: list[str]
    ALBUM: list[str]
    VIDEO: list[str]
    TRACK: list[str]
    ARTIST: list[str]


class SessionResponse(BaseModel):
    class Client(BaseModel):
        id: int
        name: str
        authorizedForOffline: bool
        authorizedForOfflineDate: str | None

    sessionId: str
    userId: int
    countryCode: str
    channelId: int
    partnerId: int
    client: Client


class TrackStream(BaseModel):
    trackId: int
    assetPresentation: Literal["FULL"]
    audioMode: Literal["STEREO", "DOLBY_ATMOS"]
    audioQuality: TrackQuality
    manifestMimeType: Literal["application/dash+xml", "application/vnd.tidal.bts"]
    manifestHash: str
    manifest: str
    albumReplayGain: float | None = None
    albumPeakAmplitude: float | None = None
    trackReplayGain: float | None = None
    trackPeakAmplitude: float | None = None
    bitDepth: int | None = None
    sampleRate: int | None = None


class VideoStream(BaseModel):
    videoId: int
    streamType: Literal["ON_DEMAND"]
    assetPresentation: Literal["FULL"]
    videoQuality: StreamVideoQuality
    # streamingSessionId: str  # only in web?
    manifestMimeType: Literal["application/dash+xml", "application/vnd.tidal.emu"]
    manifestHash: str
    manifest: str


# It seemed like the search API doesn't return `artist.type`, so this is used instead of resources.Artist for search results to avoid validation errors.
# FIXME: This can be discarded if we are okay with making the `type` field optional in resources.Artist, but I don't think it's my decision to make lol


class TrackLyrics(BaseModel):
    isRightToLeft: bool
    lyrics: str
    lyricsProvider: str
    providerCommontrackId: str
    providerLyricsId: str
    subtitles: str
    trackId: int


class AuthResponse(BaseModel):
    class User(BaseModel):
        userId: int
        email: str
        countryCode: str
        fullName: str | None
        firstName: str | None
        lastName: str | None
        nickname: str | None
        username: str
        address: str | None
        city: str | None
        postalcode: str | None
        usState: str | None
        phoneNumber: str | None
        birthday: int | str | None
        channelId: int
        parentId: int
        acceptedEULA: bool
        created: int | str
        updated: int | str
        accountLinkCreated: bool
        emailVerified: bool
        newUser: bool
        facebookUid: int | None = None
        appleUid: str | None = None
        googleUid: str | None = None

    user: User
    scope: str
    clientName: str
    token_type: str
    access_token: str
    expires_in: int
    user_id: int


class AuthResponseWithRefresh(AuthResponse):
    refresh_token: str


class AuthDeviceResponse(BaseModel):
    deviceCode: str
    userCode: str
    verificationUri: str
    verificationUriComplete: str
    expiresIn: int
    interval: int
