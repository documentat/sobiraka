from asyncio import create_task, gather

from panflute import Link, Str

from sobiraka.models import Page, PageHref, UnknownPageHref
from sobiraka.models.error import BadLinkError
from sobiraka.utils import save_debug_json


async def process2(page: Page):
    await page.processed1.wait()
    await gather(*page.process2_tasks)
    save_debug_json('s2', page)


async def process2_link(page: Page, link: Link, href: PageHref):
    await href.target.processed1.wait()

    link.url = '#' + href.target.id
    link.title = href.target.title

    if href.anchor:
        try:
            link.url += '--' + href.anchor
            link.title = href.target.anchors[href.anchor]
        except KeyError:
            href = BadLinkError(f'{href.target.relative_path}#{href.anchor}')
            page.errors.add(href)