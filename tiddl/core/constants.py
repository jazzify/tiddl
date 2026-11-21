from pathlib import Path

from tiddl.core.types import (
    ChoiceQualityTrack,
    ChoiceQualityVideo,
    DownloadStatus,
    StreamVideoQuality,
    TrackQuality,
)

### CLI
ENV_KEY = "TIDDL_PATH"
APP_DIR_NAME = ".tiddl"
# Config
CONFIG_FILENAME = "config.toml"
DEFAULT_DOWNLOAD_PATH = Path.home() / "Music" / "tiddl"
# App
VERSION = "v3.4.4"
# Downloader
CHUNK_SIZE = 1024**2
QUALITY_COLOR_TRACK: dict[TrackQuality, str] = {
    "LOW": "[gray]96 kbps",
    "HIGH": "[gray]320 kbps",
    "LOSSLESS": "[cyan]",
    "HI_RES_LOSSLESS": "[yellow]",
}
QUALITY_COLOR_VIDEO: dict[StreamVideoQuality, str] = {
    "LOW": "[gray]360p",
    "MEDIUM": "[cyan]720p",
    "HIGH": "[yellow]1080p",
}
RESULT_MESSAGE: dict[DownloadStatus, str] = {
    DownloadStatus.DOWNLOADED: "[green]Downloaded",
    DownloadStatus.OVERWRITTEN: "[cyan]Overwrited",
}

### Core
QUALITIES_TRACK: dict[ChoiceQualityTrack, TrackQuality] = {
    "low": "LOW",
    "high": "HIGH",
    "lossless": "LOSSLESS",
    "max": "HI_RES_LOSSLESS",
}
QUALITIES_VIDEO: dict[ChoiceQualityVideo, StreamVideoQuality] = {
    "sd": "LOW",
    "hd": "MEDIUM",
    "fhd": "HIGH",
}
# API
API_URL = "https://api.tidal.com/v1"
MAX_RETRIES = 5
RETRY_DELAY = 2
# Client
ENV_KEY = "TIDDL_AUTH"
AUTH_URL = "https://auth.tidal.com/v1/oauth2"
BASE64_THING = "NE4zbjZRMXg5NUxMNUs3cDtvS09YZkpXMzcxY1g2eGFaMFB5aGdHTkJkTkxsQlpkNEFLS1lvdWdNamlrPQ=="
# Parse
DOLBY_CODECS = ["eac3", "ac4"]
