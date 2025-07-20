import json
from asyncio.subprocess import Process, create_subprocess_exec
from os.path import dirname
from subprocess import PIPE
from textwrap import dedent
from typing import Iterable

from panflute import Element, Header, stringify
from typing_extensions import override

from sobiraka.models import Page, PageHref, Volume
from sobiraka.models.config import Config_Search_LinkTarget
from sobiraka.processing.html import HeadJsCode, HeadJsFile, HeadTag
from sobiraka.processing.txt import PlainTextDispatcher
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath, RelativePath
from .searchindexer import SearchIndexer


class PagefindIndexer(SearchIndexer, PlainTextDispatcher):
    """
    - Pagefind website: https://pagefind.app/
    - Pagefind JS API: https://pagefind.app/docs/node-api/
    """

    node_process: Process = None

    def default_index_path(self, volume: Volume) -> RelativePath:
        return RelativePath('_pagefind')

    async def initialize(self):
        self.node_process = await create_subprocess_exec('node',
                                                         f'{dirname(__file__)}/run_pagefind.js',
                                                         '--indexPath', str(self.index_path),
                                                         stdin=PIPE)

    def _add_record(self, *, url: str, title: str, content: str):
        self.node_process.stdin.write(json.dumps(dict(
            url=url,
            content=content,
            language=self.volume.lang or 'en',
            meta=dict(title=title or ''),
        )).encode('utf-8') + b'\n')

    async def add_page(self, page: Page):
        await super().process_doc(RT[page].doc, page)

        tm = self.tm[page]
        url = str(self.builder.make_internal_url(PageHref(page)))
        title = page.meta.title

        match self.search_config.link_target:
            case Config_Search_LinkTarget.H1:
                self._add_record(url=url, title=title, content=tm.text)

            case _:
                for anchor, fragment in tm.sections_up_to_level(self.search_config.link_target.level).items():
                    if anchor is None:
                        self._add_record(url=url, title=title, content=fragment.text)
                    else:
                        self._add_record(url=f'{url}#{anchor.identifier}',
                                         title=f'{title} » {stringify(anchor.header)}',
                                         content=fragment.text)

    async def finalize(self):
        self.node_process.stdin.close()
        await self.node_process.wait()
        assert self.node_process.returncode == 0, 'Pagefind failure'

    def results(self) -> set[AbsolutePath]:
        return set(self.index_path.walk_all())

    def head_tags(self) -> Iterable[HeadTag]:
        yield HeadJsFile(self.index_path_relative / 'pagefind-ui.js')
        if self.search_config.generate_js:
            yield HeadJsCode(dedent(f'''
                window.addEventListener("DOMContentLoaded", (event) => {{
                    new PagefindUI({{
                        element: {self.search_config.container!r},
                        baseUrl: new URL("../%ROOT%", location),
                        translations: {self.search_config.translations.to_json()},
                    }})
                }})
            ''').strip())

    @override
    async def must_skip(self, elem: Element, page: Page):
        return isinstance(elem, self.search_config.skip_elements)

    async def process_header(self, header: Header, page: Page):
        if header.level != 1:
            await super().process_header(header, page)
