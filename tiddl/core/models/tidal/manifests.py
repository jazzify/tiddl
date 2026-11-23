from pydantic import BaseModel


class TrackManifest(BaseModel):
    mimeType: str
    codecs: str
    encryptionType: str
    urls: list[str]


class VideoManifest(BaseModel):
    mimeType: str
    urls: list[str]
