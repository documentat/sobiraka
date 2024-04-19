from asyncio.subprocess import Process, create_subprocess_exec
from pathlib import Path
from subprocess import PIPE
from textwrap import dedent
from typing import Sequence

from panflute import Element, stringify

from sobiraka.models import Page
from sobiraka.models.config import Config_Search_LinkTarget
from sobiraka.processing.txt import PlainTextDispatcher
from sobiraka.runtime import RT

from .searchindexer import SearchIndexer
from ..head import HeadJsCode, HeadJsFile, HeadTag


class PagefindIndexer(SearchIndexer, PlainTextDispatcher):
    """
    - Pagefind website: https://pagefind.app/
    - Pagefind JS API: https://pagefind.app/docs/node-api/
    """

    # pylint: disable=abstract-method

    node_process: Process = None

    def execute_js(self, code: str):
        self.node_process.stdin.write(code.encode('utf-8'))

    async def initialize(self):
        self.node_process = await create_subprocess_exec('node', '--input-type', 'module', stdin=PIPE, stdout=PIPE)
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
                    title: {title!r},
                }},
            }});
        ''')

    async def add_page(self, page: Page):
        await super().process_doc(RT[page].doc, page)

        tm = self.tm[page]
        url = str(self.builder.get_target_path(page).relative_to(self.builder.output))
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

    def results(self) -> set[Path]:
        return set(self.index_path.rglob('**/*'))

    def head_tags(self) -> Sequence[HeadTag]:
        yield HeadJsFile(self.index_path.relative_to(self.builder.output) / 'pagefind-ui.js')
        yield HeadJsCode(dedent(f'''
            window.addEventListener("DOMContentLoaded", (event) => {{
                new PagefindUI({{
                    element: ".book-search",
                    baseUrl: new URL("%ROOT%", location),
                    translations: {self.search_config.translations.to_json()},
                }})
            }})
        ''').strip())

    async def process_element(self, elem: Element, page: Page):
        if not isinstance(elem, self.search_config.skip_elements):
            return await super().process_element(elem, page)
