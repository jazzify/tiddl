from logging import getLogger
from pathlib import Path

from tiddl.core.types import TrackQuality

log = getLogger(__name__)


def get_existing_track_filename(
    track_quality: TrackQuality, download_quality: TrackQuality, file_name: Path
) -> Path:
    """
    Predict track extension.
    """

    FLAC_QUALITIES: list[TrackQuality] = ["LOSSLESS", "HI_RES_LOSSLESS"]

    if download_quality in FLAC_QUALITIES and track_quality in FLAC_QUALITIES:
        extension = ".flac"
    else:
        extension = ".m4a"

    full_file_name = file_name.with_suffix(extension)

    log.debug(f"{track_quality=}, {download_quality=}, {file_name=}, {full_file_name=}")

    return full_file_name


def resolve_existing_path_case(base_path: Path, relative_path: Path) -> Path:
    """
    Return base_path / relative_path, reusing existing path component casing.
    """

    if relative_path.is_absolute():
        raise ValueError("relative_path must not be absolute")

    resolved_path = base_path

    for part in relative_path.parts:
        if part in ("", "."):
            continue

        existing_part = find_existing_child_case(resolved_path, part)
        resolved_path = resolved_path / (existing_part or part)

    return resolved_path


def find_existing_child_case(parent: Path, name: str) -> str | None:
    if not parent.is_dir():
        return None

    casefolded_name = name.casefold()
    fallback: str | None = None

    for child in parent.iterdir():
        if child.name == name:
            return child.name

        if fallback is None and child.name.casefold() == casefolded_name:
            fallback = child.name

    return fallback
