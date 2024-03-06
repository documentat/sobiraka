from os.path import relpath

from sobiraka.models import Page, PageHref
from sobiraka.processing.abstract import ProjectProcessor


class FakeProcessor(ProjectProcessor):
    def make_internal_url(self, href: PageHref, *, page: Page) -> str:
        if page is href.target:
            return ''
        if page is None:
            return str(href.target.path_in_volume)
        return relpath(href.target.path_in_volume, start=page.path_in_volume.parent)
