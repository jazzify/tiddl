from logging import getLogger

from tiddl.core.api import TidalAPI
from tiddl.core.exceptions import ApiError
from tiddl.core.metadata import Cover, ItemMetadata
from tiddl.core.models import Album, Config, PlanOptions, TidalResource, Track, Video
from tiddl.core.types import PlanErrorKind
from tiddl.core.utils.format import format_template

from .pagination import paginate
from .plan import (
    CoverJob,
    ErrorSink,
    M3UJob,
    PlanError,
    ResourcePlan,
    WorkItem,
)
from .quality import get_item_quality

log = getLogger(__name__)


def _track_info(item: Track | Video, with_album: bool = False) -> str:
    info = f"Track: {getattr(item, 'title', 'Unknown')} (ID: {item.id})"

    if with_album and hasattr(item, "album") and item.album:
        info += f", Album ID: {item.album.id}"

    return info


class ResourcePlanner:
    """
    Turns a Tidal resource into plans: what to download and where to put it.

    Talks to the API (blocking calls) but never downloads or prints anything.
    """

    def __init__(
        self,
        api: TidalAPI,
        config: Config,
        options: PlanOptions,
        on_error: ErrorSink,
    ) -> None:
        self.api = api
        self.config = config
        self.options = options
        self.on_error = on_error

    def plan(self, resource: TidalResource) -> list[ResourcePlan]:
        match resource.type:
            case "track":
                return [self._track(resource)]
            case "video":
                return [self._video(resource)]
            case "album":
                album = self.api.get_album(album_id=resource.id)
                return [self._album(album)]
            case "mix":
                return [self._mix(resource)]
            case "playlist":
                return [self._playlist(resource)]
            case "artist":
                return self._artist(resource)
            case _:
                raise ValueError(f"Unsupported resource type: {resource.type}")

    def _quality(self, item: Track | Video) -> str:
        return get_item_quality(
            item,
            self.options.track_quality,
            self.options.video_quality,
        )

    def _track(self, resource: TidalResource) -> ResourcePlan:
        config = self.config

        track = self.api.get_track(resource.id)
        album = self.api.get_album(track.album.id)

        cover: Cover | None = None
        save_cover = ("track" in config.cover.allowed) and config.cover.save

        if album.cover and (config.metadata.cover or save_cover):
            cover = Cover(album.cover, size=config.cover.size)

        plan = ResourcePlan(
            items=[
                WorkItem(
                    item=track,
                    file_path=format_template(
                        template=self.options.template or config.templates.track,
                        item=track,
                        album=album,
                        quality=self._quality(track),
                    ),
                    metadata=ItemMetadata(
                        cover=cover,
                        date=str(album.releaseDate),
                        artist=album.artist.name if album.artist else "",
                        # TODO: credits are missing
                    ),
                )
            ]
        )
        if (
            config.cover.save
            and ("track" in config.cover.allowed)
            and track.album.cover
        ):
            plan.cover = CoverJob(
                cover=Cover(track.album.cover, size=config.cover.size),
                directory=self.options.download_path
                / format_template(
                    config.cover.templates.track, item=track, album=album
                ),
            )
        return plan

    def _video(self, resource: TidalResource) -> ResourcePlan:
        video = self.api.get_video(resource.id)
        template = self.options.template or self.config.templates.video

        if "{album" in template and video.album and video.album.id is not None:
            album = self.api.get_album(video.album.id)
        else:
            album = None

        return ResourcePlan(
            items=[
                WorkItem(
                    item=video,
                    file_path=format_template(
                        template=template,
                        item=video,
                        album=album,
                        quality=self._quality(video),
                    ),
                )
            ]
        )

    def _album(self, album: Album, label: str | None = None) -> ResourcePlan:
        config = self.config

        cover: Cover | None = None
        save_cover = ("album" in config.cover.allowed) and config.cover.save

        if album.cover and (config.metadata.cover or save_cover):
            cover = Cover(album.cover, size=config.cover.size)

        album_review = ""

        if config.metadata.album_review:
            try:
                album_review = self.api.get_album_review(
                    album_id=album.id
                ).normalized_text()
            except ApiError as e:
                log.error(e)

        template = self.options.template or config.templates.album
        items: list[WorkItem] = []

        for album_items in paginate(
            lambda offset: self.api.get_album_items_credits(
                album_id=album.id, offset=offset
            )
        ):
            for album_item in album_items.items:
                try:
                    file_path = format_template(
                        template=template,
                        item=album_item.item,
                        album=album,
                        quality=self._quality(album_item.item),
                    )
                except AttributeError as exc:
                    log.error(f"{exc=}")
                    self.on_error(
                        PlanError(
                            PlanErrorKind.TEMPLATE,
                            exc,
                            f"{template=}, {album.id=}, {album_item.item.id=}",
                        )
                    )
                    continue

                items.append(
                    WorkItem(
                        item=album_item.item,
                        file_path=file_path,
                        metadata=ItemMetadata(
                            cover=cover,
                            date=str(album.releaseDate),
                            artist=album.artist.name if album.artist else "",
                            credits=album_item.credits,
                            album_review=album_review,
                        ),
                    )
                )

        plan = ResourcePlan(
            items=items,
            label=label,
            m3u=M3UJob(
                "album",
                format_template(config.m3u.templates.album, album=album, type="album"),
            ),
        )

        if save_cover and cover:
            plan.cover = CoverJob(
                cover=cover,
                directory=self.options.download_path
                / format_template(template=config.cover.templates.album, album=album),
            )

        return plan

    def _mix(self, resource: TidalResource) -> ResourcePlan:
        config = self.config
        template = self.options.template or config.templates.mix
        items: list[WorkItem] = []

        for mix_items in paginate(
            lambda offset: self.api.get_mix_items(resource.id, offset=offset)
        ):
            for mix_item in mix_items.items:
                try:
                    if "{album" in template:
                        album = self.api.get_album(mix_item.item.album.id)
                    else:
                        album = None

                    items.append(
                        WorkItem(
                            item=mix_item.item,
                            file_path=format_template(
                                template=template,
                                item=mix_item.item,
                                album=album,
                                mix_id=resource.id,
                                quality=self._quality(mix_item.item),
                            ),
                        )
                    )
                except Exception as e:  # noqa: BLE001
                    self.on_error(
                        PlanError(PlanErrorKind.ITEM, e, _track_info(mix_item.item))
                    )

        return ResourcePlan(
            items=items,
            m3u=M3UJob(
                "mix",
                format_template(
                    config.m3u.templates.mix, mix_id=resource.id, type="mix"
                ),
            ),
        )

    def _playlist(self, resource: TidalResource) -> ResourcePlan:
        config = self.config
        template = self.options.template or config.templates.playlist
        items: list[WorkItem] = []
        playlist_index = 0
        playlist = self.api.get_playlist(playlist_uuid=resource.id)

        for playlist_items in paginate(
            lambda offset: self.api.get_playlist_items(
                playlist_uuid=resource.id, offset=offset
            )
        ):
            for playlist_item in playlist_items.items:
                playlist_index += 1

                try:
                    if "{album" in template:
                        album = self.api.get_album(playlist_item.item.album.id)
                    else:
                        album = None

                    items.append(
                        WorkItem(
                            item=playlist_item.item,
                            file_path=format_template(
                                template=template,
                                item=playlist_item.item,
                                album=album,
                                playlist=playlist,
                                playlist_index=playlist_index,
                                quality=self._quality(playlist_item.item),
                            ),
                        )
                    )
                except Exception as e:  # noqa: BLE001
                    self.on_error(
                        PlanError(
                            PlanErrorKind.ITEM,
                            e,
                            _track_info(playlist_item.item, with_album=True),
                        )
                    )

        plan = ResourcePlan(
            items=items,
            m3u=M3UJob(
                "playlist",
                format_template(
                    config.m3u.templates.playlist, playlist=playlist, type="playlist"
                ),
            ),
        )

        if (
            config.cover.save
            and ("playlist" in config.cover.allowed)
            and playlist.squareImage
        ):
            plan.cover = CoverJob(
                cover=Cover(playlist.squareImage, size=min(config.cover.size, 1080)),
                directory=self.options.download_path
                / format_template(
                    template=config.cover.templates.playlist, playlist=playlist
                ),
            )

        return plan

    def _artist(self, resource: TidalResource) -> list[ResourcePlan]:
        plans: list[ResourcePlan] = []

        def plan_videos() -> None:
            template = self.options.template or self.config.templates.video
            items: list[WorkItem] = []

            for artist_videos in paginate(
                lambda offset: self.api.get_artist_videos(resource.id, offset=offset)
            ):
                for video in artist_videos.items:
                    try:
                        if "{album" in template and video.album:
                            album = self.api.get_album(video.album.id)
                        else:
                            album = None

                        items.append(
                            WorkItem(
                                item=video,
                                file_path=format_template(
                                    template=template,
                                    item=video,
                                    album=album,
                                    quality=self._quality(video),
                                ),
                            )
                        )
                    except Exception as e:  # noqa: BLE001
                        self.on_error(
                            PlanError(
                                PlanErrorKind.ITEM,
                                e,
                                f"Video: {video.title}, ID: {video.id}",
                            )
                        )

            if items:
                plans.append(ResourcePlan(items=items))

        def plan_albums(singles: bool) -> None:
            for artist_albums in paginate(
                lambda offset: self.api.get_artist_albums(
                    artist_id=resource.id,
                    offset=offset,
                    filter="EPSANDSINGLES" if singles else "ALBUMS",
                )
            ):
                for album in artist_albums.items:
                    label = f"Album: {album.title}, ID: {album.id}"

                    try:
                        plans.append(self._album(album, label=label))
                    except Exception as e:  # noqa: BLE001
                        self.on_error(PlanError(PlanErrorKind.ITEM, e, label))

        if self.options.videos_filter != "none":
            plan_videos()

        if self.options.videos_filter != "only":
            if self.options.singles_filter == "include":
                # two different requests: regular albums, then EPs and singles
                plan_albums(False)
                plan_albums(True)
            else:
                plan_albums(self.options.singles_filter == "only")

        return plans
