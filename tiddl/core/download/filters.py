from tiddl.core.models.tidal.items import Track, Video
from tiddl.core.types import ChoiceFilterAtmos, ChoiceFilterVideos


def video_filter_skips(item: Track | Video, mode: ChoiceFilterVideos) -> bool:
    return (isinstance(item, Video) and mode == "none") or (
        isinstance(item, Track) and mode == "only"
    )


def atmos_filter_skips(audio_mode: str, mode: ChoiceFilterAtmos) -> bool:
    return (mode == "none" and audio_mode == "DOLBY_ATMOS") or (
        mode == "only" and audio_mode == "STEREO"
    )
