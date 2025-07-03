from __future__ import annotations

from typing import TYPE_CHECKING

from sobiraka.utils import Location
from .page import Page, PageMeta
from ..syntax import Syntax

if TYPE_CHECKING:
    from sobiraka.models import Source


class IndexPage(Page):
    """
    A page that is created from index.md or a similar file in a directory.
    The only difference from a normal Page is in how the Location is created.
    """

    def __init__(self, source: Source, location: Location, syntax: Syntax, meta: PageMeta, text: str):
        super().__init__(source, location, syntax, meta, text)
        self.location = self.location.parent
        if self.location.is_root:
            self.parent = None
