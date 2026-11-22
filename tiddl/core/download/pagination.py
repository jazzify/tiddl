from collections.abc import Callable, Iterator

from tiddl.core.models.tidal.items import Items


def paginate[P: Items](fetch: Callable[[int], P]) -> Iterator[P]:
    """
    Yield pages from `fetch(offset)` until `totalNumberOfItems` is reached.

    Fetching is lazy: the next page is requested only when the caller
    asks for it.
    """

    offset = 0

    while True:
        page = fetch(offset)

        yield page

        offset += page.limit

        if page.limit <= 0 or offset >= page.totalNumberOfItems:
            return
