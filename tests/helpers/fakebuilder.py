from os.path import relpath

from sobiraka.models import Page, PageHref
from sobiraka.processing.abstract import ProjectBuilder


class FakeBuilder(ProjectBuilder):
    def make_internal_url(self, href: PageHref, *, page: Page = None) -> str:
        result = ''
        if href.target is not page:
            if page is not None:
                result += relpath(href.target.path_in_volume, start=page.path_in_volume.parent)
            else:
                result += str(href.target.path_in_volume)
        if href.anchor is not None:
            result += '#' + href.anchor
        return result