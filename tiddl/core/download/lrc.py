from logging import getLogger
from pathlib import Path

from tiddl.core.models.tidal.items import Track

log = getLogger(__name__)


def write_lrc_file(track: Track, lyrics: str, file_path: Path) -> None:
    if not lyrics.strip():
        return

    try:
        with open(file_path.with_suffix(".lrc"), "w", encoding="utf-8") as f:
            f.write(lyrics)
    except FileExistsError as e:
        log.error(
            f"[DOWNLOAD_CALLBACK] Failed to write LRC file for track {track.title} (ID: {track.id}): {e}"
        )
