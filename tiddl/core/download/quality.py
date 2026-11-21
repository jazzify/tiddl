from tiddl.core.models import Track, Video
from tiddl.core.types import ChoiceQualityTrack, ChoiceQualityVideo


def get_item_quality(
    item: Track | Video,
    track_quality: ChoiceQualityTrack,
    video_quality: ChoiceQualityVideo,
) -> str:
    def predict_item_quality() -> ChoiceQualityTrack | ChoiceQualityVideo:
        if isinstance(item, Track):
            if track_quality in ["low", "high"]:
                return track_quality
            elif track_quality == "max" and (
                "HIRES_LOSSLESS" not in item.mediaMetadata.tags
            ):
                return "high"
            return track_quality
        elif isinstance(item, Video):
            # TODO: add missing Video.quality literals so this function can work properly
            return video_quality

    return predict_item_quality().upper()
