from asyncio.subprocess import Process, create_subprocess_exec
from importlib.resources import files
from subprocess import PIPE
from textwrap import dedent
from typing import Sequence

from panflute import Element, Header, stringify
from typing_extensions import override

from sobiraka.models import Page, PageHref, Volume
from sobiraka.models.config import Config_Search_LinkTarget
from sobiraka.processing.txt import PlainTextDispatcher
from sobiraka.processing.web import HeadJsCode, HeadJsFile, HeadTag
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath, RelativePath
from .searchindexer import SearchIndexer


class PagefindIndexer(SearchIndexer, PlainTextDispatcher):
    """
    - Pagefind website: https://pagefind.app/
    - Pagefind JS API: https://pagefind.app/docs/node-api/
    """

    # pylint: disable=abstract-method

    node_process: Process = None

    def default_index_path(self, volume: Volume) -> RelativePath:
        return RelativePath('_pagefind')

    def execute_js(self, code: str):
        self.node_process.stdin.write(code.encode('utf-8'))

    async def initialize(self):
        self.node_process = await create_subprocess_exec('node', '--input-type', 'module', stdin=PIPE, stdout=PIPE,
                                                         cwd=files('sobiraka'))
        self.execute_js('''
            import * as fs from 'fs';
            import * as path from 'path';
            import * as pagefind from 'pagefind';
            
            const { index } = await pagefind.createIndex();
        ''')

    def _add_record(self, *, url: str, title: str, content: str):
        self.execute_js(f'''
            var {{ errors, file }} = await index.addCustomRecord({{
                url: {url!r},
                content: {content!r},
                language: {self.volume.lang or 'en'!r},
                meta: {{
                    title: {repr(title) if title else "''"},
                }},
            }});
        ''')

    async def add_page(self, page: Page):
        await super().process_doc(RT[page].doc, page)

        tm = self.tm[page]
        url = str(self.builder.make_internal_url(PageHref(page)))
        title = RT[page].title

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
        (self.index_path / 'fragment').mkdir(parents=True, exist_ok=True)
        (self.index_path / 'index').mkdir(parents=True, exist_ok=True)
        self.execute_js(f'''
            var {{ errors, files }} = await index.getFiles();
            for (const file of files) {{
                const filePath = path.join({str(self.index_path)!r}, file.path);
                const fileData = Buffer.from(file.content);
                fs.writeFileSync(filePath, fileData);
            }}
        ''')
        self.node_process.stdin.close()
        await self.node_process.wait()
        assert self.node_process.returncode == 0, 'Pagefind failure'

    def results(self) -> set[AbsolutePath]:
        return set(self.index_path.walk_all())

    def head_tags(self) -> Sequence[HeadTag]:
        yield HeadJsFile(self.index_path_relative / 'pagefind-ui.js')
        yield HeadJsCode(dedent(f'''
            window.addEventListener("DOMContentLoaded", (event) => {{
                new PagefindUI({{
                    element: ".book-search",
                    baseUrl: new URL("%ROOT%", location),
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
