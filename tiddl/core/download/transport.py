import shutil
from collections.abc import Callable
from pathlib import Path
from tempfile import NamedTemporaryFile

import aiofiles
import aiohttp

from tiddl.core.constants import CHUNK_SIZE


async def stream_to_file(
    urls: list[str],
    destination: Path,
    on_progress: Callable[[int], None],
) -> None:
    """
    Download `urls` one after another into `destination`.

    Data goes to a temp file next to the destination first, so a failed
    download never leaves a half-written file under the final name.
    """

    # TODO shouldnt session be reused instead of
    # creating new one on every download?

    with NamedTemporaryFile("wb", delete=False, dir=destination.parent) as tmp:
        tmp_path = Path(tmp.name)

    try:
        async with (
            aiohttp.ClientSession(trust_env=True) as session,
            aiofiles.open(tmp_path, "wb") as f,
        ):
            for url in urls:
                async with session.get(url) as resp:
                    async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                        await f.write(chunk)
                        on_progress(len(chunk))

        shutil.move(tmp_path, destination)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise

    try:
        destination.chmod(0o644)
    except OSError:
        pass
