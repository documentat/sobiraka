import re
from functools import singledispatch
from pathlib import Path

from panflute import Element, Header, Image, Link, ListContainer, stringify

from sobiraka.building.processing2 import process2_link
from sobiraka.models import Book, PageHref, Href, Page, UrlHref
from sobiraka.models.error import BadLinkError
from sobiraka.models.href import PageHref, UnknownPageHref
from sobiraka.utils import LatexBlock, save_debug_json


async def process1(page: Page):
    await page.loaded.wait()
    _process_element(page.doc, page, page.book)
    save_debug_json('s1', page)


@singledispatch
def _process_element(elem: Element, page: Page, book: Book) -> None | Element | tuple[Element, ...]:
    try:
        assert isinstance(elem.content, ListContainer)
    except (AttributeError, AssertionError):
        return

    i = 0
    while i < len(elem.content):
        result = _process_element(elem.content[i], page, book)
        match result:
            case None:
                pass
            case Element():
                elem.content[i] = result
            case tuple():
                elem.content[i:i + 1] = result
                i += len(result) - 1
            case _:
                raise TypeError(result)
        i += 1
    return elem


@_process_element.register
def _(header: Header, page: Page, _: Book):
    nodes = [header]

    if not header.identifier:
        header.identifier = stringify(header).lower().replace(' ', '-')

    page.anchors.setdefault(header.identifier, []).append(stringify(header))

    if header.level == 1:
        full_id = page.id
    else:
        full_id = page.id + '--' + header.identifier

    if header.level == 1 and page.title is None:
        page.title = stringify(header)

    nodes.insert(0, LatexBlock(fr'''
        \hypertarget{{{full_id}}}{{}}
        \bookmark[level={page.level},dest={full_id}]{{{stringify(header)}}}
    '''))

    if page.antilevel > 1:
        nodes.insert(0, LatexBlock(r'\newpage'))
        nodes.append(LatexBlock(r'\newpage'))

    return tuple(nodes)


@_process_element.register
def _(image: Image, _: Page, book: Book):
    image.url = str(book.root / '_images' / image.url)


@_process_element.register
def _(link: Link, page: Page, book: Book):
    href: Href

    if re.match(r'^\w+:', link.url):
        href = UrlHref(link.url)

    else:
        m = re.match(r'^ ([^\#]+)? (?: \#(.+) )?', link.url, flags=re.VERBOSE)
        target, anchor = m.groups()
        target = target or None
        anchor = anchor or None

        if target is None:
            href = PageHref(page, anchor)
        else:
            target_path = (page.path.parent / Path(target)).resolve()
            try:
                target_page = book.pages_by_path[target_path]
                href = PageHref(target_page, anchor)
            except KeyError:
                href = UnknownPageHref(target, anchor)
                page.errors.add(BadLinkError(target))

    if isinstance(href, PageHref):
        page.process2_tasks.append(process2_link(page, link, href))