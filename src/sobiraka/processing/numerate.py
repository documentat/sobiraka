from typing import Iterable

from sobiraka.models import Page
from sobiraka.runtime import RT
from sobiraka.utils import SKIP_NUMERATION, TocNumber, Unnumbered


def numerate(pages: Iterable[Page], counter: TocNumber = TocNumber(0)):
    for page in pages:
        # Skip if has to be skipped
        if RT[page].number == SKIP_NUMERATION:
            RT[page].number = Unnumbered()
            for anchor in RT[page].anchors:
                RT[anchor].number = Unnumbered()
            continue

        # Numerate the page itself
        counter = counter.increased()
        RT[page].number = counter

        # Numerate the page's anchors
        subcounter = TocNumber(*counter, 0)
        skipping_lower_than = None
        for anchor in RT[page].anchors:

            if skipping_lower_than is not None:
                # For subsections of a skipped section, do nothing
                # Once we come back to the previous level or higher, reset the variable
                if anchor.level > skipping_lower_than:
                    continue
                skipping_lower_than = None

            if RT[anchor].number == SKIP_NUMERATION:
                RT[anchor].number = Unnumbered()
                skipping_lower_than = anchor.level
                continue

            subcounter = subcounter.increased_at(len(counter) + anchor.level - 1)
            RT[anchor].number = subcounter

        # Numerate the page's children
        numerate(page.children, subcounter)
