from os.path import relpath

from sobiraka.models import Page, PageHref, Volume
from sobiraka.processing.abstract import Processor, ProjectBuilder, Theme
from sobiraka.processing.abstract.builder import P, T


class FakeBuilder(ProjectBuilder):
    def init_processor(self, volume: Volume) -> P:
        return Processor(self)

    def init_theme(self, volume: Volume) -> T:
        return Theme(volume.config.web.theme)

    def run(self):
        raise NotImplementedError

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
