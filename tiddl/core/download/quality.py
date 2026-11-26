from tiddl.core.models.tidal.items import Track, Video
from tiddl.core.types import ChoiceQualityTrack, ChoiceQualityVideo


def get_item_quality(
    item: Track | Video,
    track_quality: ChoiceQualityTrack,
    video_quality: ChoiceQualityVideo,
) -> str:
    if isinstance(item, Track):
        if track_quality == "max" and "HIRES_LOSSLESS" not in item.mediaMetadata.tags:
            return "lossless".upper()
        return track_quality.upper()
    return video_quality.upper()
