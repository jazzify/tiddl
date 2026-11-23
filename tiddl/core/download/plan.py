from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from tiddl.core.metadata import Cover, ItemMetadata
from tiddl.core.models import Track, Video
from tiddl.core.types import ChoiceResourceM3U, PlanErrorKind


@dataclass
class WorkItem:
    """One track or video to download, with everything needed to tag it."""

    item: Track | Video
    file_path: str
    metadata: ItemMetadata = field(default_factory=ItemMetadata)


@dataclass(frozen=True)
class M3UJob:
    resource_type: ChoiceResourceM3U
    filename: str


@dataclass(frozen=True)
class CoverJob:
    cover: Cover
    directory: Path


@dataclass
class ResourcePlan:
    """What to do for a resource: items to download, then optional extras."""

    items: list[WorkItem] = field(default_factory=list)
    m3u: M3UJob | None = None
    cover: CoverJob | None = None
    # when set, a failure of this plan is reported under this label
    # and must not abort sibling plans (e.g. albums of an artist)
    label: str | None = None


@dataclass(frozen=True)
class PlanError:
    kind: PlanErrorKind
    exc: Exception
    # what was being planned, ready to be shown to the user
    context: str


# Called for every error that does not stop planning. The sink decides what
# to do: print it, log it, or re-raise `error.exc` to abort planning.
ErrorSink = Callable[[PlanError], None]
