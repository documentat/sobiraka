from asyncio.subprocess import Process, create_subprocess_exec
from pathlib import Path
from subprocess import PIPE

from panflute import Doc
from sobiraka.models import Page
from sobiraka.processing.txt import PlainTextDispatcher
from sobiraka.runtime import RT

from .searchindexer import SearchIndexer


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

    async def process_doc(self, doc: Doc, page: Page):
        await super().process_doc(doc, page)
        self.execute_js(f'''
            var {{ errors, file }} = await index.addCustomRecord({{
                url: {str(self.builder.get_target_path(page).relative_to(self.builder.output))!r},
                content: {self.tm[page].text!r},
                language: {self.volume.lang or 'en'!r},
                meta: {{
                    title: {RT[page].title!r},
                }},
            }});
        ''')

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
