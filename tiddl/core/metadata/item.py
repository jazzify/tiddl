from dataclasses import dataclass, field

from tiddl.core.metadata.cover import Cover
from tiddl.core.models import AlbumItemsCredits


@dataclass
class ItemMetadata:
    date: str = ""
    artist: str = ""
    credits: list[AlbumItemsCredits.ItemWithCredits.CreditsEntry] = field(
        default_factory=list
    )
    cover: Cover | None = None
    album_review: str = ""
