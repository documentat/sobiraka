from typing import Iterable

from sobiraka.models import Anchor, Page, Volume
from sobiraka.runtime import RT
from sobiraka.utils import RootNumber, TocNumber


def numerate(volume: Volume):
    _numerate_page(volume.root_page, RootNumber())


def _numerate_page(page: Page, counter: TocNumber) -> TocNumber:
    """
    First, the `page` will consume a number from the given `counter`,
    then it will numerate its anchors and its child pages,
    passing a next-level counter to them.

    If `skip_current_level` is True, the page itself will not be numerated,
    but its anchors and children will be.
    """

    # Skip if has to be skipped
    if RT[page].skip_numeration:
        return counter

    # Numerate the page itself
    # Skip this for a root page
    if not page.is_root():
        counter = RT[page].number = counter.increased()

    # Numerate the page's anchors and children
    subcounter = counter.with_new_zero()
    subcounter = _numerate_anchors(RT[page].anchors, subcounter)
    for child in page.children:
        subcounter = _numerate_page(child, subcounter)

    return counter


def _numerate_anchors(anchors: Iterable[Anchor], counter: TocNumber) -> TocNumber:
    """
    Numerate the given `anchors` by consuming the given `counter`.
    It is assumed that the `counter` currently ends with a zero,
    which will be replaced with one or more numbers for each numerated anchor.
    """
    original_level = len(counter)
    skipping_lower_than = None

    for anchor in anchors:
        if skipping_lower_than is not None:
            # For subsections of a skipped section, do nothing
            # Once we come back to the previous level or higher, reset the variable
            if anchor.level > skipping_lower_than:
                continue
            skipping_lower_than = None

        if RT[anchor].skip_numeration:
            skipping_lower_than = anchor.level
            continue

        counter = RT[anchor].number = counter.increased_at(original_level + anchor.level - 2)

    return counter
