from panflute import Element, Header
from sobiraka.models import Page
from sobiraka.processing.plugin import WeasyTheme
from sobiraka.runtime import RT


class PrintableTheme(WeasyTheme):

    async def process_header(self, header: Header, page: Page) -> tuple[Element, ...]:
        if header.level == 1:
            header.attributes['data-number'] = str(RT[page].number)
        else:
            anchor = RT[page].anchors.by_header(header)
            header.attributes['data-number'] = str(RT[anchor].number)

        return header,
