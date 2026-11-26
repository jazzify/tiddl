import asyncio
from collections.abc import Iterable
from pathlib import Path

from tiddl.core.models.plan import ResourcePlan
from tiddl.core.models.settings import Config
from tiddl.core.models.tidal.resources import TidalResource
from tiddl.core.protocols import FailureSink
from tiddl.core.utils.m3u import save_m3u

from .pipeline import ItemPipeline
from .planner import ResourcePlanner


async def run_plan(
    plan: ResourcePlan,
    pipeline: ItemPipeline,
    m3u_settings: Config.M3UConfig,
    download_path: Path,
) -> None:
    """Download all items of a plan at once, then save its m3u and cover."""

    tracks_with_path = await asyncio.gather(
        *(
            pipeline.run(
                item=work.item,
                file_path=work.file_path,
                track_metadata=work.metadata,
            )
            for work in plan.items
        )
    )

    if plan.m3u:
        save_m3u(
            settings=m3u_settings,
            download_path=download_path,
            resource_type=plan.m3u.resource_type,
            filename=plan.m3u.filename,
            tracks_with_path=tracks_with_path,
        )

    if plan.cover:
        plan.cover.cover.save_to_directory(path=plan.cover.directory)


class DownloadRunner:
    """Plans resources and runs their plans, reporting failures to a sink."""

    def __init__(
        self,
        planner: ResourcePlanner,
        pipeline: ItemPipeline,
        m3u_settings: Config.M3UConfig,
        download_path: Path,
        on_error: FailureSink,
    ) -> None:
        self.planner = planner
        self.pipeline = pipeline
        self.m3u_settings = m3u_settings
        self.download_path = download_path
        self.on_error = on_error

    async def run(self, resources: Iterable[TidalResource]) -> None:
        await asyncio.gather(*(self._run_resource(r) for r in resources))

    async def _run_resource(self, resource: TidalResource) -> None:
        try:
            plans = self.planner.plan(resource)
            await asyncio.gather(*(self._run_plan(plan) for plan in plans))
        except Exception as e:  # noqa: BLE001
            self.on_error(e, str(resource))

    async def _run_plan(self, plan: ResourcePlan) -> None:
        if plan.label is None:
            await self._execute(plan)
            return

        # labeled plans (albums of an artist) fail on their own
        try:
            await self._execute(plan)
        except Exception as e:  # noqa: BLE001
            self.on_error(e, plan.label)

    async def _execute(self, plan: ResourcePlan) -> None:
        await run_plan(plan, self.pipeline, self.m3u_settings, self.download_path)
