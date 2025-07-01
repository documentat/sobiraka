from sobiraka.models import Page, PageHref, Volume
from sobiraka.processing.abstract import Processor, Theme, ThemeableProjectBuilder


class FakeBuilder(ThemeableProjectBuilder):
    def init_processor(self, volume: Volume) -> Processor:
        return Processor(self)

    def init_theme(self, volume: Volume) -> Theme:
        return Theme(volume.config.web.theme.path)

    def additional_variables(self) -> dict:
        return {}

    async def run(self):
        await self.waiter.wait_all()

    def make_internal_url(self, href: PageHref, *, page: Page = None) -> str:
        result = href.target.location.as_relative_path_str(
            start=page and page.location,
            suffix=href.target.source.path_in_project.suffix,
            index_file_name='',
        )
        if href.anchor:
            result += '#' + href.anchor
        return result
