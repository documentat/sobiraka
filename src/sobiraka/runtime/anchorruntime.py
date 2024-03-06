from dataclasses import dataclass

from sobiraka.utils import TocNumber, Unnumbered


@dataclass
class AnchorRuntime:
    number: TocNumber = Unnumbered()
    """
    Number of the header in the global TOC.
    """

    skip_numeration: bool = False
    """
    If true, `numerate()` will not set numbers for this anchors and its child anchors.
    """
