from rich.live import Live

from tiddl.cli.ctx import ContextObject
from tiddl.core.download.downloader import Downloader
from tiddl.core.download.pipeline import ItemPipeline
from tiddl.core.download.planner import ResourcePlanner
from tiddl.core.download.runner import DownloadRunner
from tiddl.core.models.downloader import (
    DownloadOptions,
    ItemPipelineOptions,
    PlanOptions,
)
from tiddl.core.models.settings import Config

from .output import ErrorReporter, RichOutput


async def download_resources(
    obj: ContextObject,
    config: Config,
    download_options: DownloadOptions,
    plan_options: PlanOptions,
    pipeline_options: ItemPipelineOptions,
    raise_errors: bool,
) -> None:
    """Download `obj.resources`, showing progress and errors in the console."""

    rich_output = RichOutput(obj.console)
    error_reporter = ErrorReporter(obj.console, raise_errors)
    runner = DownloadRunner(
        planner=ResourcePlanner(
            api=obj.api,
            config=config,
            options=plan_options,
            on_error=error_reporter.plan_error,
        ),
        pipeline=ItemPipeline(
            api=obj.api,
            downloader=Downloader(
                api=obj.api,
                options=download_options,
                reporter=rich_output,
            ),
            options=pipeline_options,
            reporter=rich_output,
        ),
        m3u_settings=config.m3u,
        download_path=plan_options.download_path,
        on_error=error_reporter.failure,
    )

    with Live(
        rich_output.group,
        refresh_per_second=10,
        console=obj.console,
        transient=True,
    ):
        await runner.run(obj.resources)

    rich_output.show_stats()
