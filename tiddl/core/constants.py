import os
from pathlib import Path

from tiddl.core.types import (
    ChoiceQualityTrack,
    ChoiceQualityVideo,
    DownloadStatus,
    StreamVideoQuality,
    TrackQuality,
)

### CLI
ENV_APP_PATH = "TIDDL_PATH"
APP_DIR_NAME = ".tiddl"
# Config
CONFIG_FILENAME = "config.toml"
DEFAULT_DOWNLOAD_PATH = Path.home() / "Music" / "tiddl"
# App
VERSION = "v3.4.4"
# Downloader
CHUNK_SIZE = 1024**2
QUALITY_COLOR_TRACK: dict[TrackQuality, str] = {
    "LOW": "[text]96 kbps",
    "HIGH": "[text]320 kbps",
    "LOSSLESS": "[info]",
    "HI_RES_LOSSLESS": "[warning]",
}
QUALITY_COLOR_VIDEO: dict[StreamVideoQuality, str] = {
    "LOW": "[text]360p",
    "MEDIUM": "[info]720p",
    "HIGH": "[warning]1080p",
}
RESULT_MESSAGE: dict[DownloadStatus, str] = {
    DownloadStatus.DOWNLOADED: "[success]Downloaded",
    DownloadStatus.OVERWRITTEN: "[warning]Overwrited",
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
ENV_AUTH = "TIDDL_AUTH"
AUTH_URL = "https://auth.tidal.com/v1/oauth2"
BASE64_THING = "NE4zbjZRMXg5NUxMNUs3cDtvS09YZkpXMzcxY1g2eGFaMFB5aGdHTkJkTkxsQlpkNEFLS1lvdWdNamlrPQ=="
# Parse
DOLBY_CODECS = ["eac3", "ac4"]
# Auth
FILE_WRITE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
FILE_WRITE_MODE = 0o600  # Owner: read & write; Group & Others: no access
