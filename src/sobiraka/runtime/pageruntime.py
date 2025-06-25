from dataclasses import dataclass, field

from panflute import Doc, Image, Link

from sobiraka.models import Anchors, Href
from sobiraka.utils import TocNumber, Unnumbered


@dataclass
class PageRuntime:
    # pylint: disable=too-many-instance-attributes

    doc: Doc = None
    """
    The document tree, as parsed by `Pandoc <https://pandoc.org/>`_ 
    and `Panflute <http://scorreia.com/software/panflute/>`_.
    
    Do not rely on the value for page here until `load()` is awaited for that page.
    """

    title: str = None
    """Page title.
    
    Do not rely on the value for page here until `do_process1()` is awaited for that page.
    """

    number: TocNumber = Unnumbered()
    """
    Number of the page in the global TOC.
    """

    skip_numeration: bool = False
    """
    If true, `numerate()` will not set numbers for this page, and its anchors and child pages.
    """

    links: set[Href] = field(default_factory=set)
    """All links present on the page, both internal and external.
    
    Do not rely on the value for page here until `do_process1()` is awaited for that page."""

    anchors: Anchors = field(default_factory=Anchors)

    bytes: bytes = None

    converted_image_urls: list[tuple[Image, str]] = field(default_factory=list)
    links_that_follow_images: list[tuple[Image, Link]] = field(default_factory=list)
