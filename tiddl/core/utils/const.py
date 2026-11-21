from tiddl.core.types import (
    ChoiceQualityTrack,
    ChoiceQualityVideo,
    StreamVideoQuality,
    TrackQuality,
)

track_qualities: dict[ChoiceQualityTrack, TrackQuality] = {
    "low": "LOW",
    "high": "HIGH",
    "lossless": "LOSSLESS",
    "max": "HI_RES_LOSSLESS",
}

video_qualities: dict[ChoiceQualityVideo, StreamVideoQuality] = {
    "sd": "LOW",
    "hd": "MEDIUM",
    "fhd": "HIGH",
}
