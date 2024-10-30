from panflute import Element, Header
from sobiraka.models import Page
from sobiraka.processing.plugin import WeasyPrintTheme
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath


class PrintableTheme(WeasyPrintTheme):
    def __init__(self, theme_dir: AbsolutePath):
        super().__init__(theme_dir)
        self.sass_files['sass/printable.scss'] = 'printable.css'

    async def process_header(self, header: Header, page: Page) -> tuple[Element, ...]:
        if header.level == 1:
            header.attributes['data-number'] = str(RT[page].number)
        else:
            anchor = RT[page].anchors.by_header(header)
            header.attributes['data-number'] = str(RT[anchor].number)

        return header,
